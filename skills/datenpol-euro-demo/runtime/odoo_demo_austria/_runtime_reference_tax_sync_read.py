from __future__ import annotations

from typing import Any

from ._planner_types import SyncFiscalPositionTaxesFromReferenceOperation
from ._runtime_reference_tax_sync_types import (
    ReferenceAccount,
    ReferenceTax,
    ReferenceTaxGroup,
)
from .json2_client import Json2Client, Json2ClientError


def resolve_fiscal_positions(
    client: Json2Client,
    *,
    company_id: int,
    fiscal_position_names: tuple[str, ...],
) -> dict[str, int]:
    records = client.search_read(
        "account.fiscal.position",
        domain=[
            ["company_id", "=", company_id],
            ["name", "in", list(fiscal_position_names)],
        ],
        fields=["id", "name"],
        order="id",
    )
    by_name = {str(record.get("name")): int(record["id"]) for record in records}
    missing = [name for name in fiscal_position_names if name not in by_name]
    if missing:
        missing_names = ", ".join(repr(name) for name in missing)
        raise Json2ClientError(f"Missing fiscal positions for sync: {missing_names}")
    return by_name


def load_reference_taxes(
    client: Json2Client,
    operation: SyncFiscalPositionTaxesFromReferenceOperation,
    *,
    reference_positions_by_name: dict[str, int],
) -> tuple[ReferenceTax, ...]:
    position_names_by_id = {
        record_id: name for name, record_id in reference_positions_by_name.items()
    }
    rows = client.search_read(
        "account.tax",
        domain=[
            ["company_id", "=", operation.reference_company_id],
            ["fiscal_position_ids", "in", list(reference_positions_by_name.values())],
        ],
        fields=[
            "id",
            "name",
            "type_tax_use",
            "tax_group_id",
            "fiscal_position_ids",
            "original_tax_ids",
        ],
        order="id",
    )
    tax_ids = [int(row["id"]) for row in rows]
    base_copy = copy_data(client, "account.tax", tax_ids)
    translated_copy = copy_data(
        client,
        "account.tax",
        tax_ids,
        context={"lang": operation.display_language},
    )
    return tuple(
        ReferenceTax(
            record_id=int(row["id"]),
            name=str(row.get("name")),
            type_tax_use=str(row.get("type_tax_use")),
            tax_group_id=many2one_id(row.get("tax_group_id"), "account.tax.tax_group_id"),
            fiscal_position_names=tuple(
                position_names_by_id[position_id]
                for position_id in row.get("fiscal_position_ids", [])
                if position_id in position_names_by_id
            ),
            original_tax_ids=tuple(int(item) for item in row.get("original_tax_ids", [])),
            base_copy_vals=base_vals,
            translated_copy_vals=translated_vals,
        )
        for row, base_vals, translated_vals in zip(rows, base_copy, translated_copy, strict=True)
    )


def load_reference_tax_groups(
    client: Json2Client,
    reference_taxes: tuple[ReferenceTax, ...],
) -> tuple[ReferenceTaxGroup, ...]:
    group_ids = sorted({item.tax_group_id for item in reference_taxes})
    group_names = {
        int(row["id"]): str(row.get("name"))
        for row in client.read("account.tax.group", group_ids, ["id", "name"])
    }
    group_copy_vals = copy_data(client, "account.tax.group", group_ids)
    return tuple(
        ReferenceTaxGroup(
            record_id=group_id,
            name=group_names[group_id],
            copy_vals=values,
        )
        for group_id, values in zip(group_ids, group_copy_vals, strict=True)
    )


def load_reference_accounts(
    client: Json2Client,
    *,
    reference_company_id: int,
    reference_groups: tuple[ReferenceTaxGroup, ...],
    reference_taxes: tuple[ReferenceTax, ...],
) -> dict[int, ReferenceAccount]:
    account_ids = required_reference_account_ids(reference_groups, reference_taxes)
    if not account_ids:
        return {}
    rows = client.read(
        "account.account",
        account_ids,
        ["id", "name", "account_type", "code"],
        context=company_access_context(reference_company_id),
    )
    return {
        int(row["id"]): ReferenceAccount(
            record_id=int(row["id"]),
            name=str(row.get("name")),
            account_type=str(row.get("account_type")),
            code=optional_text(row.get("code")),
        )
        for row in rows
    }


def required_reference_account_ids(
    reference_groups: tuple[ReferenceTaxGroup, ...],
    reference_taxes: tuple[ReferenceTax, ...],
) -> list[int]:
    account_ids: set[int] = set()
    for group in reference_groups:
        account_ids.update(int_values(group.copy_vals, "tax_payable_account_id"))
        account_ids.update(int_values(group.copy_vals, "tax_receivable_account_id"))
        account_ids.update(int_values(group.copy_vals, "advance_tax_payment_account_id"))
    for tax in reference_taxes:
        account_ids.update(int_values(tax.base_copy_vals, "cash_basis_transition_account_id"))
        for command in tax.base_copy_vals.get("repartition_line_ids", []):
            if len(command) == 3 and isinstance(command[2], dict):
                account_ids.update(int_values(command[2], "account_id"))
    return sorted(account_ids)


def copy_data(
    client: Json2Client,
    model: str,
    ids: list[int],
    *,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not ids:
        return []
    payload: dict[str, Any] = {"ids": ids}
    if context:
        payload["context"] = context
    result = client.call(model, "copy_data", payload)
    if not isinstance(result, list):
        raise Json2ClientError(f"{model}.copy_data returned a non-list response")
    return [dict(item) for item in result]


def company_access_context(company_id: int) -> dict[str, Any]:
    return {
        "company": company_id,
        "allowed_company_ids": [company_id],
    }


def many2one_id(value: Any, field_name: str) -> int:
    if isinstance(value, list) and value:
        return int(value[0])
    raise Json2ClientError(f"Expected populated many2one for {field_name}")


def optional_int(value: Any) -> int | None:
    if isinstance(value, bool) or value in (None, False):
        return None
    if isinstance(value, int):
        return value
    return None


def optional_text(value: Any) -> str | None:
    if not value:
        return None
    return str(value)


def int_values(mapping: dict[str, Any], key: str) -> set[int]:
    value = mapping.get(key)
    if isinstance(value, bool):
        return set()
    if isinstance(value, int):
        return {value}
    return set()
