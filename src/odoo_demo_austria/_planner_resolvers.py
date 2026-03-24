from __future__ import annotations

from typing import Any

from ._planner_types import RepartitionLineRef
from .json2_client import Json2Client, Json2ClientError
from .models import (
    AccountSpec,
    BankIdentity,
    CurrencyRecordSpec,
    FiscalPositionSpec,
    JournalSpec,
    ProjectSpec,
    ResolvedAccount,
    ResolvedBank,
    ResolvedCurrencyRecord,
    ResolvedFiscalPosition,
    ResolvedJournal,
    ResolvedProject,
    ResolvedTax,
    ResolvedTaxGroup,
    TaxSpec,
)


def resolve_cosmetic_targets(client: Json2Client, spec: ProjectSpec) -> ResolvedProject:
    company = _resolve_company(client, spec)
    company_id = int(company["id"])
    company_partner_id = _many2one_id(company.get("partner_id"), "company.partner_id")
    active_company_currency = ResolvedCurrencyRecord(
        spec=spec.currency.active_company_currency,
        record_id=_many2one_id(company.get("currency_id"), "company.currency_id"),
    )
    displaced_reference_currency = _resolve_displaced_currency(
        client,
        spec.currency.displaced_reference_currency,
        active_currency_id=active_company_currency.record_id,
    )
    bank = _resolve_bank(client, company_partner_id, spec.identity.bank)
    taxes = _resolve_taxes(client, spec.taxes, company_id)
    tax_groups = _resolve_tax_groups(client, spec, taxes)
    journals = _resolve_journals(client, spec.journals, company_id)
    fiscal_positions = _resolve_fiscal_positions(client, spec.fiscal_positions, company_id)
    accounts = _resolve_accounts(client, spec.chart.explicit_accounts, company_id)
    return ResolvedProject(
        company_id=company_id,
        company_partner_id=company_partner_id,
        bank=bank,
        active_company_currency=active_company_currency,
        displaced_reference_currency=displaced_reference_currency,
        tax_groups=tax_groups,
        taxes=taxes,
        journals=journals,
        fiscal_positions=fiscal_positions,
        accounts=accounts,
    )


def resolve_repartition_lines(
    client: Json2Client,
    tax_ids: list[int],
) -> dict[int, tuple[RepartitionLineRef, ...]]:
    records = client.search_read(
        "account.tax.repartition.line",
        domain=[["tax_id", "in", tax_ids]],
        fields=["id", "tax_id", "document_type", "repartition_type"],
        order="tax_id,id",
    )
    grouped: dict[int, list[RepartitionLineRef]] = {tax_id: [] for tax_id in tax_ids}
    for record in records:
        tax_id = _many2one_id(record.get("tax_id"), "account.tax.repartition.line.tax_id")
        grouped.setdefault(tax_id, []).append(
            RepartitionLineRef(
                record_id=int(record["id"]),
                tax_id=tax_id,
                document_type=str(record["document_type"]),
                repartition_type=str(record["repartition_type"]),
            )
        )
    return {tax_id: tuple(lines) for tax_id, lines in grouped.items()}


def _resolve_company(client: Json2Client, spec: ProjectSpec) -> dict[str, Any]:
    records = client.search_read(
        "res.company",
        domain=[["name", "in", list(_candidate_names(
            spec.source_environment.company_name,
            spec.identity.company.target_company_name,
        ))]],
        fields=["id", "name", "partner_id", "currency_id"],
        order="id",
    )
    return _single_record(records, model="res.company", label="source company")


def _resolve_displaced_currency(
    client: Json2Client,
    spec: CurrencyRecordSpec,
    *,
    active_currency_id: int,
) -> ResolvedCurrencyRecord:
    records = client.search_read(
        "res.currency",
        domain=[["name", "in", list(_candidate_names(spec.source_code, spec.target_code))]],
        fields=["id", "name"],
        order="id",
    )
    matches = [record for record in records if int(record["id"]) != active_currency_id]
    record = _single_record(matches, model="res.currency", label=f"currency {spec.source_code}")
    return ResolvedCurrencyRecord(spec=spec, record_id=int(record["id"]))


def _resolve_bank(client: Json2Client, partner_id: int, spec: BankIdentity) -> ResolvedBank:
    records = client.search_read(
        "res.partner.bank",
        domain=[["partner_id", "=", partner_id]],
        fields=["id", "acc_number", "lock_trust_fields"],
        order="id",
    )
    acc_numbers = _candidate_names(spec.source_acc_number, spec.acc_number)
    matches = [record for record in records if str(record.get("acc_number")) in acc_numbers]
    if not matches:
        matches = records
    record = _single_record(matches, model="res.partner.bank", label="company bank account")
    return ResolvedBank(
        record_id=int(record["id"]),
        bank_fields_locked=bool(record.get("lock_trust_fields")),
    )


def _resolve_taxes(
    client: Json2Client,
    taxes: tuple[TaxSpec, ...],
    company_id: int,
) -> tuple[ResolvedTax, ...]:
    resolved: list[ResolvedTax] = []
    for spec in taxes:
        records = client.search_read(
            "account.tax",
            domain=[
                ["company_id", "=", company_id],
                ["type_tax_use", "=", spec.source_type_tax_use],
                [
                    "name",
                    "in",
                    list(_candidate_names(spec.source_name, spec.cosmetic.target_name.base)),
                ],
            ],
            fields=["id", "name", "tax_group_id"],
            order="id",
        )
        record = _single_record(records, model="account.tax", label=spec.source_name)
        resolved.append(
            ResolvedTax(
                spec=spec,
                record_id=int(record["id"]),
                tax_group_id=_many2one_id(record.get("tax_group_id"), "account.tax.tax_group_id"),
            )
        )
    return tuple(resolved)


