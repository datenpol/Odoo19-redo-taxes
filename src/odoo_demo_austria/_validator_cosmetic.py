from __future__ import annotations

from typing import Any

from ._validator_support import (
    ValidationIssue,
    expect_equal,
    index_by_id,
    many2one_id,
    normalize_rich_text,
    single,
)
from .json2_client import Json2Client
from .models import (
    ResolvedAccount,
    ResolvedCurrencyRecord,
    ResolvedFiscalPosition,
    ResolvedJournal,
    ResolvedProject,
    ResolvedTax,
    ResolvedTaxGroup,
)


def validate_currency(
    client: Json2Client,
    resolved: ResolvedCurrencyRecord,
    lang: str,
    issues: list[ValidationIssue],
) -> None:
    fields = [
        "name",
        "symbol",
        "full_name",
        "currency_unit_label",
        "currency_subunit_label",
        "position",
    ]
    base_record = single(client.read("res.currency", [resolved.record_id], fields))
    translated_record = single(
        client.read("res.currency", [resolved.record_id], fields, context={"lang": lang})
    )

    prefix = f"res.currency[{resolved.record_id}]"
    expect_equal(issues, prefix, "name", base_record.get("name"), resolved.spec.target_code)
    expect_equal(issues, prefix, "symbol", base_record.get("symbol"), resolved.spec.target_symbol)
    expect_equal(
        issues,
        prefix,
        "position",
        base_record.get("position"),
        resolved.spec.target_position,
    )
    expect_equal(
        issues,
        prefix,
        "full_name(display)",
        normalize_rich_text(translated_record.get("full_name")),
        resolved.spec.target_full_name.value_for(lang),
    )
    expect_equal(
        issues,
        prefix,
        "currency_unit_label(display)",
        normalize_rich_text(translated_record.get("currency_unit_label")),
        resolved.spec.target_unit_label.value_for(lang),
    )
    expect_equal(
        issues,
        prefix,
        "currency_subunit_label(display)",
        normalize_rich_text(translated_record.get("currency_subunit_label")),
        resolved.spec.target_subunit_label.value_for(lang),
    )


def validate_tax_groups(
    client: Json2Client,
    resolved: tuple[ResolvedTaxGroup, ...],
    lang: str,
    issues: list[ValidationIssue],
) -> None:
    ids = [item.record_id for item in resolved]
    translated = index_by_id(
        client.read("account.tax.group", ids, ["name"], context={"lang": lang})
    )
    for item in resolved:
        prefix = f"account.tax.group[{item.record_id}]"
        expect_equal(
            issues,
            prefix,
            "name(display)",
            normalize_rich_text(translated[item.record_id].get("name")),
            item.spec.cosmetic.target_name.value_for(lang),
        )


def validate_taxes(
    client: Json2Client,
    resolved: tuple[ResolvedTax, ...],
    lang: str,
    issues: list[ValidationIssue],
) -> None:
    ids = [item.record_id for item in resolved]
    fields = ["name", "description", "invoice_label", "amount", "tax_group_id"]
    base = index_by_id(client.read("account.tax", ids, fields))
    translated = index_by_id(client.read("account.tax", ids, fields, context={"lang": lang}))
    for item in resolved:
        prefix = f"account.tax[{item.record_id}]"
        record = base[item.record_id]
        translated_record = translated[item.record_id]
        expect_equal(
            issues,
            prefix,
            "name(display)",
            normalize_rich_text(translated_record.get("name")),
            item.spec.cosmetic.target_name.value_for(lang),
        )
        expect_equal(
            issues,
            prefix,
            "description(display)",
            normalize_rich_text(translated_record.get("description")),
            item.spec.cosmetic.target_description.value_for(lang),
        )
        expect_equal(
            issues,
            prefix,
            "invoice_label(display)",
            normalize_rich_text(translated_record.get("invoice_label")),
            item.spec.cosmetic.target_invoice_label.value_for(lang),
        )
        expect_equal(
            issues,
            prefix,
            "amount",
            record.get("amount"),
            item.spec.cosmetic.target_amount,
        )
        expect_equal(
            issues,
            prefix,
            "tax_group_id",
            many2one_id(record.get("tax_group_id")),
            item.tax_group_id,
        )


