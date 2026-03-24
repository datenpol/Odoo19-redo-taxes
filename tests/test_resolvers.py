from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any, cast

from odoo_demo_austria.json2_client import Json2Client
from odoo_demo_austria.planner import resolve_cosmetic_targets
from odoo_demo_austria.spec_loader import load_spec

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "data" / "austria-cosmetic-mapping-spec.draft.yaml"


class FakeResolverClient:
    def __init__(self, spec: Any, *, use_target_names: bool) -> None:
        self.spec = spec
        self.use_target_names = use_target_names

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
            return [self._company_record()]
        if model == "res.currency":
            return [
                {"id": 1, "name": self._currency_name(active=True)},
                {"id": 126, "name": self._currency_name(active=False)},
            ]
        if model == "res.partner.bank":
            return [
                {
                    "id": 2,
                    "acc_number": self._bank_acc_number(),
                    "lock_trust_fields": False,
                }
            ]
        if model == "account.tax":
            return [self._tax_record(domain)]
        if model == "account.journal":
            return [self._journal_record(domain)]
        if model == "account.fiscal.position":
            return self._fiscal_position_records(domain)
        if model == "account.account":
            return self._account_records(domain)
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
        if model != "account.tax.group":
            raise AssertionError(f"Unexpected read model: {model}")
        return [self._tax_group_record(group_id) for group_id in ids]

    def _company_record(self) -> dict[str, Any]:
        return {
            "id": self.spec.source_environment.company_id,
            "name": self._name(
                self.spec.source_environment.company_name,
                self.spec.identity.company.target_company_name,
            ),
            "partner_id": [11, "Datenpol Wohnatelier GmbH"],
            "currency_id": [1, self._currency_name(active=True)],
        }

    def _currency_name(self, *, active: bool) -> str:
        record = (
            self.spec.currency.active_company_currency
            if active
            else self.spec.currency.displaced_reference_currency
        )
        if self.use_target_names:
            return record.target_code
        return record.source_code

    def _bank_acc_number(self) -> str:
        if self.use_target_names:
            return self.spec.identity.bank.acc_number
        return self.spec.identity.bank.source_acc_number

    def _tax_record(self, domain: list[Any]) -> dict[str, Any]:
        spec = self._single_tax_spec(domain)
        return {
            "id": spec.record_id + 100,
            "name": self._name(spec.source_name, spec.cosmetic.target_name.base),
            "tax_group_id": [self._resolved_tax_group_id(spec.cosmetic.target_group_id), "group"],
        }

    def _journal_record(self, domain: list[Any]) -> dict[str, Any]:
        spec = self._match_by_name(self.spec.journals, self._domain_value(domain, "name"))
        return {
            "id": spec.record_id + 1_000,
            "name": self._name(spec.source_name, spec.target_name.base),
        }

    def _fiscal_position_records(self, domain: list[Any]) -> list[dict[str, Any]]:
        spec = self._match_by_name(self.spec.fiscal_positions, self._domain_value(domain, "name"))
        if spec is None or spec.create_if_missing:
            return []
        name = self._name(spec.source_name, spec.target_name.base)
        return [{"id": spec.record_id + 2_000, "name": name}]

    def _account_records(self, domain: list[Any]) -> list[dict[str, Any]]:
        names = self._domain_value(domain, "name")
        matches = [
            item
            for item in self.spec.chart.explicit_accounts
            if item.source_name in names or item.target_name.base in names
        ]
        return [
            {
                "id": item.record_id + 3_000,
                "name": self._name(item.source_name, item.target_name.base),
                "code": item.code,
            }
            for item in matches
        ]

    def _tax_group_record(self, group_id: int) -> dict[str, Any]:
        group_ref = group_id - 5_000
        spec = next(item for item in self.spec.tax_groups if item.record_id == group_ref)
        return {
            "id": group_id,
            "name": self._name(spec.source_name, spec.cosmetic.target_name.base),
        }

    def _single_tax_spec(self, domain: list[Any]) -> Any:
        names = self._domain_value(domain, "name")
        type_tax_use = self._domain_value(domain, "type_tax_use")
        matches = [
            item
            for item in self.spec.taxes
            if item.source_type_tax_use == type_tax_use
            and (item.source_name in names or item.cosmetic.target_name.base in names)
        ]
        assert len(matches) == 1
        return matches[0]

    def _resolved_tax_group_id(self, group_ref: int) -> int:
        return group_ref + 5_000

    def _match_by_name(self, specs: Any, names: list[str]) -> Any:
        matches = [
            item
            for item in specs
            if item.source_name in names or item.target_name.base in names
        ]
        if not matches:
            return None
        assert len(matches) == 1
        return matches[0]

    def _domain_value(self, domain: list[Any], field_name: str) -> Any:
        for field, _operator, value in domain:
            if field == field_name:
                return value
        raise AssertionError(f"Missing domain field {field_name}")

    def _name(self, source_name: str | None, target_name: str) -> str:
        if self.use_target_names or source_name is None:
            return target_name
        return source_name


class ResolverTests(unittest.TestCase):
    def test_resolves_source_state_without_fixed_ids(self) -> None:
        spec = load_spec(SPEC_PATH)
        client = cast(Json2Client, FakeResolverClient(spec, use_target_names=False))
        resolved = resolve_cosmetic_targets(client, spec)

        self.assertEqual(resolved.company_id, 1)
        self.assertEqual(resolved.company_partner_id, 11)
        self.assertEqual(resolved.bank.record_id, 2)
        self.assertEqual(resolved.taxes[0].record_id, 101)
        self.assertEqual(resolved.tax_groups[0].record_id, 5_001)
        self.assertEqual(resolved.journals[0].record_id, 1_001)
        self.assertEqual(resolved.accounts[0].record_id, 3_001)
        self.assertIsNone(resolved.fiscal_positions[2].record_id)

    def test_resolves_target_state_after_cosmetic_rename(self) -> None:
        spec = load_spec(SPEC_PATH)
        client = cast(Json2Client, FakeResolverClient(spec, use_target_names=True))
        resolved = resolve_cosmetic_targets(client, spec)

        self.assertEqual(resolved.active_company_currency.record_id, 1)
        self.assertEqual(resolved.displaced_reference_currency.record_id, 126)
        self.assertEqual(resolved.taxes[1].record_id, 102)
        self.assertEqual(resolved.journals[-1].record_id, 1_021)
        self.assertEqual(resolved.accounts[-1].record_id, 3_050)
        self.assertIsNone(resolved.fiscal_positions[3].record_id)


if __name__ == "__main__":
    unittest.main()
