from __future__ import annotations

from typing import Any

from ._planner_builders import _ensure_operations_safe, build_cosmetic_plan
from ._planner_types import PlanOperation, RepartitionLineRef, WriteOperation
from .json2_client import Json2ClientError
from .models import ProjectSpec, ResolvedProject, ResolvedTax, ResolvedTaxGroup


def build_report_aware_plan(
    spec: ProjectSpec,
    resolved: ResolvedProject,
    *,
    repartition_lines_by_tax: dict[int, tuple[RepartitionLineRef, ...]],
) -> list[PlanOperation]:
    operations = build_cosmetic_plan(spec, resolved)
    operations.extend(_build_report_aware_operations(resolved, repartition_lines_by_tax))
    _ensure_operations_safe(operations)
    return operations


def _build_report_aware_operations(
    resolved: ResolvedProject,
    repartition_lines_by_tax: dict[int, tuple[RepartitionLineRef, ...]],
) -> list[WriteOperation]:
    operations = _build_report_aware_tax_group_operations(resolved.tax_groups)
    operations.extend(_build_report_aware_tax_operations(resolved.taxes, repartition_lines_by_tax))
    return operations


def _build_report_aware_tax_group_operations(
    tax_groups: tuple[ResolvedTaxGroup, ...],
) -> list[WriteOperation]:
    return [
        WriteOperation(
            model="account.tax.group",
            ids=(tax_group.record_id,),
            vals={"country_id": tax_group.spec.report_aware.target_country_id},
            reason=f"Align tax group {tax_group.record_id} with Austrian report country",
        )
        for tax_group in tax_groups
    ]


def _build_report_aware_tax_operations(
    taxes: tuple[ResolvedTax, ...],
    repartition_lines_by_tax: dict[int, tuple[RepartitionLineRef, ...]],
) -> list[WriteOperation]:
    operations: list[WriteOperation] = []
    for tax in taxes:
        operations.append(
            WriteOperation(
                model="account.tax",
                ids=(tax.record_id,),
                vals={"country_id": tax.spec.report_aware.target_country_id},
                reason=f"Align tax {tax.record_id} with Austrian report country",
            )
        )
        operations.extend(_build_repartition_line_operations(tax, repartition_lines_by_tax))
    return operations


def _build_repartition_line_operations(
    tax: ResolvedTax,
    repartition_lines_by_tax: dict[int, tuple[RepartitionLineRef, ...]],
) -> list[WriteOperation]:
    lines = repartition_lines_by_tax.get(tax.record_id)
    if not lines:
        raise Json2ClientError(f"Missing repartition lines for tax {tax.record_id}")
    return [
        WriteOperation(
            model="account.tax.repartition.line",
            ids=(line.record_id,),
            vals=_report_aware_line_values(tax, line),
            reason=f"Align repartition line {line.record_id} for tax {tax.record_id}",
        )
        for line in lines
    ]


def _report_aware_line_values(
    tax: ResolvedTax,
    line: RepartitionLineRef,
) -> dict[str, Any]:
    if line.repartition_type == "base":
        return {
            "account_id": False,
            "tag_ids": [[6, 0, list(tax.spec.report_aware.reference_invoice_tags)]],
            "use_in_tax_closing": False,
        }
    if line.repartition_type != "tax":
        raise Json2ClientError(
            f"Unexpected repartition_type {line.repartition_type!r} on line {line.record_id}"
        )
    return {
        "account_id": tax.spec.report_aware.target_tax_account_id or False,
        "tag_ids": [[6, 0, list(tax.spec.report_aware.reference_tax_tags)]],
        "use_in_tax_closing": True,
    }
