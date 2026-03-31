from __future__ import annotations

from ._planner_types import ReferenceAccountTarget, SyncFiscalPositionTaxesFromReferenceOperation
from .json2_client import Json2Client, Json2ClientError
from .models import ProjectSpec, ResolvedProject


def build_reference_tax_sync_operation(
    client: Json2Client,
    spec: ProjectSpec,
    resolved: ResolvedProject,
) -> SyncFiscalPositionTaxesFromReferenceOperation | None:
    reference = spec.reference_environment
    if not reference.same_database:
        return None

    reference_company_id = reference.company_id
    reference_company_name = _read_reference_company_name(client, spec)
    fiscal_position_names = tuple(item.spec.target_name.base for item in resolved.fiscal_positions)
    _ensure_reference_fiscal_positions(
        client,
        company_id=reference_company_id,
        fiscal_position_names=fiscal_position_names,
    )
    return SyncFiscalPositionTaxesFromReferenceOperation(
        target_company_id=resolved.company_id,
        reference_company_id=reference_company_id,
        reference_company_name=str(
            reference_company_name or reference.company_name or f"Company {reference_company_id}"
        ),
        display_language=spec.localization.primary_display_language,
        fiscal_position_names=fiscal_position_names,
        reference_account_targets=_reference_account_targets(spec),
        reason=(
            "Mirror fiscal-position taxes from the reference AT company into the target company"
        ),
    )


def _read_reference_company_name(client: Json2Client, spec: ProjectSpec) -> str | None:
    reference = spec.reference_environment
    records = client.read(
        "res.company",
        [reference.company_id],
        ["id", "name"],
    )
    if len(records) != 1:
        raise Json2ClientError(f"Missing reference company id {reference.company_id}")
    name = records[0].get("name")
    return name if isinstance(name, str) else None


def _ensure_reference_fiscal_positions(
    client: Json2Client,
    *,
    company_id: int,
    fiscal_position_names: tuple[str, ...],
) -> None:
    records = client.search_read(
        "account.fiscal.position",
        domain=[
            ["company_id", "=", company_id],
            ["name", "in", list(fiscal_position_names)],
        ],
        fields=["id", "name"],
        order="id",
    )
    names = {str(record.get("name")) for record in records}
    missing = [name for name in fiscal_position_names if name not in names]
    if missing:
        missing_names = ", ".join(repr(name) for name in missing)
        raise Json2ClientError(
            "Reference company is missing fiscal positions required for tax sync: "
            f"{missing_names}"
        )


def _reference_account_targets(spec: ProjectSpec) -> tuple[ReferenceAccountTarget, ...]:
    targets: list[ReferenceAccountTarget] = []
    for account in spec.chart.explicit_accounts:
        reference_account_id = account.reference_account_id
        if reference_account_id is None:
            continue
        targets.append(
            ReferenceAccountTarget(
                reference_account_id=reference_account_id,
                target_code=account.code,
            )
        )
    return tuple(targets)
