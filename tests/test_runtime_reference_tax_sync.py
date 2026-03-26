from __future__ import annotations

import unittest
from typing import Any, cast

from odoo_demo_austria._runtime_reference_tax_sync import (
    sync_fiscal_position_taxes_from_reference,
)
from odoo_demo_austria.json2_client import Json2Client
from odoo_demo_austria.planner import (
    ReferenceAccountTarget,
    SyncFiscalPositionTaxesFromReferenceOperation,
)


class ReferenceTaxSyncTests(unittest.TestCase):
    def test_sync_fiscal_position_taxes_from_reference_creates_missing_rows(self) -> None:
        client = FakeReferenceSyncClient()
        operation = SyncFiscalPositionTaxesFromReferenceOperation(
            target_company_id=1,
            reference_company_id=3,
            reference_company_name="AT Company",
            display_language="de_DE",
            fiscal_position_names=("National", "Europäische Union"),
            reference_account_targets=(
                ReferenceAccountTarget(reference_account_id=183, target_code="3500"),
                ReferenceAccountTarget(reference_account_id=193, target_code="3530"),
            ),
            reason="Mirror fiscal-position taxes from the reference AT company",
        )

        sync_fiscal_position_taxes_from_reference(cast(Json2Client, client), operation)

        self.assertEqual(
            client.create_calls[0],
            (
                "account.account",
                {
                    "name": "Advance Tax Payment",
                    "account_type": "asset_current",
                    "reconcile": False,
                    "company_ids": [[6, 0, [1]]],
                    "code": "3532",
                },
                {
                    "company": 1,
                    "allowed_company_ids": [1],
                },
            ),
        )
        self.assertEqual(
            client.create_calls[1],
            (
                "account.tax.group",
                {
                    "name": "20%",
                    "sequence": 10,
                    "company_id": 1,
                    "tax_payable_account_id": 22,
                    "tax_receivable_account_id": 22,
                    "advance_tax_payment_account_id": 701,
                    "preceding_subtotal": False,
                    "pos_receipt_label": False,
                },
                None,
            ),
        )
        self.assertEqual(client.create_calls[2][0], "account.tax")
        self.assertEqual(client.create_calls[2][1]["name"], "0% Ust EU")
        self.assertEqual(client.create_calls[2][1]["company_id"], 1)
        self.assertEqual(client.create_calls[2][1]["tax_group_id"], 501)
        self.assertEqual(client.create_calls[2][1]["fiscal_position_ids"], [[6, 0, [102]]])
        self.assertEqual(client.create_calls[2][1]["original_tax_ids"], [[6, 0, []]])
        self.assertNotIn("country_id", client.create_calls[2][1])
        self.assertIn(
            (
                "account.tax",
                [301],
                {
                    "amount": 20.0,
                    "tax_scope": "consu",
                },
                None,
            ),
            client.write_calls,
        )
        self.assertIn(
            (
                "account.tax",
                [601],
                {
                    "name": "0% Ust EU",
                    "description": "UST_017 IGL 0% (ohne Art. 6 Abs. 1)",
                    "invoice_label": "0%",
                },
                {"lang": "de_DE"},
            ),
            client.write_calls,
        )
        self.assertIn(
            (
                "account.tax",
                [601],
                {
                    "fiscal_position_ids": [[6, 0, [102]]],
                    "original_tax_ids": [[6, 0, [301]]],
                },
                None,
            ),
            client.write_calls,
        )
        self.assertFalse(
            any(
                model == "account.tax"
                and ids == [301]
                and any(
                    field_name in vals
                    for field_name in ("repartition_line_ids", "tax_group_id", "country_id")
                )
                for model, ids, vals, _context in client.write_calls
            )
        )


