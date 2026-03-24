from __future__ import annotations

from typing import Any, Mapping

from ._planner_types import (
    EnsureCreateOperation,
    PlanOperation,
    WriteOperation,
    ensure_operation_safe,
)
from .models import (
    HtmlTranslatedText,
    ProjectSpec,
    ResolvedAccount,
    ResolvedCurrencyRecord,
    ResolvedFiscalPosition,
    ResolvedJournal,
    ResolvedProject,
    ResolvedTax,
    ResolvedTaxGroup,
    TranslatedText,
)

TranslatedField = TranslatedText | HtmlTranslatedText


def build_cosmetic_plan(
    spec: ProjectSpec,
    resolved: ResolvedProject,
) -> list[PlanOperation]:
    lang = spec.localization.primary_display_language
    operations: list[PlanOperation] = [
        _build_company_operation(spec, resolved),
        _build_partner_operation(spec, resolved),
        _build_bank_operation(spec, resolved),
    ]
    operations.extend(
        _build_currency_operations(
            resolved.displaced_reference_currency,
            lang=lang,
            reason_prefix="Move the seeded EUR currency out of the way",
        )
    )
    operations.extend(
        _build_currency_operations(
            resolved.active_company_currency,
            lang=lang,
            reason_prefix=("Rename the active USD company currency to Austrian-looking EUR labels"),
        )
    )
    operations.extend(_build_tax_group_operations(resolved.tax_groups, lang=lang))
    operations.extend(_build_tax_operations(resolved.taxes, lang=lang))
    operations.extend(_build_journal_operations(resolved.journals, lang=lang))
    operations.extend(_build_fiscal_position_operations(resolved, lang=lang))
    operations.extend(_build_account_operations(resolved.accounts, lang=lang))
    _ensure_operations_safe(operations)
    return operations


def _build_company_operation(spec: ProjectSpec, resolved: ResolvedProject) -> WriteOperation:
    return WriteOperation(
        model="res.company",
        ids=(resolved.company_id,),
        vals={
            "name": spec.identity.company.target_company_name,
            "currency_id": resolved.active_company_currency.record_id,
        },
        reason="Update company display name and active currency pointer",
    )


def _build_partner_operation(spec: ProjectSpec, resolved: ResolvedProject) -> WriteOperation:
    company = spec.identity.company
    return WriteOperation(
        model="res.partner",
        ids=(resolved.company_partner_id,),
        vals={
            "name": company.target_partner_name,
            "street": company.street,
            "street2": company.street2,
            "zip": company.zip_code,
            "city": company.city,
            "country_id": company.country_id,
            "state_id": company.state_id or False,
            "vat": company.vat,
            "phone": company.phone,
            "email": company.email,
            "website": company.website,
        },
        reason="Update company partner master data",
    )


def _build_bank_operation(spec: ProjectSpec, resolved: ResolvedProject) -> WriteOperation:
    bank_vals: dict[str, Any] = {
        "allow_out_payment": spec.identity.bank.allow_out_payment,
    }
    if not resolved.bank.bank_fields_locked:
        bank_vals["acc_number"] = spec.identity.bank.acc_number
        bank_vals["bank_id"] = spec.identity.bank.bank_id or False
    return WriteOperation(
        model="res.partner.bank",
        ids=(resolved.bank.record_id,),
        vals=bank_vals,
        reason="Update display bank details for the company partner",
    )


def _build_currency_operations(
    item: ResolvedCurrencyRecord,
    *,
    lang: str,
    reason_prefix: str,
) -> list[WriteOperation]:
    return _build_translated_write_operations(
        model="res.currency",
        record_id=item.record_id,
        base_fields={
            "name": item.spec.target_code,
            "symbol": item.spec.target_symbol,
            "position": item.spec.target_position,
        },
        translated_fields={
            "full_name": item.spec.target_full_name,
            "currency_unit_label": item.spec.target_unit_label,
            "currency_subunit_label": item.spec.target_subunit_label,
        },
        lang=lang,
        reason=reason_prefix,
    )


def _build_tax_group_operations(
    tax_groups: tuple[ResolvedTaxGroup, ...],
    *,
    lang: str,
) -> list[WriteOperation]:
    operations: list[WriteOperation] = []
    for tax_group in tax_groups:
        operations.extend(
            _build_translated_write_operations(
                model="account.tax.group",
                record_id=tax_group.record_id,
                base_fields={},
                translated_fields={"name": tax_group.spec.cosmetic.target_name},
                lang=lang,
                reason=f"Rename tax group {tax_group.record_id} cosmetically",
            )
        )
    return operations


def _build_tax_operations(
    taxes: tuple[ResolvedTax, ...],
    *,
    lang: str,
) -> list[WriteOperation]:
    operations: list[WriteOperation] = []
    for tax in taxes:
        operations.extend(
            _build_translated_write_operations(
                model="account.tax",
                record_id=tax.record_id,
                base_fields={
                    "amount": tax.spec.cosmetic.target_amount,
                    "tax_group_id": tax.tax_group_id,
                },
                translated_fields={
                    "name": tax.spec.cosmetic.target_name,
                    "description": tax.spec.cosmetic.target_description,
                    "invoice_label": tax.spec.cosmetic.target_invoice_label,
                },
                lang=lang,
                reason=f"Rename tax {tax.record_id} cosmetically",
            )
        )
    return operations


