from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "tools" / "build_datenpol_euro_demo_skill.py"
SPEC_SOURCE = ROOT / "data" / "austria-cosmetic-mapping-spec.draft.yaml"
REFERENCE_SOURCE = ROOT / "data" / "at-company-reference-values-2026-03-12.json"

CODEX_ARTIFACT = ROOT / "skills" / "datenpol-euro-demo"
CLAUDE_ARTIFACT = ROOT / "dist" / "claude" / "datenpol-euro-demo"
LEGACY_ARTIFACTS = (
    ROOT / ".agents" / "skills" / "datenpol-euro-demo",
    ROOT / ".claude" / "skills" / "datenpol-euro-demo",
)


def _build_artifacts() -> None:
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        details = "\n".join(
            [
                f"Build script failed with exit code {result.returncode}",
                f"STDOUT:\n{result.stdout}",
                f"STDERR:\n{result.stderr}",
            ]
        )
        raise AssertionError(details)


class SkillPackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _build_artifacts()

    def test_codex_artifact_layout(self) -> None:
        expected_paths = (
            CODEX_ARTIFACT / "SKILL.md",
            CODEX_ARTIFACT / "agents" / "openai.yaml",
            CODEX_ARTIFACT / "scripts" / "datenpol_euro_demo.py",
            CODEX_ARTIFACT / "runtime" / "odoo_demo_austria" / "cli.py",
            CODEX_ARTIFACT / "runtime" / "odoo_demo_austria" / "spec_loader.py",
            CODEX_ARTIFACT / "data" / "spec.json",
            CODEX_ARTIFACT / "data" / REFERENCE_SOURCE.name,
        )
        for path in expected_paths:
            self.assertTrue(path.exists(), f"Missing Codex artifact path: {path}")

    def test_claude_artifact_layout(self) -> None:
        expected_paths = (
            CLAUDE_ARTIFACT / "SKILL.md",
            CLAUDE_ARTIFACT / "scripts" / "datenpol_euro_demo.py",
            CLAUDE_ARTIFACT / "runtime" / "odoo_demo_austria" / "cli.py",
            CLAUDE_ARTIFACT / "runtime" / "odoo_demo_austria" / "spec_loader.py",
            CLAUDE_ARTIFACT / "data" / "spec.json",
            CLAUDE_ARTIFACT / "data" / REFERENCE_SOURCE.name,
        )
        for path in expected_paths:
            self.assertTrue(path.exists(), f"Missing Claude artifact path: {path}")

    def test_packaged_spec_json_matches_yaml_source(self) -> None:
        source_raw = yaml.safe_load(SPEC_SOURCE.read_text(encoding="utf-8"))
        self.assertIsInstance(source_raw, dict)
        for artifact in (CODEX_ARTIFACT, CLAUDE_ARTIFACT):
            packaged_raw = json.loads((artifact / "data" / "spec.json").read_text(encoding="utf-8"))
            self.assertEqual(source_raw, packaged_raw)

    def test_packaged_runtime_excludes_cache_artifacts(self) -> None:
        for artifact in (CODEX_ARTIFACT, CLAUDE_ARTIFACT):
            runtime_root = artifact / "runtime"
            self.assertFalse(list(runtime_root.rglob("__pycache__")))
            self.assertFalse(list(runtime_root.rglob("*.pyc")))
            self.assertFalse(list(runtime_root.rglob("*.pyo")))

    def test_build_removes_legacy_repo_local_skill_outputs(self) -> None:
        for artifact in LEGACY_ARTIFACTS:
            self.assertFalse(artifact.exists(), f"Legacy artifact should be absent: {artifact}")


if __name__ == "__main__":
    unittest.main()
