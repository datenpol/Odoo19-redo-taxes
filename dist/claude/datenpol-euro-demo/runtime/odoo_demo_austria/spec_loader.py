from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._spec_sections import build_project_spec
from ._spec_semantics import validate_project_spec
from ._spec_support import require_mapping
from .models import ProjectSpec, SpecValidationError

_YAML_EXTENSIONS = (".yaml", ".yml")
_SUPPORTED_EXTENSIONS = (".json", *_YAML_EXTENSIONS)


def load_spec(spec_path: str | Path) -> ProjectSpec:
    path = Path(spec_path).resolve()
    root = require_mapping(_load_raw_spec(path), "root")
    spec = build_project_spec(root, path)
    validate_project_spec(spec)
    return spec


def _load_raw_spec(path: Path) -> Any:
    extension = path.suffix.lower()
    raw = path.read_text(encoding="utf-8")
    if extension == ".json":
        return json.loads(raw)
    if extension in _YAML_EXTENSIONS:
        return _import_yaml().safe_load(raw)
    supported = ", ".join(_SUPPORTED_EXTENSIONS)
    raise SpecValidationError(
        f"Unsupported spec extension '{path.suffix or '<none>'}'. Supported: {supported}"
    )


def _import_yaml() -> Any:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise SpecValidationError(
            "YAML spec loading requires PyYAML. Install PyYAML or provide a .json spec."
        ) from exc
    return yaml