def _build_journal_operations(
    journals: tuple[ResolvedJournal, ...],
    *,
    lang: str,
) -> list[WriteOperation]:
    operations: list[WriteOperation] = []
    for journal in journals:
        operations.extend(
            _build_translated_write_operations(
                model="account.journal",
                record_id=journal.record_id,
                base_fields={},
                translated_fields={"name": journal.spec.target_name},
                lang=lang,
                reason=f"Rename journal {journal.record_id} cosmetically",
            )
        )
    return operations


def _build_account_operations(
    accounts: tuple[ResolvedAccount, ...],
    *,
    lang: str,
) -> list[WriteOperation]:
    operations: list[WriteOperation] = []
    for account in accounts:
        operations.extend(
            _build_translated_write_operations(
                model="account.account",
                record_id=account.record_id,
                base_fields={"code": account.spec.code},
                translated_fields={"name": account.spec.target_name},
                lang=lang,
                reason=(
                    f"Rename account {account.record_id} "
                    f"({account.spec.code}) cosmetically"
                ),
            )
        )
    return operations


def _build_translated_write_operations(
    *,
    model: str,
    record_id: int,
    base_fields: Mapping[str, Any],
    translated_fields: Mapping[str, TranslatedField],
    lang: str,
    reason: str,
) -> list[WriteOperation]:
    operations = [
        WriteOperation(
            model=model,
            ids=(record_id,),
            vals={**dict(base_fields), **_base_translation_values(translated_fields)},
            reason=reason,
        )
    ]
    translated_vals = _translated_values(translated_fields, lang)
    if translated_vals:
        operations.append(
            WriteOperation(
                model=model,
                ids=(record_id,),
                vals=translated_vals,
                context={"lang": lang},
                reason=f"{reason} ({lang} translation)",
            )
        )
    return operations


def _base_translation_values(
    translated_fields: Mapping[str, TranslatedField],
) -> dict[str, str]:
    base_vals: dict[str, str] = {}
    for field_name, value in translated_fields.items():
        if isinstance(value, HtmlTranslatedText):
            base_vals[field_name] = value.base_html
        else:
            base_vals[field_name] = value.base
    return base_vals


def _translated_values(
    translated_fields: Mapping[str, TranslatedField],
    lang: str,
) -> dict[str, str]:
    return {field_name: value.value_for(lang) for field_name, value in translated_fields.items()}


def _build_fiscal_position_operations(
    resolved: ResolvedProject,
    *,
    lang: str,
) -> list[PlanOperation]:
    operations: list[PlanOperation] = []
    for fiscal_position in resolved.fiscal_positions:
        operations.extend(
            _build_single_fiscal_position_operations(
                fiscal_position,
                company_id=resolved.company_id,
                lang=lang,
            )
        )
    return operations


def _build_single_fiscal_position_operations(
    fiscal_position: ResolvedFiscalPosition,
    *,
    company_id: int,
    lang: str,
) -> list[PlanOperation]:
    spec = fiscal_position.spec
    base_fields = {
        "sequence": spec.sequence,
        "auto_apply": spec.auto_apply,
        "country_id": spec.country_id or False,
        "country_group_id": spec.country_group_id or False,
        "vat_required": spec.vat_required,
        "foreign_vat": spec.foreign_vat or False,
        "tax_ids": [[6, 0, list(spec.target_tax_ids)]],
    }
    translated_fields = {"name": spec.target_name}

    if fiscal_position.record_id is not None:
        operations: list[PlanOperation] = []
        operations.extend(
            _build_translated_write_operations(
                model="account.fiscal.position",
                record_id=fiscal_position.record_id,
                base_fields=base_fields,
                translated_fields=translated_fields,
                lang=lang,
                reason=f"Align fiscal position {fiscal_position.record_id} cosmetically",
            )
        )
        return operations

    if not spec.create_if_missing:
        name = spec.target_name.base
        raise ValueError(f"Fiscal position {name!r} has no id and is not marked create_if_missing")

    return [
        _build_ensure_create_operation(
            model="account.fiscal.position",
            lookup_domain=[
                ["company_id", "=", company_id],
                ["name", "=", spec.target_name.base],
            ],
            create_fields={"company_id": company_id, **base_fields},
            translated_fields=translated_fields,
            lang=lang,
            reason=(
                f"Ensure fiscal position {spec.target_name.base} exists cosmetically"
            ),
        )
    ]


def _build_ensure_create_operation(
    *,
    model: str,
    lookup_domain: list[list[Any]],
    create_fields: Mapping[str, Any],
    translated_fields: Mapping[str, TranslatedField],
    lang: str,
    reason: str,
) -> EnsureCreateOperation:
    create_vals = {**dict(create_fields), **_base_translation_values(translated_fields)}
    translated_update_vals = _translated_values(translated_fields, lang)
    if translated_update_vals == {
        field_name: create_vals[field_name] for field_name in translated_update_vals
    }:
        update_vals: dict[str, Any] | None = None
    else:
        update_vals = translated_update_vals

    return EnsureCreateOperation(
        model=model,
        lookup_domain=lookup_domain,
        create_vals=create_vals,
        update_vals=update_vals,
        update_context={"lang": lang} if update_vals is not None else None,
        reason=reason,
    )


def _ensure_operations_safe(operations: list[PlanOperation]) -> None:
    for operation in operations:
        ensure_operation_safe(operation)
