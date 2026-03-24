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
from .planner import resolve_cosmetic_targets


def validate_cosmetic_state(
    client: Json2Client,
    spec: ProjectSpec,
) -> list[ValidationIssue]:
    lang = spec.localization.primary_display_language
    resolved = resolve_cosmetic_targets(client, spec)
    issues: list[ValidationIssue] = []

    validate_company_identity(client, spec, resolved, issues)
    validate_partner_identity(client, spec, resolved, issues)
    validate_bank_identity(client, spec, resolved, issues)
    validate_currency(client, resolved.displaced_reference_currency, lang, issues)
    validate_currency(client, resolved.active_company_currency, lang, issues)
    validate_tax_groups(client, resolved.tax_groups, lang, issues)
    validate_taxes(client, resolved.taxes, lang, issues)
    validate_journals(client, resolved.journals, lang, issues)
    validate_fiscal_positions(client, resolved, lang, issues)
    validate_accounts(client, resolved.accounts, lang, issues)
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
