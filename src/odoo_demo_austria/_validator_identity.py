from __future__ import annotations

from ._validator_support import ValidationIssue, expect_equal, many2one_id, single
from .json2_client import Json2Client
from .models import ProjectSpec, ResolvedProject


def validate_company_identity(
    client: Json2Client,
    spec: ProjectSpec,
    resolved: ResolvedProject,
    issues: list[ValidationIssue],
) -> None:
    company = single(client.read("res.company", [resolved.company_id], ["name", "currency_id"]))
    expect_equal(
        issues,
        "res.company",
        "name",
        company.get("name"),
        spec.identity.company.target_company_name,
    )
    expect_equal(
        issues,
        "res.company",
        "currency_id",
        many2one_id(company.get("currency_id")),
        resolved.active_company_currency.record_id,
    )


def validate_partner_identity(
    client: Json2Client,
    spec: ProjectSpec,
    resolved: ResolvedProject,
    issues: list[ValidationIssue],
) -> None:
    partner = single(
        client.read(
            "res.partner",
            [resolved.company_partner_id],
            [
                "name",
                "street",
                "street2",
                "zip",
                "city",
                "country_id",
                "state_id",
                "vat",
                "phone",
                "email",
                "website",
            ],
        )
    )
    company = spec.identity.company
    expect_equal(issues, "res.partner", "name", partner.get("name"), company.target_partner_name)
    expect_equal(issues, "res.partner", "street", partner.get("street"), company.street)
    expect_equal(issues, "res.partner", "street2", partner.get("street2"), company.street2)
    expect_equal(issues, "res.partner", "zip", partner.get("zip"), company.zip_code)
    expect_equal(issues, "res.partner", "city", partner.get("city"), company.city)
    expect_equal(
        issues,
        "res.partner",
        "country_id",
        many2one_id(partner.get("country_id")),
        company.country_id,
    )
    expect_equal(
        issues,
        "res.partner",
        "state_id",
        many2one_id(partner.get("state_id")),
        company.state_id,
    )
    expect_equal(issues, "res.partner", "vat", partner.get("vat"), company.vat)
    expect_equal(issues, "res.partner", "phone", partner.get("phone"), company.phone)
    expect_equal(issues, "res.partner", "email", partner.get("email"), company.email)
    expect_equal(issues, "res.partner", "website", partner.get("website"), company.website)


def validate_bank_identity(
    client: Json2Client,
    spec: ProjectSpec,
    resolved: ResolvedProject,
    issues: list[ValidationIssue],
) -> None:
    bank = single(
        client.read(
            "res.partner.bank",
            [resolved.bank.record_id],
            ["acc_number", "bank_id", "allow_out_payment", "lock_trust_fields"],
        )
    )
    if not resolved.bank.bank_fields_locked:
        expect_equal(
            issues,
            "res.partner.bank",
            "acc_number",
            bank.get("acc_number"),
            spec.identity.bank.acc_number,
        )
        expect_equal(
            issues,
            "res.partner.bank",
            "bank_id",
            many2one_id(bank.get("bank_id")),
            spec.identity.bank.bank_id,
        )
    expect_equal(
        issues,
        "res.partner.bank",
        "allow_out_payment",
        bank.get("allow_out_payment"),
        spec.identity.bank.allow_out_payment,
    )
