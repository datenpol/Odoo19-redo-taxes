from __future__ import annotations

from ._validator_support import (
    ValidationIssue,
    expect_equal,
    index_by_id,
    many2one_id,
)
from .json2_client import Json2Client
from .models import ProjectSpec


def validate_report_aware_tax_groups(
    client: Json2Client,
    spec: ProjectSpec,
    issues: list[ValidationIssue],
) -> None:
    ids = [item.record_id for item in spec.tax_groups]
    records = index_by_id(client.read("account.tax.group", ids, ["country_id"]))
    for item in spec.tax_groups:
        prefix = f"account.tax.group[{item.record_id}]"
        expect_equal(
            issues,
            prefix,
            "country_id",
            many2one_id(records[item.record_id].get("country_id")),
            item.report_aware.target_country_id,
        )


def validate_report_aware_taxes(
    client: Json2Client,
    spec: ProjectSpec,
    issues: list[ValidationIssue],
) -> None:
    ids = [item.record_id for item in spec.taxes]
    records = index_by_id(client.read("account.tax", ids, ["country_id"]))
    for item in spec.taxes:
        prefix = f"account.tax[{item.record_id}]"
        expect_equal(
            issues,
            prefix,
            "country_id",
            many2one_id(records[item.record_id].get("country_id")),
            item.report_aware.target_country_id,
        )


def validate_report_aware_repartition_lines(
    client: Json2Client,
    spec: ProjectSpec,
    issues: list[ValidationIssue],
) -> None:
    tax_ids = [item.record_id for item in spec.taxes]
    records = client.search_read(
        "account.tax.repartition.line",
        domain=[["tax_id", "in", tax_ids]],
        fields=[
            "id",
            "tax_id",
            "document_type",
            "repartition_type",
            "account_id",
            "tag_ids",
            "use_in_tax_closing",
        ],
        order="tax_id,id",
    )
    for record in records:
        tax_ref = record.get("tax_id")
        if not isinstance(tax_ref, list) or not tax_ref:
            issues.append(
                ValidationIssue(
                    scope="account.tax.repartition.line",
                    message=f"Line {record.get('id')} has no tax_id",
                )
            )
            continue
        tax_id = int(tax_ref[0])
        spec_item = next(item for item in spec.taxes if item.record_id == tax_id)
        prefix = f"account.tax.repartition.line[{record['id']}]"
        if record.get("repartition_type") == "base":
            expected_tags = list(spec_item.report_aware.reference_invoice_tags)
            expected_account = None
            expected_closing = False
        else:
            expected_tags = list(spec_item.report_aware.reference_tax_tags)
            expected_account = spec_item.report_aware.target_tax_account_id
            expected_closing = True
        expect_equal(
            issues,
            prefix,
            "account_id",
            many2one_id(record.get("account_id")),
            expected_account,
        )
        expect_equal(
            issues,
            prefix,
            "tag_ids",
            list(record.get("tag_ids", [])),
            expected_tags,
        )
        expect_equal(
            issues,
            prefix,
            "use_in_tax_closing",
            record.get("use_in_tax_closing"),
            expected_closing,
        )
