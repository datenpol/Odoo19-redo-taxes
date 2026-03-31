from __future__ import annotations

from dataclasses import dataclass

from .json2_client import Json2Client, Json2ClientError
from .models import ProjectSpec, ReferenceEnvironment


@dataclass(frozen=True)
class ResolvedReferenceCompany:
    record_id: int
    name: str | None


def resolve_reference_company(
    client: Json2Client,
    spec: ProjectSpec,
) -> ResolvedReferenceCompany:
    reference = spec.reference_environment
    if reference.same_database:
        return _resolve_same_database_reference_company(client, reference)
    return _resolve_reference_company_by_id(client, reference.company_id)


def _resolve_same_database_reference_company(
    client: Json2Client,
    reference: ReferenceEnvironment,
) -> ResolvedReferenceCompany:
    company_name = reference.company_name
    if company_name is None:
        raise Json2ClientError(
            "Same-database reference company_name is required for reference resolution"
        )
    records = client.search_read(
        "res.company",
        domain=[["name", "=", company_name]],
        fields=["id", "name"],
        order="id",
    )
    if not records:
        raise Json2ClientError(f"Missing reference company named {company_name!r}")
    if len(records) != 1:
        raise Json2ClientError(
            f"Expected exactly one reference company named {company_name!r}, got {len(records)}"
        )
    return _resolved_reference_company(records[0])


def _resolve_reference_company_by_id(
    client: Json2Client,
    company_id: int | None,
) -> ResolvedReferenceCompany:
    if company_id is None:
        raise Json2ClientError(
            "reference_environment.company_id is required when same_database is false"
        )
    records = client.read("res.company", [company_id], ["id", "name"])
    if len(records) != 1:
        raise Json2ClientError(f"Missing reference company id {company_id}")
    return _resolved_reference_company(records[0])


def _resolved_reference_company(record: dict[str, object]) -> ResolvedReferenceCompany:
    record_id = record.get("id")
    if isinstance(record_id, bool) or not isinstance(record_id, int):
        raise Json2ClientError("Reference company payload is missing an integer id")
    name = record.get("name")
    return ResolvedReferenceCompany(
        record_id=record_id,
        name=name if isinstance(name, str) else None,
    )
