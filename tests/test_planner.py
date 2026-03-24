from __future__ import annotations

import unittest
from pathlib import Path

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
from odoo_demo_austria.planner import (
    EnsureCreateOperation,
    RepartitionLineRef,
    WriteOperation,
    build_cosmetic_plan,
    build_report_aware_plan,
    ensure_operation_safe,
)
from odoo_demo_austria.spec_loader import load_spec

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "data" / "austria-cosmetic-mapping-spec.draft.yaml"


class PlannerTests(unittest.TestCase):
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
                ResolvedAccount(spec=item, record_id=item.record_id)
                for item in project.chart.explicit_accounts
            ),
        )

    def _repartition_fixture(self) -> dict[int, tuple[RepartitionLineRef, ...]]:
        return {
            1: (
                RepartitionLineRef(1, 1, "invoice", "base"),
                RepartitionLineRef(2, 1, "invoice", "tax"),
                RepartitionLineRef(3, 1, "refund", "base"),
                RepartitionLineRef(4, 1, "refund", "tax"),
            ),
            2: (
                RepartitionLineRef(5, 2, "invoice", "base"),
                RepartitionLineRef(6, 2, "invoice", "tax"),
                RepartitionLineRef(7, 2, "refund", "base"),
                RepartitionLineRef(8, 2, "refund", "tax"),
            ),
            3: (
                RepartitionLineRef(9, 3, "invoice", "base"),
                RepartitionLineRef(10, 3, "invoice", "tax"),
                RepartitionLineRef(11, 3, "refund", "base"),
                RepartitionLineRef(12, 3, "refund", "tax"),
            ),
            4: (
                RepartitionLineRef(13, 4, "invoice", "base"),
                RepartitionLineRef(14, 4, "invoice", "tax"),
                RepartitionLineRef(15, 4, "refund", "base"),
                RepartitionLineRef(16, 4, "refund", "tax"),
            ),
        }

    def test_builds_full_cosmetic_plan(self) -> None:
        spec = load_spec(SPEC_PATH)
        operations = build_cosmetic_plan(spec, self._resolved_fixture(spec))
        first_operation = operations[0]
        assert isinstance(first_operation, WriteOperation)
        self.assertEqual(len(operations), 157)
        self.assertEqual(first_operation.model, "res.company")
        self.assertEqual(first_operation.vals["name"], "Datenpol Wohnatelier GmbH")
        for operation in operations:
            ensure_operation_safe(operation)

    def test_currency_rename_moves_seeded_eur_first(self) -> None:
        spec = load_spec(SPEC_PATH)
        operations = build_cosmetic_plan(spec, self._resolved_fixture(spec))
        write_operations = [
            operation for operation in operations if isinstance(operation, WriteOperation)
        ]
        displaced_index = next(
            index
            for index, operation in enumerate(write_operations)
            if operation.model == "res.currency"
            and operation.ids == (126,)
            and operation.context is None
        )
        active_index = next(
            index
            for index, operation in enumerate(write_operations)
            if operation.model == "res.currency"
            and operation.ids == (1,)
            and operation.context is None
        )
        self.assertLess(displaced_index, active_index)
        self.assertEqual(write_operations[displaced_index].vals["name"], "XEU")
        self.assertEqual(write_operations[active_index].vals["name"], "EUR")

    def test_plan_contains_german_translation_writes(self) -> None:
        spec = load_spec(SPEC_PATH)
        operations = build_cosmetic_plan(spec, self._resolved_fixture(spec))
        journal_translation = next(
            operation
            for operation in operations
            if isinstance(operation, WriteOperation)
            and operation.model == "account.journal"
            and operation.ids == (19,)
            and operation.context == {"lang": "de_DE"}
        )
        account_translation = next(
            operation
            for operation in operations
            if isinstance(operation, WriteOperation)
            and operation.model == "account.account"
            and operation.ids == (43,)
            and operation.context == {"lang": "de_DE"}
        )
        self.assertEqual(journal_translation.vals["name"], "Steuererklärungen")
        self.assertEqual(
            account_translation.vals["name"],
            "Forderungen aus Lieferungen und Leistungen Inland (Kassensystem)",
        )

    def test_plan_includes_account_codes_and_fiscal_position_ensures(self) -> None:
        spec = load_spec(SPEC_PATH)
        operations = build_cosmetic_plan(spec, self._resolved_fixture(spec))
        account_write = next(
            operation
            for operation in operations
            if isinstance(operation, WriteOperation)
            and operation.model == "account.account"
            and operation.ids == (26,)
            and operation.context is None
        )
        eu_position = next(
            operation
            for operation in operations
            if isinstance(operation, EnsureCreateOperation)
            and operation.model == "account.fiscal.position"
            and operation.lookup_domain
            == [["company_id", "=", 1], ["name", "=", "Europäische Union"]]
        )
        self.assertEqual(account_write.vals["code"], "4000")
        self.assertEqual(eu_position.create_vals["tax_ids"], [[6, 0, [3, 4]]])

    def test_builds_report_aware_extension(self) -> None:
        spec = load_spec(SPEC_PATH)
        operations = build_report_aware_plan(
            spec,
            self._resolved_fixture(spec),
            repartition_lines_by_tax=self._repartition_fixture(),
        )
        self.assertEqual(len(operations), 179)
        tax_group_country = next(
            operation
            for operation in operations
            if isinstance(operation, WriteOperation)
            and operation.model == "account.tax.group"
            and operation.ids == (1,)
            and operation.vals == {"country_id": 12}
        )
        line_2 = next(
            operation
            for operation in operations
            if isinstance(operation, WriteOperation)
            and operation.model == "account.tax.repartition.line"
            and operation.ids == (2,)
        )
        line_10 = next(
            operation
            for operation in operations
            if isinstance(operation, WriteOperation)
            and operation.model == "account.tax.repartition.line"
            and operation.ids == (10,)
        )
        self.assertEqual(tax_group_country.reason, "Align tax group 1 with Austrian report country")
        self.assertEqual(line_2.vals["account_id"], 21)
        self.assertEqual(line_2.vals["tag_ids"], [[6, 0, [1055]]])
        self.assertTrue(line_2.vals["use_in_tax_closing"])
        self.assertFalse(line_10.vals["account_id"])
        self.assertEqual(line_10.vals["tag_ids"], [[6, 0, []]])
        self.assertTrue(line_10.vals["use_in_tax_closing"])


if __name__ == "__main__":
    unittest.main()
