from __future__ import annotations

from typing import Any

from ._reference_company import resolve_reference_company
from ._validator_support import ValidationIssue, index_by_id, normalize_rich_text
from .json2_client import Json2Client, Json2ClientError
from .models import ProjectSpec


def validate_reference_tax_surface(
    client: Json2Client,
    spec: ProjectSpec,
    *,
    target_fiscal_position_id: int,
    fiscal_position_name: str,
    lang: str,
    prefix: str,
    issues: list[ValidationIssue],
) -> None:
    reference_company_id = resolve_reference_company(client, spec).record_id
    reference_fiscal_position_id = _reference_fiscal_position_id(
        client,
        company_id=reference_company_id,
        fiscal_position_name=fiscal_position_name,
    )
    actual = _tax_surface(
        client,
        company_id=_target_company_id(client, target_fiscal_position_id),
        fiscal_position_id=target_fiscal_position_id,
        lang=lang,
    )
    expected = _tax_surface(
        client,
        company_id=reference_company_id,
        fiscal_position_id=reference_fiscal_position_id,
        lang=lang,
    )
    if actual != expected:
        issues.append(
            ValidationIssue(
                scope=prefix,
                message=_surface_difference_message(
                    fiscal_position_name,
                    expected=expected,
                    actual=actual,
                ),
            )
        )


def _reference_fiscal_position_id(
    client: Json2Client,
    *,
    company_id: int,
    fiscal_position_name: str,
) -> int:
    records = client.search_read(
        "account.fiscal.position",
        domain=[["company_id", "=", company_id], ["name", "=", fiscal_position_name]],
        fields=["id"],
        order="id",
    )
    if len(records) != 1:
        raise Json2ClientError(
            "Expected exactly one reference fiscal position "
            f"{fiscal_position_name!r}, got {len(records)}"
        )
    return int(records[0]["id"])


def _target_company_id(client: Json2Client, fiscal_position_id: int) -> int:
    record = client.read("account.fiscal.position", [fiscal_position_id], ["company_id"])
    company = record[0].get("company_id")
    if isinstance(company, list) and company:
        return int(company[0])
    raise Json2ClientError(f"Fiscal position {fiscal_position_id} is missing company_id")


def _tax_surface(
    client: Json2Client,
    *,
    company_id: int,
    fiscal_position_id: int,
    lang: str,
) -> list[tuple[str, str, tuple[str, ...], str, Any, str, str]]:
    taxes = client.search_read(
        "account.tax",
        domain=[
            ["company_id", "=", company_id],
            ["fiscal_position_ids", "in", [fiscal_position_id]],
        ],
        fields=[
            "id",
            "name",
            "type_tax_use",
            "tax_scope",
            "amount",
            "description",
            "invoice_label",
            "original_tax_ids",
        ],
        order="type_tax_use,name,id",
        context={"lang": lang},
    )
    original_names = _original_tax_names(client, taxes, lang=lang)
    return sorted(
        (
            str(row.get("type_tax_use") or ""),
            str(normalize_rich_text(row.get("name")) or ""),
            tuple(sorted(original_names.get(int(row["id"]), ()))),
            str(row.get("tax_scope") or ""),
            row.get("amount"),
            str(normalize_rich_text(row.get("description")) or ""),
            str(normalize_rich_text(row.get("invoice_label")) or ""),
        )
        for row in taxes
    )


def _original_tax_names(
    client: Json2Client,
    taxes: list[dict[str, Any]],
    *,
    lang: str,
) -> dict[int, tuple[str, ...]]:
    original_ids = sorted(
        {
            int(original_id)
            for row in taxes
            for original_id in row.get("original_tax_ids", [])
        }
    )
    if not original_ids:
        return {int(row["id"]): () for row in taxes}
    names_by_id = {
        record_id: str(normalize_rich_text(record.get("name")) or "")
        for record_id, record in index_by_id(
            client.read("account.tax", original_ids, ["id", "name"], context={"lang": lang})
        ).items()
    }
    return {
        int(row["id"]): tuple(
            names_by_id[int(original_id)] for original_id in row.get("original_tax_ids", [])
        )
        for row in taxes
    }


def _surface_difference_message(
    fiscal_position_name: str,
    *,
    expected: list[tuple[str, str, tuple[str, ...], str, Any, str, str]],
    actual: list[tuple[str, str, tuple[str, ...], str, Any, str, str]],
) -> str:
    expected_set = set(expected)
    actual_set = set(actual)
    missing = sorted(expected_set - actual_set)
    extra = sorted(actual_set - expected_set)
    parts = [
        (
            "reference tax surface mismatch for "
            f"{fiscal_position_name!r}: expected {len(expected)} rows, got {len(actual)}"
        )
    ]
    if missing:
        parts.append(f"missing {missing[0]!r}")
    if extra:
        parts.append(f"extra {extra[0]!r}")
    return "; ".join(parts)
