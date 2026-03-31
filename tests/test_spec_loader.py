from __future__ import annotations

import builtins
import importlib
import json
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from typing import Any
from unittest.mock import patch

import yaml

from odoo_demo_austria.models import ProjectSpec, SpecValidationError
from odoo_demo_austria.spec_loader import load_spec

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "data" / "austria-cosmetic-mapping-spec.draft.yaml"
_ORIGINAL_IMPORT = builtins.__import__


def _raise_on_yaml_import(
    name: str,
    globals_dict: dict[str, Any] | None = None,
    locals_dict: dict[str, Any] | None = None,
    fromlist: tuple[Any, ...] = (),
    level: int = 0,
) -> Any:
    if name == "yaml":
        raise ModuleNotFoundError("No module named 'yaml'")
    return _ORIGINAL_IMPORT(name, globals_dict, locals_dict, fromlist, level)


def _normalized_spec(spec: ProjectSpec) -> dict[str, Any]:
    payload = asdict(spec)
    payload["spec_path"] = "<normalized>"
    return payload


def _write_json_spec_copy() -> Path:
    raw_spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if raw_spec is None:
        raise AssertionError("Expected canonical YAML spec to parse to data")
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix="spec-loader-",
        dir=ROOT / "data",
        delete=False,
    ) as handle:
        json.dump(raw_spec, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        return Path(handle.name)


class SpecLoaderTests(unittest.TestCase):
    def test_loads_translation_aware_spec(self) -> None:
        spec = load_spec(SPEC_PATH)
        self.assertTrue(spec.reference_environment.same_database)
        self.assertEqual(spec.reference_environment.company_id, 3)
        self.assertEqual(spec.reference_environment.company_name, "AT Company")
        self.assertIsNone(spec.source_environment.company_name)
        self.assertEqual(spec.localization.primary_display_language, "de_DE")
        self.assertTrue(spec.localization.reference_snapshot_file.exists())
        self.assertEqual(spec.identity.bank.source_acc_number, "BANK134567890")
        self.assertEqual(len(spec.taxes), 4)
        self.assertEqual(len(spec.journals), 13)
        self.assertEqual(len(spec.fiscal_positions), 4)
        self.assertEqual(len(spec.chart.explicit_accounts), 64)

    def test_loads_german_tax_description_translation(self) -> None:
        spec = load_spec(SPEC_PATH)
        sale_tax = next(item for item in spec.taxes if item.record_id == 1)
        self.assertEqual(
            sale_tax.cosmetic.target_description.base_html, "<div>UST_022 Normal tax rate 20%</div>"
        )
        self.assertEqual(
            sale_tax.cosmetic.target_description.value_for("de_DE"),
            "UST_022 Normalsteuersatz 20%",
        )

    def test_loads_german_manual_overrides(self) -> None:
        spec = load_spec(SPEC_PATH)
        tax_returns = next(item for item in spec.journals if item.record_id == 19)
        pos_receivable = next(item for item in spec.chart.explicit_accounts if item.record_id == 43)
        self.assertEqual(tax_returns.target_name.value_for("de_DE"), "Steuererklärungen")
        self.assertEqual(
            pos_receivable.target_name.value_for("de_DE"),
            "Forderungen aus Lieferungen und Leistungen Inland (Kassensystem)",
        )

    def test_loads_austrian_account_codes_and_fiscal_positions(self) -> None:
        spec = load_spec(SPEC_PATH)
        sales = next(item for item in spec.chart.explicit_accounts if item.record_id == 26)
        revenue_10 = next(item for item in spec.chart.explicit_accounts if item.record_id == 51)
        eu_position = next(
            item for item in spec.fiscal_positions if item.target_name.base == "Europäische Union"
        )
        self.assertEqual(sales.code, "4000")
        self.assertEqual(revenue_10.code, "4010")
        self.assertTrue(revenue_10.create_if_missing)
        self.assertEqual(revenue_10.account_type, "income")
        self.assertTrue(eu_position.create_if_missing)
        self.assertEqual(eu_position.target_tax_ids, (3, 4))
        self.assertEqual(len(eu_position.account_mappings), 5)

    def test_yaml_and_json_load_to_equivalent_project_spec(self) -> None:
        json_spec_path = _write_json_spec_copy()
        try:
            yaml_spec = load_spec(SPEC_PATH)
            json_spec = load_spec(json_spec_path)
        finally:
            json_spec_path.unlink(missing_ok=True)

        self.assertEqual(_normalized_spec(yaml_spec), _normalized_spec(json_spec))

    def test_json_load_does_not_require_yaml_dependency(self) -> None:
        module_name = "odoo_demo_austria.spec_loader"
        json_spec_path = _write_json_spec_copy()
        try:
            sys.modules.pop(module_name, None)
            with patch("builtins.__import__", new=_raise_on_yaml_import):
                module = importlib.import_module(module_name)
                spec = module.load_spec(json_spec_path)
        finally:
            json_spec_path.unlink(missing_ok=True)
            sys.modules.pop(module_name, None)
            importlib.import_module(module_name)

        self.assertEqual(spec.localization.primary_display_language, "de_DE")
        self.assertEqual(spec.identity.bank.source_acc_number, "BANK134567890")

    def test_source_company_name_is_optional(self) -> None:
        raw_spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
        if raw_spec is None:
            raise AssertionError("Expected canonical YAML spec to parse to data")
        source_environment = raw_spec["source_environment"]
        source_environment["company_name"] = None
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            prefix="spec-loader-optional-company-name-",
            dir=ROOT / "data",
            delete=False,
        ) as handle:
            json.dump(raw_spec, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            spec_path = Path(handle.name)
        try:
            spec = load_spec(spec_path)
        finally:
            spec_path.unlink(missing_ok=True)

        self.assertIsNone(spec.source_environment.company_name)

    def test_yaml_load_without_pyyaml_dependency_fails_clearly(self) -> None:
        module_name = "odoo_demo_austria.spec_loader"
        try:
            sys.modules.pop(module_name, None)
            with patch("builtins.__import__", new=_raise_on_yaml_import):
                module = importlib.import_module(module_name)
                models_module = importlib.import_module("odoo_demo_austria.models")
                current_error_type = models_module.SpecValidationError
                with self.assertRaises(current_error_type) as context:
                    module.load_spec(SPEC_PATH)
        finally:
            sys.modules.pop(module_name, None)
            importlib.import_module(module_name)

        self.assertIn("PyYAML", str(context.exception))
        self.assertIn(".json", str(context.exception))

    def test_unsupported_spec_extension_fails_with_supported_extensions_hint(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".txt",
            prefix="spec-loader-",
            dir=ROOT / "data",
            delete=False,
        ) as handle:
            handle.write("{}\n")
            unsupported_path = Path(handle.name)
        try:
            with self.assertRaises(SpecValidationError) as context:
                load_spec(unsupported_path)
        finally:
            unsupported_path.unlink(missing_ok=True)

        message = str(context.exception)
        self.assertIn(".txt", message)
        self.assertIn(".json", message)
        self.assertIn(".yaml", message)


if __name__ == "__main__":
    unittest.main()
