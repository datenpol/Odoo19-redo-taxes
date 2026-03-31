from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any, cast

from odoo_demo_austria._planner_reference_tax_sync import build_reference_tax_sync_operation
from odoo_demo_austria._reference_company import resolve_reference_company
from odoo_demo_austria.json2_client import Json2Client
from odoo_demo_austria.models import (
    ProjectSpec,
    ResolvedAccount,
    ResolvedBank,
    ResolvedCurrencyRecord,
    ResolvedFiscalPosition,
    ResolvedJournal,
    ResolvedProject,
    ResolvedTax,
    ResolvedTaxGroup,
)
from odoo_demo_austria.spec_loader import load_spec

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "data" / "austria-cosmetic-mapping-spec.draft.yaml"


class FakeReferenceCompanyClient:
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
            name = next(value for field, _operator, value in domain if field == "name")
            return [{"id": 2, "name": name}]
        if model == "account.fiscal.position":
            company_id = next(value for field, _operator, value in domain if field == "company_id")
            names = next(value for field, _operator, value in domain if field == "name")
            return [
                {"id": company_id * 100 + index, "name": name}
                for index, name in enumerate(names, start=1)
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
        del ids, fields, context
        raise AssertionError(f"Unexpected read model: {model}")


class ReferenceCompanyResolutionTests(unittest.TestCase):
    def _resolved_fixture(self, project: ProjectSpec) -> ResolvedProject:
        return ResolvedProject(
            company_id=project.source_environment.company_id,
            company_partner_id=1,
            bank=ResolvedBank(record_id=2, bank_fields_locked=False),
            active_company_currency=ResolvedCurrencyRecord(
                spec=project.currency.active_company_currency,
                record_id=project.currency.active_company_currency.currency_id,
            ),
            displaced_reference_currency=ResolvedCurrencyRecord(
                spec=project.currency.displaced_reference_currency,
                record_id=project.currency.displaced_reference_currency.currency_id,
            ),
            tax_groups=tuple(
                ResolvedTaxGroup(spec=item, record_id=item.record_id)
                for item in project.tax_groups
            ),
            taxes=tuple(
                ResolvedTax(
                    spec=item,
                    record_id=item.record_id,
                    tax_group_id=item.cosmetic.target_group_id,
                )
                for item in project.taxes
            ),
            journals=tuple(
                ResolvedJournal(spec=item, record_id=item.record_id)
                for item in project.journals
            ),
            fiscal_positions=tuple(
                ResolvedFiscalPosition(spec=item, record_id=item.record_id)
                for item in project.fiscal_positions
            ),
            accounts=tuple(
                ResolvedAccount(
                    spec=item,
                    record_id=None if item.create_if_missing else item.record_id,
                )
                for item in project.chart.explicit_accounts
            ),
        )

    def test_resolves_same_database_reference_company_by_name(self) -> None:
        spec = load_spec(SPEC_PATH)
        client = cast(Json2Client, FakeReferenceCompanyClient())

        resolved = resolve_reference_company(client, spec)

        self.assertEqual(resolved.record_id, 2)
        self.assertEqual(resolved.name, "AT Company")

    def test_reference_tax_sync_uses_resolved_same_database_company_id(self) -> None:
        spec = load_spec(SPEC_PATH)
        client = cast(Json2Client, FakeReferenceCompanyClient())

        operation = build_reference_tax_sync_operation(client, spec, self._resolved_fixture(spec))

        assert operation is not None
        self.assertEqual(operation.reference_company_id, 2)
        self.assertEqual(operation.reference_company_name, "AT Company")


if __name__ == "__main__":
    unittest.main()