def validate_journals(
    client: Json2Client,
    resolved: tuple[ResolvedJournal, ...],
    lang: str,
    issues: list[ValidationIssue],
) -> None:
    ids = [item.record_id for item in resolved]
    translated = index_by_id(client.read("account.journal", ids, ["name"], context={"lang": lang}))
    for item in resolved:
        prefix = f"account.journal[{item.record_id}]"
        expect_equal(
            issues,
            prefix,
            "name(display)",
            normalize_rich_text(translated[item.record_id].get("name")),
            item.spec.target_name.value_for(lang),
        )


def validate_accounts(
    client: Json2Client,
    resolved: tuple[ResolvedAccount, ...],
    lang: str,
    issues: list[ValidationIssue],
) -> None:
    ids = [item.record_id for item in resolved]
    base = index_by_id(client.read("account.account", ids, ["code"]))
    translated = index_by_id(client.read("account.account", ids, ["name"], context={"lang": lang}))
    for item in resolved:
        prefix = f"account.account[{item.record_id}]"
        expect_equal(issues, prefix, "code", base[item.record_id].get("code"), item.spec.code)
        expect_equal(
            issues,
            prefix,
            "name(display)",
            normalize_rich_text(translated[item.record_id].get("name")),
            item.spec.target_name.value_for(lang),
        )


def validate_fiscal_positions(
    client: Json2Client,
    resolved: ResolvedProject,
    lang: str,
    issues: list[ValidationIssue],
) -> None:
    records = client.search_read(
        "account.fiscal.position",
        domain=[["company_id", "=", resolved.company_id]],
        fields=[
            "id",
            "name",
            "sequence",
            "auto_apply",
            "country_id",
            "country_group_id",
            "vat_required",
            "foreign_vat",
            "tax_ids",
        ],
        order="sequence,id",
        context={"lang": lang},
    )
    by_id = index_by_id(records)

    for item in resolved.fiscal_positions:
        record = _resolve_fiscal_position_record(item, records, by_id, lang, issues)
        if record is None:
            continue
        prefix = f"account.fiscal.position[{record['id']}]"
        expect_equal(
            issues,
            prefix,
            "name(display)",
            normalize_rich_text(record.get("name")),
            item.spec.target_name.value_for(lang),
        )
        expect_equal(issues, prefix, "sequence", record.get("sequence"), item.spec.sequence)
        expect_equal(issues, prefix, "auto_apply", record.get("auto_apply"), item.spec.auto_apply)
        expect_equal(
            issues,
            prefix,
            "country_id",
            many2one_id(record.get("country_id")),
            item.spec.country_id,
        )
        expect_equal(
            issues,
            prefix,
            "country_group_id",
            many2one_id(record.get("country_group_id")),
            item.spec.country_group_id,
        )
        expect_equal(
            issues,
            prefix,
            "vat_required",
            record.get("vat_required"),
            item.spec.vat_required,
        )
        expect_equal(
            issues,
            prefix,
            "foreign_vat",
            record.get("foreign_vat"),
            item.spec.foreign_vat,
        )
        expect_equal(
            issues,
            prefix,
            "tax_ids",
            list(record.get("tax_ids", [])),
            list(item.spec.target_tax_ids),
        )


def _resolve_fiscal_position_record(
    item: ResolvedFiscalPosition,
    records: list[dict[str, Any]],
    by_id: dict[int, dict[str, Any]],
    lang: str,
    issues: list[ValidationIssue],
) -> dict[str, Any] | None:
    if item.record_id is not None:
        record = by_id.get(item.record_id)
        if record is None:
            issues.append(
                ValidationIssue(
                    scope="account.fiscal.position",
                    message=f"Missing fiscal position id {item.record_id}",
                )
            )
        return record

    matches = [
        record
        for record in records
        if normalize_rich_text(record.get("name")) == item.spec.target_name.value_for(lang)
    ]
    if len(matches) != 1:
        issues.append(
            ValidationIssue(
                scope="account.fiscal.position",
                message=(
                    "Expected exactly one fiscal position named "
                    f"{item.spec.target_name.value_for(lang)!r}, got {len(matches)}"
                ),
            )
        )
        return None
    return matches[0]