class FakeReferenceSyncClient:
    def __init__(self) -> None:
        self.write_calls: list[tuple[str, list[int], dict[str, Any], dict[str, Any] | None]] = []
        self.create_calls: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = []
        self.read_calls: list[tuple[str, list[int], dict[str, Any] | None]] = []
        self.tax_creates = 0

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
        if model == "account.fiscal.position":
            return self._search_fiscal_positions(domain)
        if model == "account.tax":
            return self._search_taxes(domain)
        if model == "account.tax.group":
            return []
        if model == "account.account":
            return self._search_accounts(domain)
        raise AssertionError(f"Unexpected search_read model: {model}")

    def _search_fiscal_positions(self, domain: list[Any]) -> list[dict[str, Any]]:
        company_id = next(value for field, _operator, value in domain if field == "company_id")
        names = next(value for field, _operator, value in domain if field == "name")
        records = {
            1: [
                {"id": 101, "name": "National"},
                {"id": 102, "name": "Europäische Union"},
            ],
            3: [
                {"id": 201, "name": "National"},
                {"id": 202, "name": "Europäische Union"},
            ],
        }[company_id]
        if isinstance(names, str):
            return [record for record in records if record["name"] == names]
        return [record for record in records if record["name"] in names]

    def _search_taxes(self, domain: list[Any]) -> list[dict[str, Any]]:
        company_id = next(value for field, _operator, value in domain if field == "company_id")
        if company_id == 3:
            return [
                {
                    "id": 10,
                    "name": "20% Ust",
                    "type_tax_use": "sale",
                    "tax_group_id": [8, "20%"],
                    "fiscal_position_ids": [201],
                    "original_tax_ids": [],
                },
                {
                    "id": 11,
                    "name": "0% Ust EU",
                    "type_tax_use": "sale",
                    "tax_group_id": [8, "20%"],
                    "fiscal_position_ids": [202],
                    "original_tax_ids": [10],
                },
            ]
        tax_name = next(value for field, _operator, value in domain if field == "name")
        type_tax_use = next(value for field, _operator, value in domain if field == "type_tax_use")
        if tax_name == "20% Ust" and type_tax_use == "sale":
            return [{"id": 301}]
        return []

    def _search_accounts(self, domain: list[Any]) -> list[dict[str, Any]]:
        code = next(
            (value for field, _operator, value in domain if field == "code"),
            None,
        )
        if code is None:
            return []
        if code == "3500":
            return [{"id": 21, "account_type": "liability_payable"}]
        if code == "3530":
            return [{"id": 22, "account_type": "liability_payable"}]
        return []

    def read(
        self,
        model: str,
        ids: list[int],
        fields: list[str],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        del fields
        self.read_calls.append((model, ids, context))
        if model == "account.tax.group":
            return [{"id": 8, "name": "20%"}]
        if model == "account.account":
            company_ids = tuple((context or {}).get("allowed_company_ids", []))
            code_value = "3532" if company_ids == (3,) else False
            records = {
                183: {
                    "id": 183,
                    "name": "VAT 20%",
                    "account_type": "liability_payable",
                    "code": "3500" if company_ids == (3,) else False,
                },
                193: {
                    "id": 193,
                    "name": "Allocation account for tax authorities",
                    "account_type": "liability_payable",
                    "code": "3530" if company_ids == (3,) else False,
                },
                194: {
                    "id": 194,
                    "name": "Advance Tax Payment",
                    "account_type": "asset_current",
                    "code": code_value,
                },
            }
            return [records[item] for item in ids]
        if model == "account.tax":
            language = (context or {}).get("lang")
            return (
                [
                    {
                        "id": item,
                        "name": "20% Ust" if item == 10 else "0% Ust EU",
                    }
                    for item in ids
                ]
                if language
                else []
            )
        raise AssertionError(f"Unexpected read model: {model}")

    def call(self, model: str, method: str, payload: dict[str, Any]) -> Any:
        if model == "account.tax.group" and method == "copy_data":
            return [
                {
                    "name": "20%",
                    "sequence": 10,
                    "company_id": 3,
                    "tax_payable_account_id": 193,
                    "tax_receivable_account_id": 193,
                    "advance_tax_payment_account_id": 194,
                    "country_id": 12,
                    "preceding_subtotal": False,
                    "pos_receipt_label": False,
                }
            ]
        if model == "account.tax" and method == "copy_data":
            language = payload.get("context", {}).get("lang")
            records = {
                10: {
                    "name": "20% Ust (Kopie)",
                    "type_tax_use": "sale",
                    "tax_scope": "consu",
                    "amount_type": "percent",
                    "fiscal_position_ids": [[6, 0, [201]]],
                    "original_tax_ids": [[6, 0, []]],
                    "replacing_tax_ids": [[6, 0, [11]]],
                    "active": True,
                    "company_id": 3,
                    "children_tax_ids": [[6, 0, []]],
                    "sequence": 1,
                    "amount": 20.0,
                    "description": (
                        "UST_022 Normalsteuersatz 20%"
                        if language == "de_DE"
                        else "<div>UST_022 Normal tax rate 20%</div>"
                    ),
                    "invoice_label": "20%",
                    "price_include_override": False,
                    "include_base_amount": False,
                    "is_base_affected": True,
                    "analytic": False,
                    "tax_group_id": 8,
                    "tax_exigibility": "on_invoice",
                    "cash_basis_transition_account_id": False,
                    "repartition_line_ids": [
                        [
                            0,
                            0,
                            {
                                "factor_percent": 100.0,
                                "repartition_type": "tax",
                                "document_type": "invoice",
                                "account_id": 183,
                                "tag_ids": [[6, 0, []]],
                                "tax_id": 10,
                                "sequence": 1,
                                "use_in_tax_closing": True,
                            },
                        ]
                    ],
                    "country_id": 12,
                    "invoice_legal_notes": False,
                },
                11: {
                    "name": "0% Ust EU (Kopie)",
                    "type_tax_use": "sale",
                    "tax_scope": False,
                    "amount_type": "percent",
                    "fiscal_position_ids": [[6, 0, [202]]],
                    "original_tax_ids": [[6, 0, [10]]],
                    "replacing_tax_ids": [[6, 0, []]],
                    "active": True,
                    "company_id": 3,
                    "children_tax_ids": [[6, 0, []]],
                    "sequence": 2,
                    "amount": 0.0,
                    "description": (
                        "UST_017 IGL 0% (ohne Art. 6 Abs. 1)"
                        if language == "de_DE"
                        else "<div>UST_017 IGL 0% (without art. 6 par. 1)</div>"
                    ),
                    "invoice_label": "0%",
                    "price_include_override": False,
                    "include_base_amount": False,
                    "is_base_affected": True,
                    "analytic": False,
                    "tax_group_id": 8,
                    "tax_exigibility": "on_invoice",
                    "cash_basis_transition_account_id": False,
                    "repartition_line_ids": [
                        [
                            0,
                            0,
                            {
                                "factor_percent": 100.0,
                                "repartition_type": "tax",
                                "document_type": "invoice",
                                "account_id": False,
                                "tag_ids": [[6, 0, []]],
                                "tax_id": 11,
                                "sequence": 1,
                                "use_in_tax_closing": False,
                            },
                        ]
                    ],
                    "country_id": 12,
                    "invoice_legal_notes": False,
                },
            }
            return [records[item] for item in payload["ids"]]
        raise AssertionError(f"Unexpected call: {model}.{method}")

    def write(
        self,
        model: str,
        ids: list[int],
        vals: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> bool:
        self.write_calls.append((model, ids, vals, context))
        return True

    def create(
        self,
        model: str,
        vals: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> int:
        self.create_calls.append((model, vals, context))
        if model == "account.account":
            return 701
        if model == "account.tax.group":
            return 501
        if model == "account.tax":
            self.tax_creates += 1
            return 600 + self.tax_creates
        raise AssertionError(f"Unexpected create model: {model}")
