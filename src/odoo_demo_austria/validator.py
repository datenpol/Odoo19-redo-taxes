from __future__ import annotations

from ._validator_cosmetic import (
    validate_accounts,
    validate_currency,
    validate_fiscal_positions,
    validate_journals,
    validate_tax_groups,
    validate_taxes,
)
from ._validator_identity import (
    validate_bank_identity,
    validate_company_identity,
    validate_partner_identity,
)
from ._validator_report_aware import (
    validate_report_aware_repartition_lines,
    validate_report_aware_tax_groups,
    validate_report_aware_taxes,
)
from ._validator_support import ValidationIssue
from .json2_client import Json2Client
from .models import ProjectSpec
from .planner import resolve_bank_trust_lock, resolve_company_partner_id


def validate_cosmetic_state(
    client: Json2Client,
    spec: ProjectSpec,
) -> list[ValidationIssue]:
    lang = spec.localization.primary_display_language
    partner_id = resolve_company_partner_id(client, spec.source_environment.company_id)
    bank_fields_locked = resolve_bank_trust_lock(client, spec.identity.bank.partner_bank_id)
    issues: list[ValidationIssue] = []

    validate_company_identity(client, spec, issues)
    validate_partner_identity(client, spec, partner_id, issues)
    validate_bank_identity(client, spec, bank_fields_locked, issues)
    validate_currency(
        client,
        spec,
        spec.currency.displaced_reference_currency.currency_id,
        issues,
    )
    validate_currency(
        client,
        spec,
        spec.currency.active_company_currency.currency_id,
        issues,
    )
    validate_tax_groups(client, spec, lang, issues)
    validate_taxes(client, spec, lang, issues)
    validate_journals(client, spec, lang, issues)
    validate_fiscal_positions(client, spec, lang, issues)
    validate_accounts(client, spec, lang, issues)
    return issues


def validate_report_aware_state(
    client: Json2Client,
    spec: ProjectSpec,
) -> list[ValidationIssue]:
    issues = validate_cosmetic_state(client, spec)
    validate_report_aware_tax_groups(client, spec, issues)
    validate_report_aware_taxes(client, spec, issues)
    validate_report_aware_repartition_lines(client, spec, issues)
    return issues
