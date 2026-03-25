from __future__ import annotations

import unittest
from typing import Any, cast

from odoo_demo_austria._runtime_apply import (
    apply_ensure_create,
    apply_replace_fiscal_position_accounts,
)
from odoo_demo_austria.json2_client import Json2Client
from odoo_demo_austria.planner import (
    EnsureCreateOperation,
    FiscalPositionAccountMappingLine,
    ReplaceFiscalPositionAccountsOperation,
)


class FakeApplyClient:
    def __init__(self) -> None:
        self.write_calls: list[tuple[str, list[int], dict[str, Any], dict[str, Any] | None]] = []
        self.create_calls: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = []

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
        if model == "account.account":
            code = next(value for field, _operator, value in domain if field == "code")
            return [{"id": {"4000": 26, "4100": 54, "4010": 51}.get(code, 0)}] if code else []
        if model == "account.fiscal.position":
            return [{"id": 7}]
        raise AssertionError(f"Unexpected search_read model: {model}")

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
        return 999


class RuntimeApplyTests(unittest.TestCase):
    def test_apply_ensure_create_updates_existing_account_with_write_allowlist(self) -> None:
        client = FakeApplyClient()
        operation = EnsureCreateOperation(
            model="account.account",
            lookup_domain=[["company_ids", "in", [1]], ["code", "=", "4010"]],
            create_vals={
                "name": "Revenue 10%",
                "code": "4010",
                "account_type": "income",
                "reconcile": False,
                "company_ids": [[6, 0, [1]]],
            },
            reason="Ensure account 4010 exists cosmetically",
        )

        resolved_id = apply_ensure_create(cast(Json2Client, client), operation)

        self.assertEqual(resolved_id, 51)
        self.assertEqual(
            client.write_calls,
            [
                (
                    "account.account",
                    [51],
                    {
                        "name": "Revenue 10%",
                        "code": "4010",
                        "account_type": "income",
                        "reconcile": False,
                    },
                    None,
                )
            ],
        )
        self.assertEqual(client.create_calls, [])

    def test_apply_replace_fiscal_position_accounts_rewrites_account_ids_by_code(self) -> None:
        client = FakeApplyClient()
        operation = ReplaceFiscalPositionAccountsOperation(
            company_id=1,
            fiscal_position_id=None,
            fiscal_position_name="Europäische Union",
            mappings=(
                FiscalPositionAccountMappingLine(
                    source_account_code="4000",
                    replacement_account_code="4100",
                ),
                FiscalPositionAccountMappingLine(
                    source_account_code="4010",
                    replacement_account_code="4100",
                ),
            ),
            reason="Align fiscal position account mappings for Europäische Union",
        )

        apply_replace_fiscal_position_accounts(cast(Json2Client, client), operation)

        self.assertEqual(
            client.write_calls[-1],
            (
                "account.fiscal.position",
                [7],
                {
                    "account_ids": [
                        [5, 0, 0],
                        [0, 0, {"account_src_id": 26, "account_dest_id": 54}],
                        [0, 0, {"account_src_id": 51, "account_dest_id": 54}],
                    ]
                },
                None,
            ),
        )


if __name__ == "__main__":
    unittest.main()
