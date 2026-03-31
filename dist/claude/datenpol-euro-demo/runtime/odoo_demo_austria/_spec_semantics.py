from __future__ import annotations

from collections.abc import Mapping

from .models import AccountSpec, ProjectSpec, SpecValidationError


def validate_project_spec(spec: ProjectSpec) -> None:
    _validate_reference_environment(spec)
    _validate_optional_accounts(spec)


def _validate_reference_environment(spec: ProjectSpec) -> None:
    reference = spec.reference_environment
    if reference.same_database and reference.company_name is None:
        raise SpecValidationError(
            "reference_environment.company_name is required when same_database is true"
        )
    if not reference.same_database and reference.company_id is None:
        raise SpecValidationError(
            "reference_environment.company_id is required when same_database is false"
        )


def _validate_optional_accounts(spec: ProjectSpec) -> None:
    accounts_by_id = {account.record_id: account for account in spec.chart.explicit_accounts}
    for fiscal_position in spec.fiscal_positions:
        for mapping in fiscal_position.account_mappings:
            _reject_optional_mapping_account(
                accounts_by_id,
                mapping.source_account_id,
                path=(
                    "fiscal_positions"
                    f"[{fiscal_position.target_name.base}].account_mappings.source_account_id"
                ),
            )
            _reject_optional_mapping_account(
                accounts_by_id,
                mapping.replacement_account_id,
                path=(
                    "fiscal_positions"
                    f"[{fiscal_position.target_name.base}].account_mappings.replacement_account_id"
                ),
            )


def _reject_optional_mapping_account(
    accounts_by_id: Mapping[int, AccountSpec],
    account_spec_id: int,
    *,
    path: str,
) -> None:
    account = accounts_by_id.get(account_spec_id)
    if account is None:
        return
    if account.optional:
        raise SpecValidationError(
            f"{path} references optional account spec id {account_spec_id}, which is unsupported"
        )
