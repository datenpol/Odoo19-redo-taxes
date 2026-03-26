from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReferenceAccount:
    record_id: int
    name: str
    account_type: str
    code: str | None


@dataclass(frozen=True)
class ReferenceTaxGroup:
    record_id: int
    name: str
    copy_vals: dict[str, Any]


@dataclass(frozen=True)
class ReferenceTax:
    record_id: int
    name: str
    type_tax_use: str
    tax_group_id: int
    fiscal_position_names: tuple[str, ...]
    original_tax_ids: tuple[int, ...]
    base_copy_vals: dict[str, Any]
    translated_copy_vals: dict[str, Any]
