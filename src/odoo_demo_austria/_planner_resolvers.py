from __future__ import annotations

from ._planner_types import RepartitionLineRef
from .json2_client import Json2Client, Json2ClientError


def resolve_company_partner_id(client: Json2Client, company_id: int) -> int:
    records = client.read("res.company", [company_id], ["partner_id"])
    company = _single_record(records, model="res.company", record_id=company_id)
    partner = company.get("partner_id")
    if not isinstance(partner, list) or not partner:
        raise Json2ClientError(f"Company {company_id} has no partner_id")
    return int(partner[0])


def resolve_bank_trust_lock(client: Json2Client, bank_id: int) -> bool:
    records = client.read("res.partner.bank", [bank_id], ["lock_trust_fields"])
    bank = _single_record(records, model="res.partner.bank", record_id=bank_id)
    return bool(bank.get("lock_trust_fields"))


def resolve_repartition_lines(
    client: Json2Client,
    tax_ids: list[int],
) -> dict[int, tuple[RepartitionLineRef, ...]]:
    records = client.search_read(
        "account.tax.repartition.line",
        domain=[["tax_id", "in", tax_ids]],
        fields=["id", "tax_id", "document_type", "repartition_type"],
        order="tax_id,id",
    )
    grouped: dict[int, list[RepartitionLineRef]] = {tax_id: [] for tax_id in tax_ids}
    for record in records:
        tax_ref = record.get("tax_id")
        if not isinstance(tax_ref, list) or not tax_ref:
            raise Json2ClientError("account.tax.repartition.line returned a line without tax_id")
        tax_id = int(tax_ref[0])
        grouped.setdefault(tax_id, []).append(
            RepartitionLineRef(
                record_id=int(record["id"]),
                tax_id=tax_id,
                document_type=str(record["document_type"]),
                repartition_type=str(record["repartition_type"]),
            )
        )
    return {tax_id: tuple(lines) for tax_id, lines in grouped.items()}


def _single_record(
    records: list[dict[str, object]],
    *,
    model: str,
    record_id: int,
) -> dict[str, object]:
    if len(records) != 1:
        raise Json2ClientError(f"Expected exactly one {model} record for id {record_id}")
    return records[0]
