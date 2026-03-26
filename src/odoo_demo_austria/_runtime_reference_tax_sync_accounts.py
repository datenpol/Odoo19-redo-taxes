from __future__ import annotations

from typing import Any

from ._planner_types import ReferenceAccountTarget, SyncFiscalPositionTaxesFromReferenceOperation
from ._runtime_reference_tax_sync_read import company_access_context, optional_int
from ._runtime_reference_tax_sync_types import ReferenceAccount, ReferenceTaxGroup
from .json2_client import Json2Client, Json2ClientError


def candidate_codes_by_reference_id(
    account_targets: tuple[ReferenceAccountTarget, ...],
) -> dict[int, tuple[str, ...]]:
    by_reference_id: dict[int, list[str]] = {}
    for item in account_targets:
        by_reference_id.setdefault(item.reference_account_id, [])
        if item.target_code not in by_reference_id[item.reference_account_id]:
            by_reference_id[item.reference_account_id].append(item.target_code)
    return {key: tuple(values) for key, values in by_reference_id.items()}


def ensure_dynamic_target_accounts(
    client: Json2Client,
    *,
    target_company_id: int,
    reference_accounts: dict[int, ReferenceAccount],
    candidate_codes: dict[int, tuple[str, ...]],
) -> dict[int, int]:
    created: dict[int, int] = {}
    for record_id, reference_account in reference_accounts.items():
        if record_id in candidate_codes:
            continue
        existing_id = find_target_account_by_name(
            client,
            target_company_id=target_company_id,
            reference_account=reference_account,
        )
        if existing_id is not None:
            created[record_id] = existing_id
            continue
        vals = {
            "name": reference_account.name,
            "account_type": reference_account.account_type,
            "reconcile": False,
            "company_ids": [[6, 0, [target_company_id]]],
        }
        if reference_account.code:
            vals["code"] = reference_account.code
        created[record_id] = int(
            client.create(
                "account.account",
                vals,
                context=company_access_context(target_company_id),
            )
        )
    return created


def ensure_target_tax_groups(
    client: Json2Client,
    operation: SyncFiscalPositionTaxesFromReferenceOperation,
    *,
    reference_groups: tuple[ReferenceTaxGroup, ...],
    reference_accounts: dict[int, ReferenceAccount],
    candidate_codes: dict[int, tuple[str, ...]],
    created_accounts: dict[int, int],
) -> dict[int, int]:
    group_ids: dict[int, int] = {}
    for reference_group in reference_groups:
        vals = target_tax_group_vals(
            client,
            target_company_id=operation.target_company_id,
            reference_group=reference_group,
            reference_accounts=reference_accounts,
            candidate_codes=candidate_codes,
            created_accounts=created_accounts,
        )
        existing_id = find_target_tax_group_id(
            client,
            target_company_id=operation.target_company_id,
            group_name=reference_group.name,
        )
        if existing_id is None:
            group_ids[reference_group.record_id] = int(client.create("account.tax.group", vals))
            continue
        group_ids[reference_group.record_id] = existing_id
    return group_ids


def target_tax_group_vals(
    client: Json2Client,
    *,
    target_company_id: int,
    reference_group: ReferenceTaxGroup,
    reference_accounts: dict[int, ReferenceAccount],
    candidate_codes: dict[int, tuple[str, ...]],
    created_accounts: dict[int, int],
) -> dict[str, Any]:
    vals = dict(reference_group.copy_vals)
    vals["company_id"] = target_company_id
    vals.pop("country_id", None)
    vals["tax_payable_account_id"] = mapped_account_id(
        client,
        target_company_id=target_company_id,
        reference_account_id=optional_int(reference_group.copy_vals.get("tax_payable_account_id")),
        reference_accounts=reference_accounts,
        candidate_codes=candidate_codes,
        created_accounts=created_accounts,
        preferred_role="payable",
    )
    vals["tax_receivable_account_id"] = mapped_account_id(
        client,
        target_company_id=target_company_id,
        reference_account_id=optional_int(
            reference_group.copy_vals.get("tax_receivable_account_id")
        ),
        reference_accounts=reference_accounts,
        candidate_codes=candidate_codes,
        created_accounts=created_accounts,
        preferred_role="receivable",
    )
    vals["advance_tax_payment_account_id"] = mapped_account_id(
        client,
        target_company_id=target_company_id,
        reference_account_id=optional_int(
            reference_group.copy_vals.get("advance_tax_payment_account_id")
        ),
        reference_accounts=reference_accounts,
        candidate_codes=candidate_codes,
        created_accounts=created_accounts,
        preferred_role="asset",
    )
    return vals


