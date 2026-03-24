#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def _main() -> int:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    tools_dir = Path(__file__).resolve().parent
    cleaned_path: list[str] = []
    for entry in sys.path:
        resolved = Path(entry or ".").resolve()
        if resolved == tools_dir:
            continue
        cleaned_path.append(entry)
    sys.path[:] = cleaned_path
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from odoo_demo_austria.cli import main

    return main()


if __name__ == "__main__":
    raise SystemExit(_main())
