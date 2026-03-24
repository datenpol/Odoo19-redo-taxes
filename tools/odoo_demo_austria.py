#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def _main() -> int:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from odoo_demo_austria.cli import main

    return main()


if __name__ == "__main__":
    raise SystemExit(_main())
