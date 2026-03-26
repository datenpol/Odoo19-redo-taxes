from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any, cast

from odoo_demo_austria._validator_reference_tax_surface import validate_reference_tax_surface
from odoo_demo_austria._validator_support import ValidationIssue
from odoo_demo_austria.json2_client import Json2Client
from odoo_demo_austria.spec_loader import load_spec

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "data" / "austria-cosmetic-mapping-spec.draft.yaml"


class FakeReferenceTaxSurfaceClient:
    def __init__(self, *, mismatch: bool, html_escaped_target: bool = False) -> None:
        self.mismatch = mismatch
        self.html_escaped_target = html_escaped_target

    def search_read(
        self,
        model: str,
        *,
        domain: list[Any],
        fields: list[str],
        order: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        del fields, order, context
        if model == "res.company":
            return [{"id": 3}]
        if model == "account.fiscal.position":
            company_id = next(value for field, _operator, value in domain if field == "company_id")
            name = next(value for field, _operator, value in domain if field == "name")
            record_id = 101 if company_id == 1 else 201
            return [{"id": record_id, "name": name}]
        if model == "account.tax":
            company_id = next(value for field, _operator, value in domain if field == "company_id")
            description = (
                "Different description"
                if self.mismatch and company_id == 1
                else (
                    "Range &gt;= 5000"
                    if self.html_escaped_target and company_id == 1
                    else "Range >= 5000"
                )
            )
            return [
                {
                    "id": 11 if company_id == 1 else 21,
                    "name": "0% Ust EX art6",
                    "type_tax_use": "sale",
                    "tax_scope": False,
                    "amount": 0.0,
                    "description": description,
                    "invoice_label": "0%",
                    "original_tax_ids": [],
                }
            ]
        raise AssertionError(f"Unexpected search_read model: {model}")

    def read(
        self,
        model: str,
        ids: list[int],
        fields: list[str],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        del fields, context
        if model == "account.fiscal.position":
            return [{"id": ids[0], "company_id": [1, "Datenpol Wohnatelier GmbH"]}]
        if model == "account.tax":
            return []
        raise AssertionError(f"Unexpected read model: {model}")


class ReferenceTaxSurfaceValidatorTests(unittest.TestCase):
    def test_reference_tax_surface_passes_when_rows_match(self) -> None:
        spec = load_spec(SPEC_PATH)
        issues: list[ValidationIssue] = []
        client = cast(Json2Client, FakeReferenceTaxSurfaceClient(mismatch=False))

        validate_reference_tax_surface(
            client,
            spec,
            target_fiscal_position_id=101,
            fiscal_position_name="National",
            lang="de_DE",
            prefix="account.fiscal.position[101]",
            issues=issues,
        )

        self.assertEqual(issues, [])

    def test_reference_tax_surface_reports_mismatch(self) -> None:
        spec = load_spec(SPEC_PATH)
        issues: list[ValidationIssue] = []
        client = cast(Json2Client, FakeReferenceTaxSurfaceClient(mismatch=True))

        validate_reference_tax_surface(
            client,
            spec,
            target_fiscal_position_id=101,
            fiscal_position_name="National",
            lang="de_DE",
            prefix="account.fiscal.position[101]",
            issues=issues,
        )

        self.assertEqual(len(issues), 1)
        self.assertIn("reference tax surface mismatch", issues[0].message)

    def test_reference_tax_surface_unescapes_html_entities(self) -> None:
        spec = load_spec(SPEC_PATH)
        issues: list[ValidationIssue] = []
        client = cast(
            Json2Client,
            FakeReferenceTaxSurfaceClient(mismatch=False, html_escaped_target=True),
        )

        validate_reference_tax_surface(
            client,
            spec,
            target_fiscal_position_id=101,
            fiscal_position_name="National",
            lang="de_DE",
            prefix="account.fiscal.position[101]",
            issues=issues,
        )

        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
