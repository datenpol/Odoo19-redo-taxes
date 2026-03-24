from __future__ import annotations

from pathlib import Path
from typing import Any

from ._spec_project_extras import parse_chart, parse_validation
from ._spec_support import (
    optional_int,
    optional_str,
    parse_currency_record,
    parse_html_translated_text,
    parse_translated_text,
    require_bool,
    require_float,
    require_int,
    require_int_tuple,
    require_list,
    require_mapping,
    require_str,
    resolve_reference_snapshot,
)
from .models import (
    BankIdentity,
    CompanyIdentity,
    CurrencySpec,
    FiscalPositionSpec,
    IdentitySpec,
    JournalSpec,
    LocalizationSpec,
    ProjectSpec,
    SourceEnvironment,
    TaxCosmeticSpec,
    TaxGroupCosmeticSpec,
    TaxGroupReportAwareSpec,
    TaxGroupSpec,
    TaxReportAwareSpec,
    TaxSpec,
)


def build_project_spec(root: dict[str, Any], spec_path: Path) -> ProjectSpec:
    return ProjectSpec(
        version=require_str(root.get("version"), "version"),
        status=require_str(root.get("status"), "status"),
        source_environment=parse_source_environment(root),
        localization=parse_localization(root, spec_path),
        identity=parse_identity(root),
        currency=parse_currency(root),
        tax_groups=parse_tax_groups(root),
        taxes=parse_taxes(root),
        journals=parse_journals(root),
        fiscal_positions=parse_fiscal_positions(root),
        chart=parse_chart(root),
        validation=parse_validation(root),
        spec_path=spec_path,
    )


def parse_source_environment(root: dict[str, Any]) -> SourceEnvironment:
    source_environment = require_mapping(root.get("source_environment"), "source_environment")
    return SourceEnvironment(
        name=require_str(source_environment.get("name"), "source_environment.name"),
        url=require_str(source_environment.get("url"), "source_environment.url"),
        company_id=require_int(
            source_environment.get("company_id"),
            "source_environment.company_id",
        ),
        company_name=require_str(
            source_environment.get("company_name"),
            "source_environment.company_name",
        ),
    )


def parse_localization(root: dict[str, Any], spec_path: Path) -> LocalizationSpec:
    localization = require_mapping(root.get("localization"), "localization")
    return LocalizationSpec(
        primary_display_language=require_str(
            localization.get("primary_display_language"),
            "localization.primary_display_language",
        ),
        reference_harvest_date=require_str(
            localization.get("reference_harvest_date"),
            "localization.reference_harvest_date",
        ),
        reference_snapshot_file=resolve_reference_snapshot(spec_path, localization),
        translation_write_policy=tuple(
            require_str(item, "localization.translation_write_policy[]")
            for item in require_list(
                localization.get("translation_write_policy"),
                "localization.translation_write_policy",
            )
        ),
    )


def parse_identity(root: dict[str, Any]) -> IdentitySpec:
    identity = require_mapping(root.get("identity"), "identity")
    company = require_mapping(identity.get("company"), "identity.company")
    bank = require_mapping(identity.get("bank"), "identity.bank")
    return IdentitySpec(
        company=CompanyIdentity(
            target_company_name=require_str(
                company.get("target_company_name"),
                "identity.company.target_company_name",
            ),
            target_display_name=require_str(
                company.get("target_display_name"),
                "identity.company.target_display_name",
            ),
            target_partner_name=require_str(
                company.get("target_partner_name"),
                "identity.company.target_partner_name",
            ),
            street=require_str(company.get("street"), "identity.company.street"),
            street2=require_str(company.get("street2"), "identity.company.street2"),
            zip_code=require_str(company.get("zip"), "identity.company.zip"),
            city=require_str(company.get("city"), "identity.company.city"),
            country_id=require_int(company.get("country_id"), "identity.company.country_id"),
            state_id=optional_int(company.get("state_id"), "identity.company.state_id"),
            vat=require_str(company.get("vat"), "identity.company.vat"),
            phone=require_str(company.get("phone"), "identity.company.phone"),
            email=require_str(company.get("email"), "identity.company.email"),
            website=require_str(company.get("website"), "identity.company.website"),
        ),
        bank=BankIdentity(
            source_acc_number=optional_str(
                bank.get("source_acc_number"),
                "identity.bank.source_acc_number",
            ),
            acc_number=require_str(bank.get("acc_number"), "identity.bank.acc_number"),
            bank_id=optional_int(bank.get("bank_id"), "identity.bank.bank_id"),
            allow_out_payment=require_bool(
                bank.get("allow_out_payment"),
                "identity.bank.allow_out_payment",
            ),
        ),
    )


