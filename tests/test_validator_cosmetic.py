from __future__ import annotations

import unittest
from typing import cast

from odoo_demo_austria._validator_cosmetic import validate_journals
from odoo_demo_austria._validator_support import ValidationIssue
from odoo_demo_austria.json2_client import Json2Client
from odoo_demo_austria.models import JournalSpec, ResolvedJournal, TranslatedText


class FailIfCalledJournalClient:
    def read(
        self,
        model: str,
        ids: list[int],
        fields: list[str],
        *,
        context: dict[str, str] | None = None,
    ) -> list[dict[str, str]]:
        del model, ids, fields, context
        raise AssertionError("validate_journals should skip optional journals without ids")


class ValidatorJournalTests(unittest.TestCase):
    def test_validate_journals_skips_missing_optional_journal(self) -> None:
        issues: list[ValidationIssue] = []
        journal = ResolvedJournal(
            spec=JournalSpec(
                record_id=15,
                source_name="Kassensystem",
                target_name=TranslatedText(
                    base="Kassensystem",
                    translations={"de_DE": "Kassensystem"},
                ),
                optional=True,
            ),
            record_id=None,
        )

        validate_journals(
            cast(Json2Client, FailIfCalledJournalClient()),
            (journal,),
            "de_DE",
            issues,
        )

        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
