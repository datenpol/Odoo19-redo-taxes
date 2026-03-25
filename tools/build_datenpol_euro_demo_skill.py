from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SOURCE_ROOT = REPO_ROOT / "skill_src" / "datenpol-euro-demo"
RUNTIME_SOURCE = REPO_ROOT / "src" / "odoo_demo_austria"
SPEC_SOURCE = REPO_ROOT / "data" / "austria-cosmetic-mapping-spec.draft.yaml"
REFERENCE_SOURCE = REPO_ROOT / "data" / "at-company-reference-values-2026-03-12.json"

CODEX_OUTPUT = REPO_ROOT / ".agents" / "skills" / "datenpol-euro-demo"
CLAUDE_OUTPUT = REPO_ROOT / ".claude" / "skills" / "datenpol-euro-demo"

_CACHE_PATTERNS = ("__pycache__", "*.pyc", "*.pyo")


def build_datenpol_euro_demo_skill() -> None:
    _assert_required_sources()
    _recreate_directory(CODEX_OUTPUT)
    _recreate_directory(CLAUDE_OUTPUT)
    raw_spec = _load_raw_spec_mapping()
    _build_codex_artifact(raw_spec)
    _build_claude_artifact(raw_spec)


def _assert_required_sources() -> None:
    required_paths = (
        RUNTIME_SOURCE,
        SPEC_SOURCE,
        REFERENCE_SOURCE,
        SKILL_SOURCE_ROOT / "codex" / "SKILL.md",
        SKILL_SOURCE_ROOT / "codex" / "agents" / "openai.yaml",
        SKILL_SOURCE_ROOT / "claude" / "SKILL.md",
        SKILL_SOURCE_ROOT / "scripts" / "datenpol_euro_demo.py",
    )
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        missing_list = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Skill packaging sources are missing:\n{missing_list}")


def _recreate_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _load_raw_spec_mapping() -> dict[str, Any]:
    raw_spec = yaml.safe_load(SPEC_SOURCE.read_text(encoding="utf-8"))
    if not isinstance(raw_spec, dict):
        raise ValueError(f"Expected mapping in {SPEC_SOURCE}, got {type(raw_spec)!r}")
    return raw_spec


def _build_codex_artifact(raw_spec: dict[str, Any]) -> None:
    _populate_shared_content(CODEX_OUTPUT, raw_spec)
    shutil.copy2(
        SKILL_SOURCE_ROOT / "codex" / "SKILL.md",
        CODEX_OUTPUT / "SKILL.md",
    )
    agents_dir = CODEX_OUTPUT / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        SKILL_SOURCE_ROOT / "codex" / "agents" / "openai.yaml",
        agents_dir / "openai.yaml",
    )


def _build_claude_artifact(raw_spec: dict[str, Any]) -> None:
    _populate_shared_content(CLAUDE_OUTPUT, raw_spec)
    shutil.copy2(
        SKILL_SOURCE_ROOT / "claude" / "SKILL.md",
        CLAUDE_OUTPUT / "SKILL.md",
    )


def _populate_shared_content(target_root: Path, raw_spec: dict[str, Any]) -> None:
    shutil.copytree(
        RUNTIME_SOURCE,
        target_root / "runtime" / "odoo_demo_austria",
        ignore=shutil.ignore_patterns(*_CACHE_PATTERNS),
    )

    scripts_dir = target_root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        SKILL_SOURCE_ROOT / "scripts" / "datenpol_euro_demo.py",
        scripts_dir / "datenpol_euro_demo.py",
    )

    data_dir = target_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "spec.json").write_text(
        json.dumps(raw_spec, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(REFERENCE_SOURCE, data_dir / REFERENCE_SOURCE.name)


def main() -> int:
    build_datenpol_euro_demo_skill()
    print("Generated skill artifacts:")
    print(f"- {CODEX_OUTPUT}")
    print(f"- {CLAUDE_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
