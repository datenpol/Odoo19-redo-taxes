#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

_COMMANDS = ("run", "doctor", "validate", "apply")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        command, base_url, api_key = _parse_args(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    os.environ["ODOO_API_KEY"] = api_key
    skill_root = _resolve_skill_root()
    spec_path = skill_root / "data" / "spec.json"
    engine_argv = [
        command,
        "--format",
        "json",
        "--spec",
        str(spec_path),
        "--base-url",
        base_url,
    ]
    return _run_engine(skill_root, engine_argv)


def _parse_args(args: list[str]) -> tuple[str, str, str]:
    if not args:
        raise ValueError(_usage())
    first = args[0]
    if first in _COMMANDS:
        if len(args) != 3:
            raise ValueError(_usage())
        return first, args[1], args[2]
    if len(args) != 2:
        raise ValueError(_usage())
    return "run", args[0], args[1]


def _usage() -> str:
    return (
        "Usage: datenpol_euro_demo.py [run|doctor|validate|apply] URL API_KEY\n"
        "       datenpol_euro_demo.py URL API_KEY"
    )


def _resolve_skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_engine(skill_root: Path, engine_argv: list[str]) -> int:
    runtime_root = skill_root / "runtime"
    runtime_entry = str(runtime_root)
    if runtime_entry not in sys.path:
        sys.path.insert(0, runtime_entry)
    from odoo_demo_austria.cli import main as engine_main

    return engine_main(engine_argv)


if __name__ == "__main__":
    raise SystemExit(main())
