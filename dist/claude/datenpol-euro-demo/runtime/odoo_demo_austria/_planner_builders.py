from __future__ import annotations

from typing import Any

from ._planner_fiscal_position_accounts import (
    build_fiscal_position_account_mapping_operations,
)
from ._planner_types import (
    EnsureCreateOperation,
    PlanOperation,
    WriteOperation,
    ensure_operation_safe,
)
from ._planner_write_helpers import (
    build_ensure_create_operation,
    build_translated_write_operations,
)
from .models import (
    ProjectSpec,
    ResolvedAccount,
    ResolvedCurrencyRecord,
    ResolvedFiscalPosition,
    ResolvedJournal,
    ResolvedProject,
    ResolvedTax,
    ResolvedTaxGroup,
)


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
    operations.extend(
        _build_account_operations(
            resolved.accounts,
            company_id=resolved.company_id,
            lang=lang,
        )
    )
    operations.extend(build_fiscal_position_account_mapping_operations(resolved))
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
    return build_translated_write_operations(
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
            build_translated_write_operations(
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
            build_translated_write_operations(
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
        if journal.record_id is None:
            continue
        operations.extend(
            build_translated_write_operations(
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
    company_id: int,
    lang: str,
) -> list[PlanOperation]:
    operations: list[PlanOperation] = []
    for account in accounts:
        if account.record_id is not None:
            operations.extend(
                build_translated_write_operations(
                    model="account.account",
                    record_id=account.record_id,
                    base_fields=_account_base_fields(account),
                    translated_fields={"name": account.spec.target_name},
                    lang=lang,
                    reason=(
                        f"Rename account {account.record_id} "
                        f"({account.spec.code}) cosmetically"
                    ),
                )
            )
            continue

        if account.spec.optional:
            continue
        if not account.spec.create_if_missing:
            raise ValueError(f"Account {account.spec.code!r} resolved without a record id")
        operations.append(
            _build_account_create_operation(
                account,
                company_id=company_id,
                lang=lang,
            )
        )
    return operations


def _account_base_fields(account: ResolvedAccount) -> dict[str, Any]:
    fields: dict[str, Any] = {"code": account.spec.code}
    if account.spec.account_type is not None:
        fields["account_type"] = account.spec.account_type
    if account.spec.reconcile:
        fields["reconcile"] = True
    return fields


def _build_account_create_operation(
    account: ResolvedAccount,
    *,
    company_id: int,
    lang: str,
) -> EnsureCreateOperation:
    account_type = account.spec.account_type
    if account_type is None:
        raise ValueError(f"Account {account.spec.code!r} is missing account_type metadata")
    return build_ensure_create_operation(
        model="account.account",
        lookup_domain=[
            ["company_ids", "in", [company_id]],
            ["code", "=", account.spec.code],
        ],
        create_fields={
            **_account_base_fields(account),
            "account_type": account_type,
            "reconcile": account.spec.reconcile,
            "company_ids": [[6, 0, [company_id]]],
        },
        translated_fields={"name": account.spec.target_name},
        lang=lang,
        reason=f"Ensure account {account.spec.code} exists cosmetically",
    )


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
            build_translated_write_operations(
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
        build_ensure_create_operation(
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


def _ensure_operations_safe(operations: list[PlanOperation]) -> None:
    for operation in operations:
        ensure_operation_safe(operation)
