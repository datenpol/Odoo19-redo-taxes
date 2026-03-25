from __future__ import annotations

import builtins
import importlib.util
import os
import subprocess
import sys
import types
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "tools" / "build_datenpol_euro_demo_skill.py"
CODEX_LAUNCHER = ROOT / "skills" / "datenpol-euro-demo" / "scripts" / "datenpol_euro_demo.py"
_ORIGINAL_IMPORT = builtins.__import__


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


def _load_launcher(module_name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, CODEX_LAUNCHER)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Failed to build import spec for launcher: {CODEX_LAUNCHER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _raise_on_yaml_import(
    name: str,
    globals_dict: dict[str, Any] | None = None,
    locals_dict: dict[str, Any] | None = None,
    fromlist: tuple[Any, ...] = (),
    level: int = 0,
) -> Any:
    if name == "yaml":
        raise ModuleNotFoundError("No module named 'yaml'")
    return _ORIGINAL_IMPORT(name, globals_dict, locals_dict, fromlist, level)


def _clear_runtime_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "odoo_demo_austria" or module_name.startswith("odoo_demo_austria."):
            sys.modules.pop(module_name, None)


class SkillLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _build_artifacts()

    def test_wrapper_rejects_invalid_arguments(self) -> None:
        module = _load_launcher("datenpol_launcher_invalid_args")
        self.assertEqual(module.main([]), 2)
        self.assertEqual(module.main(["doctor", "https://example.odoo.test"]), 2)
        self.assertEqual(module.main(["unexpected", "https://example.odoo.test", "key"]), 2)

    def test_wrapper_defaults_to_run_and_sets_engine_arguments(self) -> None:
        module = _load_launcher("datenpol_launcher_default_run")
        captured: dict[str, Any] = {}

        def fake_run_engine(skill_root: Path, engine_argv: list[str]) -> int:
            captured["skill_root"] = skill_root
            captured["engine_argv"] = engine_argv
            return 0

        with patch.object(module, "_run_engine", side_effect=fake_run_engine):
            with patch.dict(os.environ, {}, clear=True):
                exit_code = module.main(["https://example.odoo.test", "secret-token"])
                self.assertEqual(os.environ.get("ODOO_API_KEY"), "secret-token")

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["engine_argv"][0], "run")
        self.assertIn("--format", captured["engine_argv"])
        self.assertIn("json", captured["engine_argv"])
        self.assertIn("--base-url", captured["engine_argv"])
        self.assertIn("https://example.odoo.test", captured["engine_argv"])
        self.assertIn("--spec", captured["engine_argv"])
        self.assertIn(
            str(captured["skill_root"] / "data" / "spec.json"),
            captured["engine_argv"],
        )

    def test_wrapper_passes_explicit_command(self) -> None:
        module = _load_launcher("datenpol_launcher_explicit_command")
        captured: dict[str, Any] = {}

        def fake_run_engine(skill_root: Path, engine_argv: list[str]) -> int:
            captured["engine_argv"] = engine_argv
            return 0

        with patch.object(module, "_run_engine", side_effect=fake_run_engine):
            exit_code = module.main(["doctor", "https://example.odoo.test", "secret-token"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["engine_argv"][0], "doctor")

    def test_wrapper_runs_with_blocked_yaml_when_using_json_spec(self) -> None:
        module = _load_launcher("datenpol_launcher_blocked_yaml")
        original_sys_path = list(sys.path)
        _clear_runtime_modules()
        try:
            with patch("builtins.__import__", new=_raise_on_yaml_import):
                exit_code = module.main(["not-a-url", "secret-token"])
        finally:
            sys.path[:] = original_sys_path
            _clear_runtime_modules()
        self.assertIn(exit_code, (3, 4))


if __name__ == "__main__":
    unittest.main()
