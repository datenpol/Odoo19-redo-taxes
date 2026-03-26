from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    scope: str
    message: str


def single(records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) != 1:
        raise ValueError(f"Expected a single record, got {len(records)}")
    return records[0]


def index_by_id(records: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(record["id"]): record for record in records}


def many2one_id(value: Any) -> int | None:
    if not value:
        return None
    if isinstance(value, list) and value:
        return int(value[0])
    return int(value)


def normalize_rich_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = re.sub(r"<[^>]+>", "", value).strip()
    return html.unescape(stripped)


def expect_equal(
    issues: list[ValidationIssue],
    scope: str,
    field_name: str,
    actual: Any,
    expected: Any,
) -> None:
    if expected == "" and actual in (None, False):
        actual = ""
    if expected is None and actual is False:
        actual = None
    if actual != expected:
        issues.append(
            ValidationIssue(
                scope=scope,
                message=f"{field_name} mismatch: expected {expected!r}, got {actual!r}",
            )
        )
