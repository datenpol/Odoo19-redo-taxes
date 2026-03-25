---
name: datenpol-euro-demo
description: Runs the Austrian cosmetic Odoo 19 demo patcher in this repository against a target instance. Use when you want to apply, validate, or diagnose the Datenpol Austria demo conversion from Claude Code.
argument-hint: <url> <api_key>
disable-model-invocation: true
---

Run the shared Python engine in this repository against `$0` using API key `$1`. Keep the wrapper thin and route all business logic through `tools/odoo_demo_austria.py`.

1. Work from the repository root.
2. Prefer the one-command operator path first:

```powershell
$env:ODOO_API_KEY = "$1"
python tools/odoo_demo_austria.py run --format json --base-url "$0"
```

3. If the user explicitly asks for read-only diagnosis, use:

```powershell
$env:ODOO_API_KEY = "$1"
python tools/odoo_demo_austria.py doctor --format json --base-url "$0"
python tools/odoo_demo_austria.py validate --format json --base-url "$0"
```

4. If the instance sits behind a shared domain with multiple databases, set `ODOO_DB` before running the command.
5. Parse the JSON result and summarize the command, overall status, exit code, and any failing stage.
6. Do not hardcode expected operation counts. They can change with the spec.
7. If `run` fails after starting writes, rerun the same `run` command once before changing code or data. Odoo 19 JSON-2 commits each call separately, so partial cosmetic state is possible and idempotent reruns are the recovery path.
8. If the rerun still fails, use `doctor` and `validate` to isolate whether the blocker is preflight, write-time, or post-write validation.
9. Do not widen scope beyond the cosmetic contract unless the user explicitly asks for it.
