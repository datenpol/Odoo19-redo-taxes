from __future__ import annotations

import os
from typing import Sequence

from ._cli_contract import CommandReport, ExitCode, StageReport, skipped_stage
from .json2_client import Json2Client, Json2ClientError
from .models import ProjectSpec
from .planner import (
    EnsureCreateOperation,
    PlanOperation,
    WriteOperation,
    build_cosmetic_plan,
    ensure_operation_safe,
    resolve_bank_trust_lock,
    resolve_company_partner_id,
)
from .validator import validate_cosmetic_state

MODE = "cosmetic"


def execute_command(command: str, client: Json2Client, spec: ProjectSpec) -> CommandReport:
    if command == "apply":
        return _execute_apply(client, spec)
    if command == "validate":
        return _execute_validate(client, spec)
    return _execute_run(client, spec)


def unexpected_report(*, command: str, base_url: str, summary: str) -> CommandReport:
    return CommandReport(
        command=command,
        mode=MODE,
        base_url=base_url,
        status="failure",
        summary=summary,
        exit_code=ExitCode.INTERNAL_ERROR,
        preflight=skipped_stage("Not run."),
        apply=skipped_stage("Not run."),
        validation=skipped_stage("Not run."),
    )


def resolved_base_url(base_url: str | None) -> str:
    return base_url or os.environ.get("ODOO_BASE_URL", "https://dmdemousa.odoo19.at")


