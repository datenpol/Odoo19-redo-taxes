from __future__ import annotations

from ._planner_types import (
    ALLOWED_WRITE_FIELDS,
    EnsureCreateOperation,
    PlanOperation,
    ReplaceFiscalPositionAccountsOperation,
    SyncFiscalPositionTaxesFromReferenceOperation,
    WriteOperation,
    ensure_operation_safe,
)
from ._runtime_reference_tax_sync import sync_fiscal_position_taxes_from_reference
from .json2_client import Json2Client, Json2ClientError


def apply_operations(client: Json2Client, operations: list[PlanOperation]) -> int:
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
        if isinstance(operation, EnsureCreateOperation):
            resolved_id = apply_ensure_create(client, operation)
            if operation.update_vals:
                client.write(
                    operation.model,
                    [resolved_id],
                    operation.update_vals,
                    context=operation.update_context,
                )
            continue
        if isinstance(operation, SyncFiscalPositionTaxesFromReferenceOperation):
            sync_fiscal_position_taxes_from_reference(client, operation)
            continue
        apply_replace_fiscal_position_accounts(client, operation)
    return len(operations)


def apply_ensure_create(client: Json2Client, operation: EnsureCreateOperation) -> int:
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
        allowed_fields = ALLOWED_WRITE_FIELDS.get(operation.model, set())
        update_vals = {
            key: value for key, value in operation.create_vals.items() if key in allowed_fields
        }
        if update_vals:
            client.write(operation.model, [record_id], update_vals)
        return record_id
    created_id = client.create(operation.model, operation.create_vals)
    return int(created_id)


def apply_replace_fiscal_position_accounts(
    client: Json2Client,
    operation: ReplaceFiscalPositionAccountsOperation,
) -> None:
    fiscal_position_id = _resolve_fiscal_position_id(client, operation)
    commands: list[list[object]] = [[5, 0, 0]]
    for mapping in operation.mappings:
        commands.append(
            [
                0,
                0,
                {
                    "account_src_id": _resolve_account_id_by_code(
                        client,
                        company_id=operation.company_id,
                        code=mapping.source_account_code,
                    ),
                    "account_dest_id": _resolve_account_id_by_code(
                        client,
                        company_id=operation.company_id,
                        code=mapping.replacement_account_code,
                    ),
                },
            ]
        )
    client.write("account.fiscal.position", [fiscal_position_id], {"account_ids": commands})


def _resolve_fiscal_position_id(
    client: Json2Client,
    operation: ReplaceFiscalPositionAccountsOperation,
) -> int:
    if operation.fiscal_position_id is not None:
        return operation.fiscal_position_id
    matches = client.search_read(
        "account.fiscal.position",
        domain=[
            ["company_id", "=", operation.company_id],
            ["name", "=", operation.fiscal_position_name],
        ],
        fields=["id"],
        order="id",
    )
    return _single_id(
        matches,
        label=(
            "account.fiscal.position"
            f" {operation.fiscal_position_name!r} for company {operation.company_id}"
        ),
    )


def _resolve_account_id_by_code(
    client: Json2Client,
    *,
    company_id: int,
    code: str,
) -> int:
    matches = client.search_read(
        "account.account",
        domain=[
            ["company_ids", "in", [company_id]],
            ["code", "=", code],
        ],
        fields=["id"],
        order="id",
    )
    return _single_id(matches, label=f"account.account code {code!r} for company {company_id}")


def _single_id(records: list[dict[str, object]], *, label: str) -> int:
    if len(records) != 1:
        raise Json2ClientError(f"Expected exactly one record for {label}, got {len(records)}")
    value = records[0].get("id")
    if isinstance(value, bool) or not isinstance(value, int):
        raise Json2ClientError(f"Expected integer id for {label}, got {value!r}")
    return value
