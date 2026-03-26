from __future__ import annotations

from typing import Any

from ._planner_types import SyncFiscalPositionTaxesFromReferenceOperation
from ._runtime_reference_tax_sync_accounts import mapped_account_id
from ._runtime_reference_tax_sync_read import optional_int
from ._runtime_reference_tax_sync_types import ReferenceAccount, ReferenceTax
from .json2_client import Json2Client, Json2ClientError


def ensure_target_taxes(
    client: Json2Client,
    operation: SyncFiscalPositionTaxesFromReferenceOperation,
    *,
    target_positions: dict[str, int],
    reference_taxes: tuple[ReferenceTax, ...],
    group_id_map: dict[int, int],
    reference_accounts: dict[int, ReferenceAccount],
    candidate_codes: dict[int, tuple[str, ...]],
    created_accounts: dict[int, int],
) -> dict[int, int]:
    target_tax_ids: dict[int, int] = {}
    for reference_tax in reference_taxes:
        vals = target_tax_vals(
            client,
            target_company_id=operation.target_company_id,
            target_positions=target_positions,
            reference_tax=reference_tax,
            group_id_map=group_id_map,
            reference_accounts=reference_accounts,
            candidate_codes=candidate_codes,
            created_accounts=created_accounts,
        )
        existing_id = find_target_tax_id(
            client,
            target_company_id=operation.target_company_id,
            tax_name=reference_tax.name,
            type_tax_use=reference_tax.type_tax_use,
        )
        if existing_id is None:
            existing_id = int(client.create("account.tax", vals))
        else:
            safe_vals = existing_tax_write_vals(vals)
            if safe_vals:
                client.write("account.tax", [existing_id], safe_vals)
        target_tax_ids[reference_tax.record_id] = existing_id
        translated_vals = translated_tax_vals(reference_tax)
        if translated_vals:
            client.write(
                "account.tax",
                [existing_id],
                translated_vals,
                context={"lang": operation.display_language},
            )
    return target_tax_ids


def target_tax_vals(
    client: Json2Client,
    *,
    target_company_id: int,
    target_positions: dict[str, int],
    reference_tax: ReferenceTax,
    group_id_map: dict[int, int],
    reference_accounts: dict[int, ReferenceAccount],
    candidate_codes: dict[int, tuple[str, ...]],
    created_accounts: dict[int, int],
) -> dict[str, Any]:
    vals = dict(reference_tax.base_copy_vals)
    vals["name"] = reference_tax.name
    vals["company_id"] = target_company_id
    vals.pop("country_id", None)
    vals["tax_group_id"] = group_id_map[reference_tax.tax_group_id]
    vals["children_tax_ids"] = [[6, 0, []]]
    vals["replacing_tax_ids"] = [[6, 0, []]]
    vals["original_tax_ids"] = [[6, 0, []]]
    vals["fiscal_position_ids"] = [[6, 0, mapped_position_ids(reference_tax, target_positions)]]
    vals["cash_basis_transition_account_id"] = mapped_account_id(
        client,
        target_company_id=target_company_id,
        reference_account_id=optional_int(
            reference_tax.base_copy_vals.get("cash_basis_transition_account_id")
        ),
        reference_accounts=reference_accounts,
        candidate_codes=candidate_codes,
        created_accounts=created_accounts,
        preferred_role=None,
    )
    vals["repartition_line_ids"] = sanitized_repartition_line_commands(
        client,
        target_company_id=target_company_id,
        commands=reference_tax.base_copy_vals.get("repartition_line_ids", []),
        reference_accounts=reference_accounts,
        candidate_codes=candidate_codes,
        created_accounts=created_accounts,
    )
    return vals


def existing_tax_write_vals(vals: dict[str, Any]) -> dict[str, Any]:
    field_names = ("amount", "tax_scope")
    return {
        field_name: vals[field_name]
        for field_name in field_names
        if field_name in vals
    }


def sanitized_repartition_line_commands(
    client: Json2Client,
    *,
    target_company_id: int,
    commands: list[Any],
    reference_accounts: dict[int, ReferenceAccount],
    candidate_codes: dict[int, tuple[str, ...]],
    created_accounts: dict[int, int],
) -> list[list[Any]]:
    sanitized: list[list[Any]] = []
    for command in commands:
        if len(command) != 3 or not isinstance(command[2], dict):
            continue
        vals = dict(command[2])
        vals.pop("tax_id", None)
        vals["account_id"] = mapped_account_id(
            client,
            target_company_id=target_company_id,
            reference_account_id=optional_int(vals.get("account_id")),
            reference_accounts=reference_accounts,
            candidate_codes=candidate_codes,
            created_accounts=created_accounts,
            preferred_role=None,
        )
        sanitized.append([0, 0, vals])
    return sanitized


def apply_target_tax_relationships(
    client: Json2Client,
    *,
    reference_taxes: tuple[ReferenceTax, ...],
    target_positions: dict[str, int],
    target_tax_ids: dict[int, int],
) -> None:
    for reference_tax in reference_taxes:
        client.write(
            "account.tax",
            [target_tax_ids[reference_tax.record_id]],
            {
                "fiscal_position_ids": [
                    [6, 0, mapped_position_ids(reference_tax, target_positions)]
                ],
                "original_tax_ids": [
                    [6, 0, mapped_original_tax_ids(reference_tax, target_tax_ids)]
                ],
            },
        )


def mapped_position_ids(reference_tax: ReferenceTax, target_positions: dict[str, int]) -> list[int]:
    return [target_positions[name] for name in reference_tax.fiscal_position_names]


def mapped_original_tax_ids(
    reference_tax: ReferenceTax,
    target_tax_ids: dict[int, int],
) -> list[int]:
    return [target_tax_ids[record_id] for record_id in reference_tax.original_tax_ids]


def find_target_tax_id(
    client: Json2Client,
    *,
    target_company_id: int,
    tax_name: str,
    type_tax_use: str,
) -> int | None:
    rows = client.search_read(
        "account.tax",
        domain=[
            ["company_id", "=", target_company_id],
            ["type_tax_use", "=", type_tax_use],
            ["name", "=", tax_name],
        ],
        fields=["id"],
        order="id",
    )
    if not rows:
        return None
    if len(rows) != 1:
        raise Json2ClientError(f"Expected one tax named {tax_name!r}, got {len(rows)}")
    return int(rows[0]["id"])


def translated_tax_vals(reference_tax: ReferenceTax) -> dict[str, Any]:
    vals: dict[str, Any] = {"name": reference_tax.name}
    for field_name in ("description", "invoice_label", "invoice_legal_notes"):
        value = reference_tax.translated_copy_vals.get(field_name)
        if value not in (None, False):
            vals[field_name] = value
    return vals
