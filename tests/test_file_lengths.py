from __future__ import annotations

from pathlib import Path

MAX_PYTHON_FILE_LINES = 400
ROOT = Path(__file__).resolve().parents[1]
CODE_ROOTS = ("src", "tests", "tools")


def test_python_files_stay_within_line_budget() -> None:
    violations: list[str] = []
    for relative_root in CODE_ROOTS:
        for path in sorted((ROOT / relative_root).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            line_count = sum(1 for _ in path.open(encoding="utf-8"))
            if line_count > MAX_PYTHON_FILE_LINES:
                rel_path = path.relative_to(ROOT)
                violations.append(f"{rel_path} has {line_count} lines")

    assert not violations, "\n".join(violations)