def parse_currency(root: dict[str, Any]) -> CurrencySpec:
    currency = require_mapping(root.get("currency"), "currency")
    return CurrencySpec(
        strategy=require_str(currency.get("strategy"), "currency.strategy"),
        active_company_currency=parse_currency_record(
            currency.get("active_company_currency"),
            "currency.active_company_currency",
        ),
        displaced_reference_currency=parse_currency_record(
            currency.get("displaced_reference_currency"),
            "currency.displaced_reference_currency",
        ),
    )


def parse_tax_groups(root: dict[str, Any]) -> tuple[TaxGroupSpec, ...]:
    tax_groups: list[TaxGroupSpec] = []
    for index, entry in enumerate(require_list(root.get("tax_groups"), "tax_groups")):
        item = require_mapping(entry, f"tax_groups[{index}]")
        cosmetic = require_mapping(item.get("cosmetic"), f"tax_groups[{index}].cosmetic")
        report_aware = require_mapping(
            item.get("report_aware"),
            f"tax_groups[{index}].report_aware",
        )
        tax_groups.append(
            TaxGroupSpec(
                record_id=require_int(item.get("id"), f"tax_groups[{index}].id"),
                source_name=require_str(
                    item.get("source_name"),
                    f"tax_groups[{index}].source_name",
                ),
                cosmetic=TaxGroupCosmeticSpec(
                    target_name=parse_translated_text(
                        cosmetic.get("target_name"),
                        f"tax_groups[{index}].cosmetic.target_name",
                    )
                ),
                report_aware=TaxGroupReportAwareSpec(
                    target_country_id=require_int(
                        report_aware.get("target_country_id"),
                        f"tax_groups[{index}].report_aware.target_country_id",
                    ),
                    reference_group_id=require_int(
                        report_aware.get("reference_group_id"),
                        f"tax_groups[{index}].report_aware.reference_group_id",
                    ),
                ),
            )
        )
    return tuple(tax_groups)


def parse_taxes(root: dict[str, Any]) -> tuple[TaxSpec, ...]:
    taxes: list[TaxSpec] = []
    for index, entry in enumerate(require_list(root.get("taxes"), "taxes")):
        item = require_mapping(entry, f"taxes[{index}]")
        cosmetic = require_mapping(item.get("cosmetic"), f"taxes[{index}].cosmetic")
        report_aware = require_mapping(item.get("report_aware"), f"taxes[{index}].report_aware")
        taxes.append(
            TaxSpec(
                record_id=require_int(item.get("id"), f"taxes[{index}].id"),
                source_name=require_str(item.get("source_name"), f"taxes[{index}].source_name"),
                source_type_tax_use=require_str(
                    item.get("source_type_tax_use"),
                    f"taxes[{index}].source_type_tax_use",
                ),
                default_company_sale_tax=require_bool(
                    item.get("default_company_sale_tax", False),
                    f"taxes[{index}].default_company_sale_tax",
                ),
                default_company_purchase_tax=require_bool(
                    item.get("default_company_purchase_tax", False),
                    f"taxes[{index}].default_company_purchase_tax",
                ),
                cosmetic=TaxCosmeticSpec(
                    target_name=parse_translated_text(
                        cosmetic.get("target_name"),
                        f"taxes[{index}].cosmetic.target_name",
                    ),
                    target_description=parse_html_translated_text(
                        cosmetic.get("target_description"),
                        f"taxes[{index}].cosmetic.target_description",
                    ),
                    target_invoice_label=parse_translated_text(
                        cosmetic.get("target_invoice_label"),
                        f"taxes[{index}].cosmetic.target_invoice_label",
                    ),
                    target_amount=require_float(
                        cosmetic.get("target_amount"),
                        f"taxes[{index}].cosmetic.target_amount",
                    ),
                    target_group_id=require_int(
                        cosmetic.get("target_group_id"),
                        f"taxes[{index}].cosmetic.target_group_id",
                    ),
                ),
                report_aware=TaxReportAwareSpec(
                    target_country_id=require_int(
                        report_aware.get("target_country_id"),
                        f"taxes[{index}].report_aware.target_country_id",
                    ),
                    reference_tax_id=require_int(
                        report_aware.get("reference_tax_id"),
                        f"taxes[{index}].report_aware.reference_tax_id",
                    ),
                    reference_tax_name=require_str(
                        report_aware.get("reference_tax_name"),
                        f"taxes[{index}].report_aware.reference_tax_name",
                    ),
                    reference_invoice_tags=require_int_tuple(
                        report_aware.get("reference_invoice_tags", []),
                        f"taxes[{index}].report_aware.reference_invoice_tags",
                    ),
                    reference_tax_tags=require_int_tuple(
                        report_aware.get("reference_tax_tags", []),
                        f"taxes[{index}].report_aware.reference_tax_tags",
                    ),
                    target_tax_account_id=optional_int(
                        report_aware.get("target_tax_account_id"),
                        f"taxes[{index}].report_aware.target_tax_account_id",
                    ),
                    target_tax_account_name=optional_str(
                        report_aware.get("target_tax_account_name"),
                        f"taxes[{index}].report_aware.target_tax_account_name",
                    ),
                    candidate_tax_account_id=optional_int(
                        report_aware.get("candidate_tax_account_id"),
                        f"taxes[{index}].report_aware.candidate_tax_account_id",
                    ),
                    candidate_tax_account_name=optional_str(
                        report_aware.get("candidate_tax_account_name"),
                        f"taxes[{index}].report_aware.candidate_tax_account_name",
                    ),
                    note=optional_str(
                        report_aware.get("note"),
                        f"taxes[{index}].report_aware.note",
                    ),
                ),
            )
        )
    return tuple(taxes)


