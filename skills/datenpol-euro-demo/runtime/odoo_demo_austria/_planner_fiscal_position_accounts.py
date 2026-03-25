from __future__ import annotations

from ._planner_types import (
    FiscalPositionAccountMappingLine,
    ReplaceFiscalPositionAccountsOperation,
)
from .models import ResolvedAccount, ResolvedProject


def build_fiscal_position_account_mapping_operations(
    resolved: ResolvedProject,
) -> list[ReplaceFiscalPositionAccountsOperation]:
    account_codes = _account_codes_by_spec_id(resolved.accounts)
    operations: list[ReplaceFiscalPositionAccountsOperation] = []
    for fiscal_position in resolved.fiscal_positions:
        operations.append(
            ReplaceFiscalPositionAccountsOperation(
                company_id=resolved.company_id,
                fiscal_position_id=fiscal_position.record_id,
                fiscal_position_name=fiscal_position.spec.target_name.base,
                mappings=tuple(
                    FiscalPositionAccountMappingLine(
                        source_account_code=_resolve_account_code(
                            account_codes,
                            mapping.source_account_id,
                            role="source",
                        ),
                        replacement_account_code=_resolve_account_code(
                            account_codes,
                            mapping.replacement_account_id,
                            role="replacement",
                        ),
                    )
                    for mapping in fiscal_position.spec.account_mappings
                ),
                reason=(
                    "Align fiscal position account mappings for "
                    f"{fiscal_position.spec.target_name.base}"
                ),
            )
        )
    return operations


def _account_codes_by_spec_id(accounts: tuple[ResolvedAccount, ...]) -> dict[int, str]:
    return {item.spec.record_id: item.spec.code for item in accounts}


def _resolve_account_code(
    account_codes: dict[int, str],
    spec_id: int,
    *,
    role: str,
) -> str:
    code = account_codes.get(spec_id)
    if code is None:
        raise ValueError(f"Unknown {role} account spec id {spec_id}")
    return code
