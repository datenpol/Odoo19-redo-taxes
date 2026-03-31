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
    def __init__(
        self,
        spec: Any,
        *,
        use_target_names: bool,
        use_umlaut_source_names: bool = False,
        use_translated_target_names: bool = False,
        append_copy_suffix_to_tax_names: bool = False,
        company_name_override: str | None = None,
    ) -> None:
        self.spec = spec
        self.use_target_names = use_target_names
        self.use_umlaut_source_names = use_umlaut_source_names
        self.use_translated_target_names = use_translated_target_names
        self.append_copy_suffix_to_tax_names = append_copy_suffix_to_tax_names
        self.company_name_override = company_name_override

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
        if model == "res.company":
            return [self._company_record()]
        if model != "account.tax.group":
            raise AssertionError(f"Unexpected read model: {model}")
        return [self._tax_group_record(group_id) for group_id in ids]

    def _company_record(self) -> dict[str, Any]:
        company_name = self.company_name_override
        if company_name is None:
            company_name = self._name(
                self.spec.source_environment.company_name,
                self.spec.identity.company.target_company_name,
            )
        return {
            "id": self.spec.source_environment.company_id,
            "name": company_name,
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
        target_name = (
            spec.cosmetic.target_name.value_for("de_DE")
            if self.use_translated_target_names
            else spec.cosmetic.target_name.base
        )
        name = self._name(spec.source_name, target_name)
        if self.append_copy_suffix_to_tax_names:
            name = f"{name} (Kopie)"
        return {
            "id": spec.record_id,
            "name": name,
            "tax_group_id": [self._resolved_tax_group_id(spec.cosmetic.target_group_id), "group"],
        }

    def _journal_record(self, domain: list[Any]) -> dict[str, Any]:
        spec = self._match_by_name(self.spec.journals, self._domain_value(domain, "name"))
        target_name = (
            spec.target_name.value_for("de_DE")
            if self.use_translated_target_names
            else spec.target_name.base
        )
        return {
            "id": spec.record_id + 1_000,
            "name": self._name(spec.source_name, target_name),
        }

    def _fiscal_position_records(self, domain: list[Any]) -> list[dict[str, Any]]:
        spec = self._match_by_name(self.spec.fiscal_positions, self._domain_value(domain, "name"))
        if spec is None or spec.create_if_missing:
            return []
        target_name = (
            spec.target_name.value_for("de_DE")
            if self.use_translated_target_names
            else spec.target_name.base
        )
        name = self._name(spec.source_name, target_name)
        return [{"id": spec.record_id + 2_000, "name": name}]

    def _account_records(self, domain: list[Any]) -> list[dict[str, Any]]:
        code = self._optional_domain_value(domain, "code")
        if code is not None:
            matches = [
                item for item in self.spec.chart.explicit_accounts if item.code == code
            ]
        else:
            names = self._domain_value(domain, "name")
            matches = [
                item
                for item in self.spec.chart.explicit_accounts
                if item.source_name in names
                or item.target_name.base in names
                or item.target_name.value_for("de_DE") in names
            ]
        if not self.use_target_names:
            matches = [item for item in matches if not item.create_if_missing]
        return [
            {
                "id": item.record_id + 3_000,
                "name": self._name(
                    item.source_name,
                    item.target_name.value_for("de_DE")
                    if self.use_translated_target_names
                    else item.target_name.base,
                ),
                "code": item.code,
            }
            for item in matches
        ]

    def _tax_group_record(self, group_id: int) -> dict[str, Any]:
        group_ref = group_id - 5_000
        spec = next(item for item in self.spec.tax_groups if item.record_id == group_ref)
        target_name = (
            spec.cosmetic.target_name.value_for("de_DE")
            if self.use_translated_target_names
            else spec.cosmetic.target_name.base
        )
        return {
            "id": group_id,
            "name": self._name(spec.source_name, target_name),
        }

    def _single_tax_spec(self, domain: list[Any]) -> Any:
        record_id = self._optional_domain_value(domain, "id")
        if record_id is not None:
            return next(item for item in self.spec.taxes if item.record_id == record_id)
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

    def _optional_domain_value(self, domain: list[Any], field_name: str) -> Any | None:
        for field, _operator, value in domain:
            if field == field_name:
                return value
        return None

    def _name(self, source_name: str | None, target_name: str) -> str:
        if self.use_target_names or source_name is None:
            return target_name
        if self.use_umlaut_source_names:
            return (
                source_name.replace("ae", "ä")
                .replace("oe", "ö")
                .replace("ue", "ü")
                .replace("Ae", "Ä")
                .replace("Oe", "Ö")
                .replace("Ue", "Ü")
            )
        return source_name


class ResolverTests(unittest.TestCase):
    def test_resolves_source_state_without_fixed_ids(self) -> None:
        spec = load_spec(SPEC_PATH)
        client = cast(Json2Client, FakeResolverClient(spec, use_target_names=False))
        resolved = resolve_cosmetic_targets(client, spec)

        self.assertEqual(resolved.company_id, 1)
        self.assertEqual(resolved.company_partner_id, 11)
        self.assertEqual(resolved.bank.record_id, 2)
        self.assertEqual(resolved.taxes[0].record_id, 1)
        self.assertEqual(resolved.tax_groups[0].record_id, 5_001)
        self.assertEqual(resolved.journals[0].record_id, 1_001)
        self.assertEqual(resolved.accounts[0].record_id, 3_001)
        revenue_10 = next(item for item in resolved.accounts if item.spec.code == "4010")
        self.assertIsNone(revenue_10.record_id)
        self.assertIsNone(resolved.fiscal_positions[2].record_id)

    def test_resolves_target_state_after_cosmetic_rename(self) -> None:
        spec = load_spec(SPEC_PATH)
        client = cast(Json2Client, FakeResolverClient(spec, use_target_names=True))
        resolved = resolve_cosmetic_targets(client, spec)

        self.assertEqual(resolved.active_company_currency.record_id, 1)
        self.assertEqual(resolved.displaced_reference_currency.record_id, 126)
        self.assertEqual(resolved.taxes[1].record_id, 2)
        self.assertEqual(resolved.journals[-1].record_id, 1_021)
        purchased_0 = next(item for item in resolved.accounts if item.spec.code == "5200")
        self.assertEqual(purchased_0.record_id, 3_061)
        self.assertIsNone(resolved.fiscal_positions[3].record_id)

    def test_resolves_translated_target_state_after_cosmetic_rename(self) -> None:
        spec = load_spec(SPEC_PATH)
        client = cast(
            Json2Client,
            FakeResolverClient(
                spec,
                use_target_names=True,
                use_translated_target_names=True,
            ),
        )
        resolved = resolve_cosmetic_targets(client, spec)

        self.assertEqual(resolved.taxes[1].record_id, 2)
        self.assertEqual(resolved.journals[-1].record_id, 1_021)
        revenue_10 = next(item for item in resolved.accounts if item.spec.code == "4010")
        self.assertEqual(revenue_10.record_id, 3_051)

    def test_resolves_taxes_by_stable_id_after_copy_suffix_rename(self) -> None:
        spec = load_spec(SPEC_PATH)
        client = cast(
            Json2Client,
            FakeResolverClient(
                spec,
                use_target_names=True,
                append_copy_suffix_to_tax_names=True,
            ),
        )

        resolved = resolve_cosmetic_targets(client, spec)

        self.assertEqual(resolved.taxes[0].record_id, 1)
        self.assertEqual(resolved.taxes[1].record_id, 2)

    def test_resolves_ascii_spec_names_against_umlaut_source_records(self) -> None:
        spec = load_spec(SPEC_PATH)
        client = cast(
            Json2Client,
            FakeResolverClient(spec, use_target_names=False, use_umlaut_source_names=True),
        )
        resolved = resolve_cosmetic_targets(client, spec)

        by_source_name = {item.spec.source_name: item.record_id for item in resolved.journals}
        self.assertEqual(by_source_name["Bargeld (Kleidergeschaeft)"], 1_017)
        self.assertEqual(by_source_name["Bargeld (Baeckerei)"], 1_018)

    def test_resolves_source_company_by_id_even_when_name_changed(self) -> None:
        spec = load_spec(SPEC_PATH)
        client = cast(
            Json2Client,
            FakeResolverClient(
                spec,
                use_target_names=False,
                company_name_override="Demofirma Vertrieb West",
            ),
        )

        resolved = resolve_cosmetic_targets(client, spec)

        self.assertEqual(resolved.company_id, spec.source_environment.company_id)


if __name__ == "__main__":
    unittest.main()
