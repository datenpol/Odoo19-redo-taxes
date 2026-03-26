from __future__ import annotations

from ._planner_types import SyncFiscalPositionTaxesFromReferenceOperation
from ._runtime_reference_tax_sync_accounts import (
    candidate_codes_by_reference_id,
    ensure_dynamic_target_accounts,
    ensure_target_tax_groups,
)
from ._runtime_reference_tax_sync_read import (
    load_reference_accounts,
    load_reference_tax_groups,
    load_reference_taxes,
    resolve_fiscal_positions,
)
from ._runtime_reference_tax_sync_taxes import (
    apply_target_tax_relationships,
    ensure_target_taxes,
)
from .json2_client import Json2Client


def sync_fiscal_position_taxes_from_reference(
    client: Json2Client,
    operation: SyncFiscalPositionTaxesFromReferenceOperation,
) -> None:
    target_positions = resolve_fiscal_positions(
        client,
        company_id=operation.target_company_id,
        fiscal_position_names=operation.fiscal_position_names,
    )
    reference_positions = resolve_fiscal_positions(
        client,
        company_id=operation.reference_company_id,
        fiscal_position_names=operation.fiscal_position_names,
    )
    reference_taxes = load_reference_taxes(
        client,
        operation,
        reference_positions_by_name=reference_positions,
    )
    reference_groups = load_reference_tax_groups(client, reference_taxes)
    reference_accounts = load_reference_accounts(
        client,
        reference_company_id=operation.reference_company_id,
        reference_groups=reference_groups,
        reference_taxes=reference_taxes,
    )
    candidate_codes = candidate_codes_by_reference_id(operation.reference_account_targets)
    created_accounts = ensure_dynamic_target_accounts(
        client,
        target_company_id=operation.target_company_id,
        reference_accounts=reference_accounts,
        candidate_codes=candidate_codes,
    )
    group_id_map = ensure_target_tax_groups(
        client,
        operation,
        reference_groups=reference_groups,
        reference_accounts=reference_accounts,
        candidate_codes=candidate_codes,
        created_accounts=created_accounts,
    )
    target_tax_ids = ensure_target_taxes(
        client,
        operation,
        target_positions=target_positions,
        reference_taxes=reference_taxes,
        group_id_map=group_id_map,
        reference_accounts=reference_accounts,
        candidate_codes=candidate_codes,
        created_accounts=created_accounts,
    )
    apply_target_tax_relationships(
        client,
        reference_taxes=reference_taxes,
        target_positions=target_positions,
        target_tax_ids=target_tax_ids,
    )
