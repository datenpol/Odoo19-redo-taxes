---
name: datenpol-euro-demo
description: Run the self-contained Austrian cosmetic Odoo 19 demo patcher via explicit `$datenpol-euro-demo` invocation.
---

# Datenpol Euro Demo

Use this skill only when explicitly invoked as `$datenpol-euro-demo`.

Run the bundled launcher script from the installed skill folder. Keep this wrapper thin and route all business logic through the packaged Python runtime.

## Commands

Default operator path:

```powershell
python scripts/datenpol_euro_demo.py "<URL>" "<API_KEY>"
```

Read-only diagnosis:

```powershell
python scripts/datenpol_euro_demo.py doctor "<URL>" "<API_KEY>"
python scripts/datenpol_euro_demo.py validate "<URL>" "<API_KEY>"
```

Apply only:

```powershell
python scripts/datenpol_euro_demo.py apply "<URL>" "<API_KEY>"
```

## Guardrails

- Stay on the cosmetic-only contract.
- Do not edit the mapping spec unless explicitly asked.
- Keep output in the engine JSON contract format.
- If `run` fails after writes start, rerun the same `run` command once before changing data.
