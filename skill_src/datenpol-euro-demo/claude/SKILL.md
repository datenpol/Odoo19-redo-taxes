---
name: datenpol-euro-demo
description: Runs the self-contained Austrian cosmetic Odoo 19 demo patcher.
argument-hint: [doctor|validate|apply] <url> <api_key>
disable-model-invocation: true
---

Run the bundled launcher from this skill folder and keep all business logic in the packaged runtime.

Default operator path:

```powershell
python scripts/datenpol_euro_demo.py "$0" "$1"
```

Read-only diagnosis:

```powershell
python scripts/datenpol_euro_demo.py doctor "$0" "$1"
python scripts/datenpol_euro_demo.py validate "$0" "$1"
```

Apply only:

```powershell
python scripts/datenpol_euro_demo.py apply "$0" "$1"
```

Guardrails:

- Keep scope cosmetic-only.
- Do not hardcode operation counts.
- If `run` fails after writes start, rerun `run` once before changing code or data.
