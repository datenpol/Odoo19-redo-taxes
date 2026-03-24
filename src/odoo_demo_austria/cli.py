from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .json2_client import Json2Client, Json2ClientError
from .models import ProjectSpec
from .planner import (
    EnsureCreateOperation,
    PlanOperation,
    WriteOperation,
    build_cosmetic_plan,
    build_report_aware_plan,
    ensure_operation_safe,
    resolve_bank_trust_lock,
    resolve_company_partner_id,
    resolve_repartition_lines,
)
from .spec_loader import load_spec
from .validator import validate_cosmetic_state, validate_report_aware_state


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    spec = load_spec(args.spec)
    client = _build_client(parser, args)

    if args.command == "validate":
        return _run_validation(args.mode, client, spec)

    operations = _build_operations(args.mode, client, spec)

    if args.command == "plan" or args.dry_run:
        _print_plan(operations)
        return 0

    return _apply_operations(client, operations)


def _build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--spec",
        default=str(Path("data") / "austria-cosmetic-mapping-spec.draft.yaml"),
        help="Path to the translation-aware mapping spec.",
    )
    common.add_argument(
        "--base-url",
        default=os.environ.get("ODOO_BASE_URL"),
        help="Instance root URL, for example https://codexplayground.odoo19.at",
    )
    common.add_argument(
        "--database",
        default=os.environ.get("ODOO_DB"),
        help="Optional X-Odoo-Database header value.",
    )
    common.add_argument(
        "--api-key",
        default=None,
        help="API key. Prefer the environment variable instead of passing it directly.",
    )
    common.add_argument(
        "--api-key-env",
        default="ODOO_API_KEY",
        help="Environment variable name that contains the API key.",
    )
    common.add_argument(
        "--timeout-s",
        type=int,
        default=30,
        help="HTTP timeout in seconds.",
    )

    parser = argparse.ArgumentParser(description="Odoo 19 demo Austria patcher", parents=[common])

    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("plan", "apply", "validate"):
        sub = subparsers.add_parser(command, parents=[common])
        sub.add_argument(
            "--mode",
            default="cosmetic",
            choices=("cosmetic", "report-aware"),
            help="Patch mode.",
        )
        if command == "apply":
            sub.add_argument(
                "--dry-run",
                action="store_true",
                help="Build the plan and print it without writing anything.",
            )

    return parser


def _resolve_api_key(explicit_api_key: str | None, api_key_env: str) -> str | None:
    return explicit_api_key or os.environ.get(api_key_env)


def _build_client(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Json2Client:
    try:
        return Json2Client.from_env(
            base_url=args.base_url,
            api_key=_resolve_api_key(args.api_key, args.api_key_env),
            database=args.database,
            timeout_s=args.timeout_s,
        )
    except Json2ClientError as exc:
        parser.error(str(exc))


def _run_validation(mode: str, client: Json2Client, spec: ProjectSpec) -> int:
    if mode == "cosmetic":
        issues = validate_cosmetic_state(client, spec)
    else:
        issues = validate_report_aware_state(client, spec)
    if issues:
        for issue in issues:
            print(f"[FAIL] {issue.scope}: {issue.message}")
        return 1
    print("Validation passed.")
    return 0


def _build_operations(
    mode: str,
    client: Json2Client,
    spec: ProjectSpec,
) -> list[PlanOperation]:
    partner_id = resolve_company_partner_id(client, spec.source_environment.company_id)
    bank_fields_locked = resolve_bank_trust_lock(client, spec.identity.bank.partner_bank_id)
    if mode == "cosmetic":
        return build_cosmetic_plan(
            spec,
            company_partner_id=partner_id,
            bank_fields_locked=bank_fields_locked,
        )

    repartition_lines = resolve_repartition_lines(
        client,
        [item.record_id for item in spec.taxes],
    )
    return build_report_aware_plan(
        spec,
        company_partner_id=partner_id,
        repartition_lines_by_tax=repartition_lines,
        bank_fields_locked=bank_fields_locked,
    )


def _apply_operations(client: Json2Client, operations: list[PlanOperation]) -> int:
    for operation in operations:
        ensure_operation_safe(operation)
        if isinstance(operation, WriteOperation):
            client.write(
                operation.model,
                list(operation.ids),
                operation.vals,
                context=operation.context,
            )
            continue

        resolved_id = _apply_ensure_create(client, operation)
        if operation.update_vals:
            client.write(
                operation.model,
                [resolved_id],
                operation.update_vals,
                context=operation.update_context,
            )
    print(f"Applied {len(operations)} operations.")
    return 0


def _apply_ensure_create(client: Json2Client, operation: EnsureCreateOperation) -> int:
    matches = client.search_read(
        operation.model,
        domain=operation.lookup_domain,
        fields=["id"],
        order="id",
    )
    if len(matches) > 1:
        raise Json2ClientError(
            f"Lookup for {operation.model} returned multiple records: {operation.lookup_domain!r}"
        )
    if matches:
        record_id = int(matches[0]["id"])
        update_vals = {
            key: value
            for key, value in operation.create_vals.items()
            if key
            in {
                "name",
                "sequence",
                "auto_apply",
                "country_id",
                "country_group_id",
                "vat_required",
                "foreign_vat",
                "tax_ids",
                "note",
            }
        }
        if update_vals:
            client.write(operation.model, [record_id], update_vals)
        return record_id

    created_id = client.create(operation.model, operation.create_vals)
    return int(created_id)


def _print_plan(operations: list[PlanOperation]) -> None:
    print(
        json.dumps(
            {
                "operation_count": len(operations),
                "operations": [operation.to_dict() for operation in operations],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
