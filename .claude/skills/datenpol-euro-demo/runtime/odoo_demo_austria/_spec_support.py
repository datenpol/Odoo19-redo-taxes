from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import (
    CurrencyRecordSpec,
    HtmlTranslatedText,
    SpecValidationError,
    TranslatedText,
)


def require_mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SpecValidationError(f"{path} must be a mapping")
    return value


def require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise SpecValidationError(f"{path} must be a list")
    return value


def require_str(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise SpecValidationError(f"{path} must be a string")
    return value


def require_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SpecValidationError(f"{path} must be an integer")
    return value


def require_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise SpecValidationError(f"{path} must be a boolean")
    return value


def optional_int(value: Any, path: str) -> int | None:
    if value is None:
        return None
    return require_int(value, path)


def optional_str(value: Any, path: str) -> str | None:
    if value is None:
        return None
    return require_str(value, path)


def require_float(value: Any, path: str) -> float:
    if isinstance(value, bool):
        raise SpecValidationError(f"{path} must be numeric")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError as exc:
            raise SpecValidationError(f"{path} must be numeric") from exc
    raise SpecValidationError(f"{path} must be numeric")


def require_int_tuple(value: Any, path: str) -> tuple[int, ...]:
    return tuple(
        require_int(item, f"{path}[{index}]")
        for index, item in enumerate(require_list(value, path))
    )


def parse_translated_text(value: Any, path: str) -> TranslatedText:
    mapping = require_mapping(value, path)
    return TranslatedText(
        base=require_str(mapping.get("base"), f"{path}.base"),
        translations=_parse_translations(mapping, path),
    )


def parse_html_translated_text(value: Any, path: str) -> HtmlTranslatedText:
    mapping = require_mapping(value, path)
    return HtmlTranslatedText(
        base_html=require_str(mapping.get("base_html"), f"{path}.base_html"),
        translations=_parse_translations(mapping, path),
    )


def parse_currency_record(value: Any, path: str) -> CurrencyRecordSpec:
    mapping = require_mapping(value, path)
    return CurrencyRecordSpec(
        currency_id=require_int(mapping.get("currency_id"), f"{path}.currency_id"),
        source_code=require_str(mapping.get("source_code"), f"{path}.source_code"),
        target_code=require_str(mapping.get("target_code"), f"{path}.target_code"),
        target_symbol=require_str(mapping.get("target_symbol"), f"{path}.target_symbol"),
        target_full_name=parse_translated_text(
            mapping.get("target_full_name"),
            f"{path}.target_full_name",
        ),
        target_unit_label=parse_translated_text(
            mapping.get("target_unit_label"),
            f"{path}.target_unit_label",
        ),
        target_subunit_label=parse_translated_text(
            mapping.get("target_subunit_label"),
            f"{path}.target_subunit_label",
        ),
        target_position=require_str(mapping.get("target_position"), f"{path}.target_position"),
    )


def resolve_reference_snapshot(
    spec_path: Path,
    localization: dict[str, Any],
) -> Path:
    reference_snapshot = Path(
        require_str(
            localization.get("reference_snapshot_file"),
            "localization.reference_snapshot_file",
        )
    )
    if not reference_snapshot.is_absolute():
        reference_snapshot = (spec_path.parent.parent / reference_snapshot).resolve()
    return reference_snapshot


def _parse_translations(mapping: dict[str, Any], path: str) -> dict[str, str]:
    translations = require_mapping(mapping.get("translations"), f"{path}.translations")
    return {
        require_str(lang, f"{path}.translations.lang"): require_str(
            translated,
            f"{path}.translations[{lang}]",
        )
        for lang, translated in translations.items()
    }