def _build_operations(
    client: Json2Client,
    spec: ProjectSpec,
) -> list[PlanOperation]:
    partner_id = resolve_company_partner_id(client, spec.source_environment.company_id)
    bank_fields_locked = resolve_bank_trust_lock(client, spec.identity.bank.partner_bank_id)
    return build_cosmetic_plan(
        spec,
        company_partner_id=partner_id,
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
    return len(operations)


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


def _execute_apply(client: Json2Client, spec: ProjectSpec) -> CommandReport:
    preflight = skipped_stage()
    apply = skipped_stage()
    validation = skipped_stage("Not run by the apply command.")

    try:
        operations = _build_operations(client, spec)
        preflight = StageReport(
            status="success",
            summary=f"Planned {len(operations)} cosmetic operations.",
            operation_count=len(operations),
        )
    except Exception as exc:
        return _phase_failure_report(
            command="apply",
            base_url=client.base_url,
            summary="Apply aborted during preflight.",
            phase="preflight",
            exc=exc,
            default_exit_code=ExitCode.PREFLIGHT_FAILURE,
            preflight=preflight,
            apply=apply,
            validation=validation,
        )

    try:
        applied_count = _apply_operations(client, operations)
        apply = StageReport(
            status="success",
            summary=f"Applied {applied_count} cosmetic operations.",
            operation_count=applied_count,
        )
    except Exception as exc:
        return _phase_failure_report(
            command="apply",
            base_url=client.base_url,
            summary="Apply failed while writing cosmetic changes.",
            phase="apply",
            exc=exc,
            default_exit_code=ExitCode.APPLY_FAILURE,
            preflight=preflight,
            apply=apply,
            validation=validation,
        )

    return CommandReport(
        command="apply",
        mode=MODE,
        base_url=client.base_url,
        status="success",
        summary="Apply completed successfully.",
        exit_code=ExitCode.SUCCESS,
        preflight=preflight,
        apply=apply,
        validation=validation,
    )


def _execute_validate(client: Json2Client, spec: ProjectSpec) -> CommandReport:
    preflight = skipped_stage("Not run by the validate command.")
    apply = skipped_stage("Not run by the validate command.")
    try:
        issues = validate_cosmetic_state(client, spec)
    except Exception as exc:
        return _phase_failure_report(
            command="validate",
            base_url=client.base_url,
            summary="Validate failed before finishing the API checks.",
            phase="validation",
            exc=exc,
            default_exit_code=ExitCode.VALIDATION_FAILURE,
            preflight=preflight,
            apply=apply,
            validation=skipped_stage(),
        )

    validation = _validation_stage(issues)
    if issues:
        return CommandReport(
            command="validate",
            mode=MODE,
            base_url=client.base_url,
            status="failure",
            summary=f"Validation failed with {len(issues)} issue(s).",
            exit_code=ExitCode.VALIDATION_FAILURE,
            preflight=preflight,
            apply=apply,
            validation=validation,
        )

    return CommandReport(
        command="validate",
        mode=MODE,
        base_url=client.base_url,
        status="success",
        summary="Validation passed.",
        exit_code=ExitCode.SUCCESS,
        preflight=preflight,
        apply=apply,
        validation=validation,
    )


def _execute_run(client: Json2Client, spec: ProjectSpec) -> CommandReport:
    preflight = skipped_stage()
    apply = skipped_stage()
    validation = skipped_stage()

    try:
        operations = _build_operations(client, spec)
        preflight = StageReport(
            status="success",
            summary=f"Planned {len(operations)} cosmetic operations.",
            operation_count=len(operations),
        )
    except Exception as exc:
        return _phase_failure_report(
            command="run",
            base_url=client.base_url,
            summary="Run aborted during preflight.",
            phase="preflight",
            exc=exc,
            default_exit_code=ExitCode.PREFLIGHT_FAILURE,
            preflight=preflight,
            apply=apply,
            validation=validation,
        )

    try:
        applied_count = _apply_operations(client, operations)
        apply = StageReport(
            status="success",
            summary=f"Applied {applied_count} cosmetic operations.",
            operation_count=applied_count,
        )
    except Exception as exc:
        validation = skipped_stage("Not run because apply failed.")
        return _phase_failure_report(
            command="run",
            base_url=client.base_url,
            summary="Run failed while applying cosmetic changes.",
            phase="apply",
            exc=exc,
            default_exit_code=ExitCode.APPLY_FAILURE,
            preflight=preflight,
            apply=apply,
            validation=validation,
        )

    try:
        issues = validate_cosmetic_state(client, spec)
    except Exception as exc:
        return _phase_failure_report(
            command="run",
            base_url=client.base_url,
            summary="Run failed during validation.",
            phase="validation",
            exc=exc,
            default_exit_code=ExitCode.VALIDATION_FAILURE,
            preflight=preflight,
            apply=apply,
            validation=validation,
        )

    validation = _validation_stage(issues)
    if issues:
        return CommandReport(
            command="run",
            mode=MODE,
            base_url=client.base_url,
            status="failure",
            summary=f"Run applied changes but validation found {len(issues)} issue(s).",
            exit_code=ExitCode.VALIDATION_FAILURE,
            preflight=preflight,
            apply=apply,
            validation=validation,
        )

    return CommandReport(
        command="run",
        mode=MODE,
        base_url=client.base_url,
        status="success",
        summary="Run completed successfully.",
        exit_code=ExitCode.SUCCESS,
        preflight=preflight,
        apply=apply,
        validation=validation,
    )


def _validation_stage(issues: Sequence[object]) -> StageReport:
    if issues:
        messages = tuple(_format_issue(issue) for issue in issues)
        return StageReport(
            status="failure",
            summary=f"Validation failed with {len(issues)} issue(s).",
            messages=messages,
            issue_count=len(issues),
        )
    return StageReport(
        status="success",
        summary="Validation passed.",
        issue_count=0,
    )


def _phase_failure_report(
    *,
    command: str,
    base_url: str,
    summary: str,
    phase: str,
    exc: Exception,
    default_exit_code: ExitCode,
    preflight: StageReport,
    apply: StageReport,
    validation: StageReport,
) -> CommandReport:
    stage = StageReport(
        status="failure",
        summary=f"{phase.title()} failed.",
        messages=(str(exc),),
    )
    if phase == "preflight":
        preflight = stage
    elif phase == "apply":
        apply = stage
    else:
        validation = stage

    return CommandReport(
        command=command,
        mode=MODE,
        base_url=base_url,
        status="failure",
        summary=summary,
        exit_code=_classify_failure(exc, default_exit_code),
        preflight=preflight,
        apply=apply,
        validation=validation,
    )


def _classify_failure(exc: Exception, default_exit_code: ExitCode) -> int:
    if isinstance(exc, Json2ClientError) and _looks_like_api_failure(str(exc)):
        return ExitCode.API_FAILURE
    if isinstance(exc, (Json2ClientError, ValueError)):
        return int(default_exit_code)
    return ExitCode.INTERNAL_ERROR


def _looks_like_api_failure(message: str) -> bool:
    return message.startswith(("HTTP ", "Transport error", "Invalid JSON response"))


def _format_issue(issue: object) -> str:
    scope = getattr(issue, "scope", "validation")
    message = getattr(issue, "message", str(issue))
    return f"{scope}: {message}"
