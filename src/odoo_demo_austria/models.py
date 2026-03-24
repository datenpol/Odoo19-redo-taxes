from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class SpecValidationError(ValueError):
    """Raised when the mapping spec is incomplete or malformed."""


@dataclass(frozen=True)
class TranslatedText:
    base: str
    translations: dict[str, str]

    def value_for(self, lang: str) -> str:
        return self.translations.get(lang, self.base)


@dataclass(frozen=True)
class HtmlTranslatedText:
    base_html: str
    translations: dict[str, str]

    def value_for(self, lang: str) -> str:
        return self.translations.get(lang, self.base_html)


@dataclass(frozen=True)
class SourceEnvironment:
    name: str
    url: str
    company_id: int
    company_name: str


@dataclass(frozen=True)
class LocalizationSpec:
    primary_display_language: str
    reference_harvest_date: str
    reference_snapshot_file: Path
    translation_write_policy: tuple[str, ...]


@dataclass(frozen=True)
class CompanyIdentity:
    target_company_name: str
    target_display_name: str
    target_partner_name: str
    street: str
    street2: str
    zip_code: str
    city: str
    country_id: int
    state_id: int | None
    vat: str
    phone: str
    email: str
    website: str


@dataclass(frozen=True)
class BankIdentity:
    partner_bank_id: int
    acc_number: str
    bank_id: int | None
    allow_out_payment: bool


@dataclass(frozen=True)
class IdentitySpec:
    company: CompanyIdentity
    bank: BankIdentity


@dataclass(frozen=True)
class CurrencyRecordSpec:
    currency_id: int
    source_code: str
    target_code: str
    target_symbol: str
    target_full_name: TranslatedText
    target_unit_label: TranslatedText
    target_subunit_label: TranslatedText
    target_position: str
    keep_rate_as_is: bool = True


@dataclass(frozen=True)
class CurrencySpec:
    strategy: str
    active_company_currency: CurrencyRecordSpec
    displaced_reference_currency: CurrencyRecordSpec


@dataclass(frozen=True)
class TaxGroupCosmeticSpec:
    target_name: TranslatedText


@dataclass(frozen=True)
class TaxGroupReportAwareSpec:
    target_country_id: int
    reference_group_id: int


@dataclass(frozen=True)
class TaxGroupSpec:
    record_id: int
    source_name: str
    cosmetic: TaxGroupCosmeticSpec
    report_aware: TaxGroupReportAwareSpec


@dataclass(frozen=True)
class TaxCosmeticSpec:
    target_name: TranslatedText
    target_description: HtmlTranslatedText
    target_invoice_label: TranslatedText
    target_amount: float
    target_group_id: int


@dataclass(frozen=True)
class TaxReportAwareSpec:
    target_country_id: int
    reference_tax_id: int
    reference_tax_name: str
    reference_invoice_tags: tuple[int, ...]
    reference_tax_tags: tuple[int, ...]
    target_tax_account_id: int | None
    target_tax_account_name: str | None
    candidate_tax_account_id: int | None
    candidate_tax_account_name: str | None
    note: str | None


@dataclass(frozen=True)
class TaxSpec:
    record_id: int
    source_name: str
    source_type_tax_use: str
    default_company_sale_tax: bool
    default_company_purchase_tax: bool
    cosmetic: TaxCosmeticSpec
    report_aware: TaxReportAwareSpec


@dataclass(frozen=True)
class JournalSpec:
    record_id: int
    source_name: str
    target_name: TranslatedText
    reference_journal_id: int | None


@dataclass(frozen=True)
class FiscalPositionSpec:
    record_id: int | None
    source_name: str | None
    create_if_missing: bool
    target_name: TranslatedText
    sequence: int
    auto_apply: bool
    country_id: int | None
    country_group_id: int | None
    vat_required: bool
    foreign_vat: str | None
    target_tax_ids: tuple[int, ...]


@dataclass(frozen=True)
class AccountSpec:
    record_id: int
    code: str
    source_name: str
    target_name: TranslatedText
    posted_lines: int
    reference_account_id: int | None


@dataclass(frozen=True)
class ChartSpec:
    strategy: str
    reason: str
    name_precedence: tuple[str, ...]
    core_reference_accounts: dict[str, int]
    explicit_accounts: tuple[AccountSpec, ...]


@dataclass(frozen=True)
class ValidationSpec:
    expected_company_country_id: int
    expected_company_currency_id_after_cosmetic: int
    expected_default_sale_tax_id: int
    expected_default_purchase_tax_id: int
    api_assertions: tuple[str, ...]
    ui_spot_checks: tuple[str, ...]


@dataclass(frozen=True)
class ProjectSpec:
    version: str
    status: str
    source_environment: SourceEnvironment
    localization: LocalizationSpec
    identity: IdentitySpec
    currency: CurrencySpec
    tax_groups: tuple[TaxGroupSpec, ...]
    taxes: tuple[TaxSpec, ...]
    journals: tuple[JournalSpec, ...]
    fiscal_positions: tuple[FiscalPositionSpec, ...]
    chart: ChartSpec
    validation: ValidationSpec
    spec_path: Path
