---
name: datenpol-euro-demo
description: Runs the Austrian cosmetic Odoo 19 demo patcher in this repository against a target instance. Use when the user wants to apply, validate, or diagnose the Datenpol Austria demo conversion via `$datenpol-euro-demo URL API_KEY`, or asks for the operator wrapper for this repo.
---

# Datenpol Euro Demo

Run the shared Python engine in this repository. Keep the wrapper thin: parse `URL` and `API_KEY`, set `ODOO_API_KEY` in the shell environment, and call the public engine contract instead of reimplementing business logic in prompt text.

## Workflow

1. Work from the repository root and use `python tools/odoo_demo_austria.py`.
2. Prefer `run --format json --base-url URL` for the normal operator path.
3. If the user explicitly asks for read-only diagnosis, use `doctor` or `validate`.
4. Prefer setting `ODOO_API_KEY` in the environment instead of passing `--api-key` on the command line.
5. Parse the JSON result and report a concise status summary with the failing stage and exit code when relevant.

## Commands

Default operator path:

```powershell
$env:ODOO_API_KEY = "<API_KEY>"
python tools/odoo_demo_austria.py run --format json --base-url "<URL>"
```

Read-only diagnosis:

```powershell
$env:ODOO_API_KEY = "<API_KEY>"
python tools/odoo_demo_austria.py doctor --format json --base-url "<URL>"
python tools/odoo_demo_austria.py validate --format json --base-url "<URL>"
```

Optional multi-database header:

```powershell
$env:ODOO_API_KEY = "<API_KEY>"
$env:ODOO_DB = "<DBNAME>"
python tools/odoo_demo_austria.py run --format json --base-url "<URL>"
```

## Guardrails

- Stay on the cosmetic-only contract.
- Do not edit the mapping spec unless the user explicitly asks for a spec change.
- Do not hardcode expected operation counts. They can change with the spec.
- If `run` fails after starting writes, rerun the same `run` command once before changing code or data. Odoo 19 JSON-2 commits each call separately, so partial cosmetic state is possible and safe reruns matter.
- If the rerun still fails, use `doctor` and `validate` to isolate whether the blocker is preflight, write-time, or post-write validation.
- Treat exit code `3` as auth, transport, or API failure.
- Treat exit code `4` as preflight resolver or ambiguity failure.
- Treat exit code `5` or `6` as a cosmetic apply or validation problem on a potentially partially updated instance.
