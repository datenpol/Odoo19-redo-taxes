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
    ReplaceFiscalPositionAccountsOperation,
    WriteOperation,
    build_cosmetic_plan,
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
                ResolvedAccount(
                    spec=item,
                    record_id=None if item.create_if_missing else item.record_id,
                )
                for item in project.chart.explicit_accounts
            ),
        )

    def test_builds_full_cosmetic_plan(self) -> None:
        spec = load_spec(SPEC_PATH)
        operations = build_cosmetic_plan(spec, self._resolved_fixture(spec))
        first_operation = operations[0]
        assert isinstance(first_operation, WriteOperation)
        self.assertEqual(len(operations), 172)
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
        revenue_10_create = next(
            operation
            for operation in operations
            if isinstance(operation, EnsureCreateOperation)
            and operation.model == "account.account"
            and operation.lookup_domain == [["company_ids", "in", [1]], ["code", "=", "4010"]]
        )
        eu_mappings = next(
            operation
            for operation in operations
            if isinstance(operation, ReplaceFiscalPositionAccountsOperation)
            and operation.fiscal_position_name == "Europäische Union"
        )
        self.assertEqual(account_write.vals["code"], "4000")
        self.assertEqual(eu_position.create_vals["tax_ids"], [[6, 0, [3, 4]]])
        self.assertEqual(revenue_10_create.create_vals["account_type"], "income")
        self.assertEqual(
            [item.to_dict() for item in eu_mappings.mappings],
            [
                {
                    "source_account_code": "4000",
                    "replacement_account_code": "4100",
                },
                {
                    "source_account_code": "4010",
                    "replacement_account_code": "4110",
                },
                {
                    "source_account_code": "2000",
                    "replacement_account_code": "2010",
                },
                {
                    "source_account_code": "5010",
                    "replacement_account_code": "5110",
                },
                {
                    "source_account_code": "5020",
                    "replacement_account_code": "5120",
                },
            ],
        )

    def test_plan_skips_optional_journal_without_record_id(self) -> None:
        spec = load_spec(SPEC_PATH)
        resolved = self._resolved_fixture(spec)
        journals = tuple(
            ResolvedJournal(
                spec=item.spec,
                record_id=None if item.spec.source_name == "Kassensystem" else item.record_id,
            )
            for item in resolved.journals
        )

        operations = build_cosmetic_plan(
            spec,
            ResolvedProject(
                company_id=resolved.company_id,
                company_partner_id=resolved.company_partner_id,
                bank=resolved.bank,
                active_company_currency=resolved.active_company_currency,
                displaced_reference_currency=resolved.displaced_reference_currency,
                tax_groups=resolved.tax_groups,
                taxes=resolved.taxes,
                journals=journals,
                fiscal_positions=resolved.fiscal_positions,
                accounts=resolved.accounts,
            ),
        )

        self.assertFalse(
            any(
                isinstance(operation, WriteOperation)
                and operation.model == "account.journal"
                and operation.ids == (15,)
                for operation in operations
            )
        )

    def test_plan_skips_optional_account_without_record_id(self) -> None:
        spec = load_spec(SPEC_PATH)
        resolved = self._resolved_fixture(spec)
        accounts = tuple(
            ResolvedAccount(
                spec=item.spec,
                record_id=None if item.spec.code == "2700" else item.record_id,
            )
            for item in resolved.accounts
        )

        operations = build_cosmetic_plan(
            spec,
            ResolvedProject(
                company_id=resolved.company_id,
                company_partner_id=resolved.company_partner_id,
                bank=resolved.bank,
                active_company_currency=resolved.active_company_currency,
                displaced_reference_currency=resolved.displaced_reference_currency,
                tax_groups=resolved.tax_groups,
                taxes=resolved.taxes,
                journals=resolved.journals,
                fiscal_positions=resolved.fiscal_positions,
                accounts=accounts,
            ),
        )

        self.assertFalse(
            any(
                isinstance(operation, WriteOperation)
                and operation.model == "account.account"
                and operation.ids == (291,)
                for operation in operations
            )
        )


if __name__ == "__main__":
    unittest.main()
