from __future__ import annotations

from typing import Any, Mapping

from ._planner_types import EnsureCreateOperation, WriteOperation
from .models import HtmlTranslatedText, TranslatedText

TranslatedField = TranslatedText | HtmlTranslatedText


def build_translated_write_operations(
    *,
    model: str,
    record_id: int,
    base_fields: Mapping[str, Any],
    translated_fields: Mapping[str, TranslatedField],
    lang: str,
    reason: str,
) -> list[WriteOperation]:
    operations = [
        WriteOperation(
            model=model,
            ids=(record_id,),
            vals={**dict(base_fields), **base_translation_values(translated_fields)},
            reason=reason,
        )
    ]
    translated_vals = translated_values(translated_fields, lang)
    if translated_vals:
        operations.append(
            WriteOperation(
                model=model,
                ids=(record_id,),
                vals=translated_vals,
                context={"lang": lang},
                reason=f"{reason} ({lang} translation)",
            )
        )
    return operations


def build_ensure_create_operation(
    *,
    model: str,
    lookup_domain: list[list[Any]],
    create_fields: Mapping[str, Any],
    translated_fields: Mapping[str, TranslatedField],
    lang: str,
    reason: str,
) -> EnsureCreateOperation:
    create_vals = {**dict(create_fields), **base_translation_values(translated_fields)}
    translated_update_vals = translated_values(translated_fields, lang)
    if translated_update_vals == {
        field_name: create_vals[field_name] for field_name in translated_update_vals
    }:
        update_vals: dict[str, Any] | None = None
    else:
        update_vals = translated_update_vals

    return EnsureCreateOperation(
        model=model,
        lookup_domain=lookup_domain,
        create_vals=create_vals,
        update_vals=update_vals,
        update_context={"lang": lang} if update_vals is not None else None,
        reason=reason,
    )


def base_translation_values(
    translated_fields: Mapping[str, TranslatedField],
) -> dict[str, str]:
    base_vals: dict[str, str] = {}
    for field_name, value in translated_fields.items():
        if isinstance(value, HtmlTranslatedText):
            base_vals[field_name] = value.base_html
        else:
            base_vals[field_name] = value.base
    return base_vals


def translated_values(
    translated_fields: Mapping[str, TranslatedField],
    lang: str,
) -> dict[str, str]:
    return {field_name: value.value_for(lang) for field_name, value in translated_fields.items()}