def parse_journals(root: dict[str, Any]) -> tuple[JournalSpec, ...]:
    journals: list[JournalSpec] = []
    for index, entry in enumerate(require_list(root.get("journals"), "journals")):
        item = require_mapping(entry, f"journals[{index}]")
        journals.append(
            JournalSpec(
                record_id=require_int(item.get("id"), f"journals[{index}].id"),
                source_name=require_str(
                    item.get("source_name"),
                    f"journals[{index}].source_name",
                ),
                target_name=parse_translated_text(
                    item.get("target_name"),
                    f"journals[{index}].target_name",
                ),
                reference_journal_id=optional_int(
                    item.get("reference_journal_id"),
                    f"journals[{index}].reference_journal_id",
                ),
            )
        )
    return tuple(journals)


def parse_fiscal_positions(root: dict[str, Any]) -> tuple[FiscalPositionSpec, ...]:
    fiscal_positions: list[FiscalPositionSpec] = []
    for index, entry in enumerate(
        require_list(root.get("fiscal_positions", []), "fiscal_positions")
    ):
        item = require_mapping(entry, f"fiscal_positions[{index}]")
        fiscal_positions.append(
            FiscalPositionSpec(
                record_id=optional_int(item.get("id"), f"fiscal_positions[{index}].id"),
                source_name=optional_str(
                    item.get("source_name"),
                    f"fiscal_positions[{index}].source_name",
                ),
                create_if_missing=require_bool(
                    item.get("create_if_missing", False),
                    f"fiscal_positions[{index}].create_if_missing",
                ),
                target_name=parse_translated_text(
                    item.get("target_name"),
                    f"fiscal_positions[{index}].target_name",
                ),
                sequence=require_int(
                    item.get("sequence"),
                    f"fiscal_positions[{index}].sequence",
                ),
                auto_apply=require_bool(
                    item.get("auto_apply"),
                    f"fiscal_positions[{index}].auto_apply",
                ),
                country_id=optional_int(
                    item.get("country_id"),
                    f"fiscal_positions[{index}].country_id",
                ),
                country_group_id=optional_int(
                    item.get("country_group_id"),
                    f"fiscal_positions[{index}].country_group_id",
                ),
                vat_required=require_bool(
                    item.get("vat_required"),
                    f"fiscal_positions[{index}].vat_required",
                ),
                foreign_vat=optional_str(
                    item.get("foreign_vat"),
                    f"fiscal_positions[{index}].foreign_vat",
                ),
                target_tax_ids=require_int_tuple(
                    item.get("target_tax_ids", []),
                    f"fiscal_positions[{index}].target_tax_ids",
                ),
            )
        )
    return tuple(fiscal_positions)
