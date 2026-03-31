from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "tools" / "build_datenpol_euro_demo_skill.py"
PUBLIC_SKILL = ROOT / "skills" / "datenpol-euro-demo"
CODEX_HOME = Path(os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"))
INSTALLER = (
    CODEX_HOME
    / "skills"
    / ".system"
    / "skill-installer"
    / "scripts"
    / "install-skill-from-github.py"
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


class PublicSkillBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _build_artifacts()

    def test_public_skill_boundary_exists(self) -> None:
        expected_paths = (
            PUBLIC_SKILL / "SKILL.md",
            PUBLIC_SKILL / "agents" / "openai.yaml",
            PUBLIC_SKILL / "scripts" / "datenpol_euro_demo.py",
            PUBLIC_SKILL / "runtime" / "odoo_demo_austria" / "cli.py",
            PUBLIC_SKILL / "data" / "spec.json",
        )
        for path in expected_paths:
            self.assertTrue(path.exists(), f"Missing public skill path: {path}")

    def test_public_skill_copy_runs_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir) / "datenpol-euro-demo"
            shutil.copytree(PUBLIC_SKILL, install_root)
            result = subprocess.run(
                [sys.executable, str(install_root / "scripts" / "datenpol_euro_demo.py")],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage: datenpol_euro_demo.py", result.stderr)


@unittest.skipUnless(
    os.environ.get("RUN_GITHUB_INSTALL_TEST") == "1",
    "Set RUN_GITHUB_INSTALL_TEST=1 to run the live GitHub installer smoke test.",
)
class GitHubInstallerSmokeTests(unittest.TestCase):
    def test_github_installer_can_install_public_skill_boundary(self) -> None:
        if not INSTALLER.exists():
            self.skipTest(f"Installer script not found: {INSTALLER}")
        repo = os.environ.get("SKILL_INSTALL_TEST_REPO", "datenpol/Odoo19-redo-taxes")
        ref = os.environ.get("SKILL_INSTALL_TEST_REF", "main")
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_root = Path(temp_dir) / "skills"
            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALLER),
                    "--repo",
                    repo,
                    "--ref",
                    ref,
                    "--path",
                    "skills/datenpol-euro-demo",
                    "--dest",
                    str(dest_root),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                details = "\n".join(
                    [
                        f"Installer failed with exit code {result.returncode}",
                        f"STDOUT:\n{result.stdout}",
                        f"STDERR:\n{result.stderr}",
                    ]
                )
                self.fail(details)
            install_root = dest_root / "datenpol-euro-demo"
            self.assertTrue((install_root / "SKILL.md").exists())
            launcher = install_root / "scripts" / "datenpol_euro_demo.py"
            launch_result = subprocess.run(
                [sys.executable, str(launcher)],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(launch_result.returncode, 2)
            self.assertIn("Usage: datenpol_euro_demo.py", launch_result.stderr)


if __name__ == "__main__":
    unittest.main()
