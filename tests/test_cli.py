from __future__ import annotations

import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from odoo_demo_austria import cli
from odoo_demo_austria._validator_support import ValidationIssue
from odoo_demo_austria.json2_client import Json2ClientError

ROOT = Path(__file__).resolve().parents[1]
WRAPPER_PATH = ROOT / "tools" / "odoo_demo_austria.py"


class FakeClient:
    base_url = "https://example.odoo.test"


class CliTests(unittest.TestCase):
    def test_wrapper_help_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, str(WRAPPER_PATH), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("{apply,validate,run}", result.stdout)

    def test_run_json_success_contract(self) -> None:
        with (
            patch("odoo_demo_austria.cli.load_spec", return_value=object()),
            patch("odoo_demo_austria.cli._build_client", return_value=FakeClient()),
            patch(
                "odoo_demo_austria._cli_runtime._build_operations",
                return_value=[object(), object()],
            ),
            patch("odoo_demo_austria._cli_runtime._apply_operations", return_value=2),
            patch("odoo_demo_austria._cli_runtime.validate_cosmetic_state", return_value=[]),
        ):
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = cli.main(
                    ["run", "--format", "json", "--base-url", "https://example.odoo.test"]
                )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["command"], "run")
        self.assertEqual(payload["mode"], "cosmetic")
        self.assertEqual(payload["base_url"], "https://example.odoo.test")
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["preflight"]["status"], "success")
        self.assertEqual(payload["preflight"]["operation_count"], 2)
        self.assertEqual(payload["apply"]["status"], "success")
        self.assertEqual(payload["apply"]["operation_count"], 2)
        self.assertEqual(payload["validation"]["status"], "success")
        self.assertEqual(payload["validation"]["issue_count"], 0)

    def test_validate_json_failure_uses_exit_code_6(self) -> None:
        issues = [ValidationIssue(scope="account.tax[1]", message="name mismatch")]
        with (
            patch("odoo_demo_austria.cli.load_spec", return_value=object()),
            patch("odoo_demo_austria.cli._build_client", return_value=FakeClient()),
            patch("odoo_demo_austria._cli_runtime.validate_cosmetic_state", return_value=issues),
        ):
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = cli.main(
                    ["validate", "--format", "json", "--base-url", "https://example.odoo.test"]
                )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 6)
        self.assertEqual(payload["status"], "failure")
        self.assertEqual(payload["exit_code"], 6)
        self.assertEqual(payload["validation"]["status"], "failure")
        self.assertEqual(payload["validation"]["issue_count"], 1)
        self.assertEqual(
            payload["validation"]["messages"],
            ["account.tax[1]: name mismatch"],
        )

    def test_run_preflight_api_failure_uses_exit_code_3(self) -> None:
        with (
            patch("odoo_demo_austria.cli.load_spec", return_value=object()),
            patch("odoo_demo_austria.cli._build_client", return_value=FakeClient()),
            patch(
                "odoo_demo_austria._cli_runtime._build_operations",
                side_effect=Json2ClientError("HTTP 401 calling res.company.read: Invalid apikey"),
            ),
        ):
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = cli.main(
                    ["run", "--format", "json", "--base-url", "https://example.odoo.test"]
                )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 3)
        self.assertEqual(payload["status"], "failure")
        self.assertEqual(payload["exit_code"], 3)
        self.assertEqual(payload["preflight"]["status"], "failure")
        self.assertEqual(payload["apply"]["status"], "skipped")
        self.assertEqual(payload["validation"]["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