def _resolve_tax_groups(
    client: Json2Client,
    spec: ProjectSpec,
    taxes: tuple[ResolvedTax, ...],
) -> tuple[ResolvedTaxGroup, ...]:
    group_ids_by_ref: dict[int, int] = {}
    for tax in taxes:
        group_ref = tax.spec.cosmetic.target_group_id
        existing = group_ids_by_ref.get(group_ref)
        if existing is not None and existing != tax.tax_group_id:
            raise Json2ClientError(
                f"Taxes linked to group ref {group_ref} do not resolve to a single tax group"
            )
        group_ids_by_ref[group_ref] = tax.tax_group_id

    unique_group_ids = sorted(set(group_ids_by_ref.values()))
    records = client.read("account.tax.group", unique_group_ids, ["id", "name"])
    groups_by_id = {int(record["id"]): record for record in records}

    resolved: list[ResolvedTaxGroup] = []
    for group_spec in spec.tax_groups:
        group_id = group_ids_by_ref.get(group_spec.record_id)
        if group_id is None:
            raise Json2ClientError(f"No tax group resolved for spec ref {group_spec.record_id}")
        record = groups_by_id.get(group_id)
        if record is None:
            raise Json2ClientError(f"Missing resolved tax group id {group_id}")
        candidate_names = _candidate_names(
            group_spec.source_name,
            group_spec.cosmetic.target_name.base,
        )
        if str(record.get("name")) not in candidate_names:
            raise Json2ClientError(
                f"Resolved tax group {group_id} does not match expected names {candidate_names!r}"
            )
        resolved.append(ResolvedTaxGroup(spec=group_spec, record_id=group_id))
    return tuple(resolved)


def _resolve_journals(
    client: Json2Client,
    journals: tuple[JournalSpec, ...],
    company_id: int,
) -> tuple[ResolvedJournal, ...]:
    resolved: list[ResolvedJournal] = []
    for spec in journals:
        records = client.search_read(
            "account.journal",
            domain=[
                ["company_id", "=", company_id],
                ["name", "in", list(_candidate_names(spec.source_name, spec.target_name.base))],
            ],
            fields=["id", "name"],
            order="id",
        )
        record = _single_record(records, model="account.journal", label=spec.source_name)
        resolved.append(ResolvedJournal(spec=spec, record_id=int(record["id"])))
    return tuple(resolved)


def _resolve_fiscal_positions(
    client: Json2Client,
    fiscal_positions: tuple[FiscalPositionSpec, ...],
    company_id: int,
) -> tuple[ResolvedFiscalPosition, ...]:
    resolved: list[ResolvedFiscalPosition] = []
    for spec in fiscal_positions:
        records = client.search_read(
            "account.fiscal.position",
            domain=[
                ["company_id", "=", company_id],
                ["name", "in", list(_candidate_names(spec.source_name, spec.target_name.base))],
            ],
            fields=["id", "name"],
            order="id",
        )
        if not records:
            if spec.create_if_missing:
                resolved.append(ResolvedFiscalPosition(spec=spec, record_id=None))
                continue
            raise Json2ClientError(
                f"Missing fiscal position {spec.source_name or spec.target_name.base}"
            )
        record = _single_record(
            records,
            model="account.fiscal.position",
            label=spec.target_name.base,
        )
        resolved.append(ResolvedFiscalPosition(spec=spec, record_id=int(record["id"])))
    return tuple(resolved)


def _resolve_accounts(
    client: Json2Client,
    accounts: tuple[AccountSpec, ...],
    company_id: int,
) -> tuple[ResolvedAccount, ...]:
    resolved: list[ResolvedAccount] = []
    for spec in accounts:
        records = client.search_read(
            "account.account",
            domain=[
                ["company_ids", "in", [company_id]],
                ["name", "in", list(_candidate_names(spec.source_name, spec.target_name.base))],
            ],
            fields=["id", "name", "code"],
            order="id",
        )
        exact_code_matches = [
            record for record in records if str(record.get("code") or "") == spec.code
        ]
        if len(exact_code_matches) == 1:
            record = exact_code_matches[0]
        else:
            record = _single_record(records, model="account.account", label=spec.source_name)
        resolved.append(ResolvedAccount(spec=spec, record_id=int(record["id"])))
    return tuple(resolved)


def _candidate_names(*names: str | None) -> tuple[str, ...]:
    values: list[str] = []
    for name in names:
        if not name or name in values:
            continue
        values.append(name)
    return tuple(values)


def _many2one_id(value: Any, field_name: str) -> int:
    if isinstance(value, list) and value:
        return int(value[0])
    raise Json2ClientError(f"Expected a populated many2one for {field_name}")


def _single_record(
    records: list[dict[str, Any]],
    *,
    model: str,
    label: str,
) -> dict[str, Any]:
    if len(records) != 1:
        raise Json2ClientError(
            f"Expected exactly one {model} record for {label!r}, got {len(records)}"
        )
    return records[0]
