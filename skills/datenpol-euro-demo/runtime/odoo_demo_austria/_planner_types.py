from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ALLOWED_WRITE_FIELDS: dict[str, set[str]] = {
    "res.company": {"name", "currency_id"},
    "res.partner": {
        "name",
        "street",
        "street2",
        "zip",
        "city",
        "country_id",
        "state_id",
        "vat",
        "phone",
        "email",
        "website",
    },
    "res.partner.bank": {"acc_number", "bank_id", "allow_out_payment"},
    "res.currency": {
        "name",
        "symbol",
        "full_name",
        "currency_unit_label",
        "currency_subunit_label",
        "position",
    },
    "account.tax.group": {"name", "country_id"},
    "account.tax": {
        "name",
        "description",
        "invoice_label",
        "amount",
        "tax_group_id",
        "country_id",
    },
    "account.tax.repartition.line": {"account_id", "tag_ids", "use_in_tax_closing"},
    "account.journal": {"name"},
    "account.account": {"name", "code", "account_type", "reconcile"},
    "account.fiscal.position": {
        "name",
        "sequence",
        "auto_apply",
        "country_id",
        "country_group_id",
        "vat_required",
        "foreign_vat",
        "tax_ids",
        "note",
    },
}

ALLOWED_CREATE_FIELDS: dict[str, set[str]] = {
    "account.account": ALLOWED_WRITE_FIELDS["account.account"] | {"company_ids"},
    "account.fiscal.position": ALLOWED_WRITE_FIELDS["account.fiscal.position"] | {"company_id"},
}


@dataclass(frozen=True)
class WriteOperation:
    model: str
    ids: tuple[int, ...]
    vals: dict[str, Any]
    reason: str
    context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "write",
            "model": self.model,
            "ids": list(self.ids),
            "vals": self.vals,
            "reason": self.reason,
            "context": self.context,
        }


@dataclass(frozen=True)
class EnsureCreateOperation:
    model: str
    lookup_domain: list[list[Any]]
    create_vals: dict[str, Any]
    reason: str
    update_vals: dict[str, Any] | None = None
    update_context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "ensure_create",
            "model": self.model,
            "lookup_domain": self.lookup_domain,
            "create_vals": self.create_vals,
            "update_vals": self.update_vals,
            "update_context": self.update_context,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FiscalPositionAccountMappingLine:
    source_account_code: str
    replacement_account_code: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source_account_code": self.source_account_code,
            "replacement_account_code": self.replacement_account_code,
        }


@dataclass(frozen=True)
class ReplaceFiscalPositionAccountsOperation:
    company_id: int
    fiscal_position_id: int | None
    fiscal_position_name: str
    mappings: tuple[FiscalPositionAccountMappingLine, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "replace_fiscal_position_accounts",
            "company_id": self.company_id,
            "fiscal_position_id": self.fiscal_position_id,
            "fiscal_position_name": self.fiscal_position_name,
            "mappings": [item.to_dict() for item in self.mappings],
            "reason": self.reason,
        }


PlanOperation = WriteOperation | EnsureCreateOperation | ReplaceFiscalPositionAccountsOperation


def ensure_operation_safe(operation: PlanOperation) -> None:
    if isinstance(operation, ReplaceFiscalPositionAccountsOperation):
        for item in operation.mappings:
            if not item.source_account_code or not item.replacement_account_code:
                raise ValueError("Fiscal position account mappings must use non-empty codes")
        return

    if isinstance(operation, WriteOperation):
        _ensure_allowlisted_fields(
            operation.model,
            operation.vals,
            ALLOWED_WRITE_FIELDS.get(operation.model),
            action="write",
        )
        return

    _ensure_allowlisted_fields(
        operation.model,
        operation.create_vals,
        ALLOWED_CREATE_FIELDS.get(operation.model),
        action="create",
    )
    if operation.update_vals is not None:
        _ensure_allowlisted_fields(
            operation.model,
            operation.update_vals,
            ALLOWED_WRITE_FIELDS.get(operation.model),
            action="update",
        )


def _ensure_allowlisted_fields(
    model: str,
    values: dict[str, Any],
    allowed_fields: set[str] | None,
    *,
    action: str,
) -> None:
    if allowed_fields is None:
        raise ValueError(f"{action.title()} model not allowlisted: {model}")
    unexpected = sorted(set(values) - allowed_fields)
    if unexpected:
        joined = ", ".join(unexpected)
        raise ValueError(f"Unexpected {action} fields for {model}: {joined}")