def find_target_tax_group_id(
    client: Json2Client,
    *,
    target_company_id: int,
    group_name: str,
) -> int | None:
    rows = client.search_read(
        "account.tax.group",
        domain=[["company_id", "=", target_company_id], ["name", "=", group_name]],
        fields=["id"],
        order="id",
    )
    if not rows:
        return None
    if len(rows) != 1:
        raise Json2ClientError(f"Expected one tax group named {group_name!r}, got {len(rows)}")
    return int(rows[0]["id"])


def mapped_account_id(
    client: Json2Client,
    *,
    target_company_id: int,
    reference_account_id: int | None,
    reference_accounts: dict[int, ReferenceAccount],
    candidate_codes: dict[int, tuple[str, ...]],
    created_accounts: dict[int, int],
    preferred_role: str | None,
) -> int | bool:
    if reference_account_id is None:
        return False
    created_id = created_accounts.get(reference_account_id)
    if created_id is not None:
        return created_id
    codes = candidate_codes.get(reference_account_id)
    if codes is None:
        reference_account = reference_accounts.get(reference_account_id)
        raise Json2ClientError(f"Missing target account mapping for {reference_account!r}")
    return candidate_target_account_id(
        client,
        target_company_id=target_company_id,
        candidate_codes=codes,
        preferred_role=preferred_role,
    )


def candidate_target_account_id(
    client: Json2Client,
    *,
    target_company_id: int,
    candidate_codes: tuple[str, ...],
    preferred_role: str | None,
) -> int:
    rows: list[dict[str, Any]] = []
    for code in candidate_codes:
        rows.extend(
            client.search_read(
                "account.account",
                domain=[["company_ids", "in", [target_company_id]], ["code", "=", code]],
                fields=["id", "account_type"],
                order="id",
                context=company_access_context(target_company_id),
            )
        )
    if not rows:
        raise Json2ClientError(f"Missing target account for codes {candidate_codes!r}")
    if len(rows) == 1:
        return int(rows[0]["id"])
    preferred = preferred_account_prefix(preferred_role)
    if preferred is not None:
        matching = [
            row for row in rows if str(row.get("account_type") or "").startswith(preferred)
        ]
        if len(matching) == 1:
            return int(matching[0]["id"])
    raise Json2ClientError(f"Ambiguous target account for codes {candidate_codes!r}")


def preferred_account_prefix(preferred_role: str | None) -> str | None:
    if preferred_role in {"asset", "receivable"}:
        return "asset"
    if preferred_role in {"liability", "payable"}:
        return "liability"
    return None


def find_target_account_by_name(
    client: Json2Client,
    *,
    target_company_id: int,
    reference_account: ReferenceAccount,
) -> int | None:
    rows = client.search_read(
        "account.account",
        domain=[
            ["company_ids", "in", [target_company_id]],
            ["name", "=", reference_account.name],
            ["account_type", "=", reference_account.account_type],
        ],
        fields=["id"],
        order="id",
        context=company_access_context(target_company_id),
    )
    if not rows:
        return None
    if len(rows) != 1:
        raise Json2ClientError(
            f"Expected one target account named {reference_account.name!r}, got {len(rows)}"
        )
    return int(rows[0]["id"])
