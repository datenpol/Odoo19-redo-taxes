from __future__ import annotations

from pathlib import Path

import yaml

from ._spec_sections import build_project_spec
from ._spec_support import require_mapping
from .models import ProjectSpec


def load_spec(spec_path: str | Path) -> ProjectSpec:
    path = Path(spec_path).resolve()
    root = require_mapping(yaml.safe_load(path.read_text(encoding="utf-8")), "root")
    return build_project_spec(root, path)
