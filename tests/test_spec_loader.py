from __future__ import annotations

import unittest
from pathlib import Path

from odoo_demo_austria.spec_loader import load_spec

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "data" / "austria-cosmetic-mapping-spec.draft.yaml"


class SpecLoaderTests(unittest.TestCase):
    def test_loads_translation_aware_spec(self) -> None:
        spec = load_spec(SPEC_PATH)
        self.assertEqual(spec.localization.primary_display_language, "de_DE")
        self.assertTrue(spec.localization.reference_snapshot_file.exists())
        self.assertEqual(len(spec.taxes), 4)
        self.assertEqual(len(spec.journals), 13)
        self.assertEqual(len(spec.fiscal_positions), 4)
        self.assertEqual(len(spec.chart.explicit_accounts), 53)

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
        eu_position = next(
            item for item in spec.fiscal_positions if item.target_name.base == "Europäische Union"
        )
        self.assertEqual(sales.code, "4000")
        self.assertTrue(eu_position.create_if_missing)
        self.assertEqual(eu_position.target_tax_ids, (3, 4))


if __name__ == "__main__":
    unittest.main()
