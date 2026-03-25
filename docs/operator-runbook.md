# Operator Runbook

## Scope

This repo ships one shared Python engine for Austrian cosmetic demo conversion on Odoo 19. The normal operator path is one command: `run`. The scope is cosmetic only.

This means:

- keep the existing demo data structure
- make the visible accounting surface look Austrian
- do not attempt real accounting migration
- do not use any removed `report-aware` runtime path

## Prerequisites

- Python 3.11 or newer
- a checkout of this repository
- an Odoo 19 instance with JSON-2 API access
- an API key with enough rights to read and write the targeted accounting records
- optional: database name if the domain hosts multiple Odoo databases

## Wrapper Assets

Codex skill asset:

- repo path: `skills/codex/datenpol-euro-demo`
- install target: copy or symlink to `$CODEX_HOME/skills/datenpol-euro-demo`
- operator invocation: `$datenpol-euro-demo URL API_KEY`

Claude Code project skill:

- repo path: `.claude/skills/datenpol-euro-demo/SKILL.md`
- availability: project-local when Claude Code is opened in this repository
- operator invocation: `/datenpol-euro-demo URL API_KEY`

## Manual Commands

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

Multi-database domains:

```powershell
$env:ODOO_API_KEY = "<API_KEY>"
$env:ODOO_DB = "<DBNAME>"
python tools/odoo_demo_austria.py run --format json --base-url "<URL>"
```

## Expected Exit Codes

- `0`: success
- `2`: bad invocation or missing required argument
- `3`: auth, connection, or API failure
- `4`: preflight failure
- `5`: apply failure
- `6`: validation failure
- `7`: unexpected internal error

## Failure Handling

Use this order:

1. Run `run` first.
2. If it returns `3`, fix credentials, connectivity, or database selection before retrying.
3. If it returns `4`, inspect `doctor` output and resolve the missing or ambiguous target.
4. If it returns `5` or `6`, rerun the same `run` command once before changing code or data.
5. If the rerun still fails, run `doctor` and `validate` to see whether the problem is now preflight-only or a post-write mismatch.
6. Do not rely on a specific planned or applied operation count in automation. The count can change with the mapping spec.

## Known Limits

- Odoo 19 JSON-2 runs each HTTP call in its own transaction, so a failed `run` can leave a partially applied cosmetic state. Safe reruns are therefore part of the operating model.
- Trusted partner bank accounts may lock immutable fields such as `acc_number`. The patcher skips those locked fields instead of failing the whole run.
- The mapping spec is still marked draft.
- The final proof target remains `codexvalidation`. A reported green smoke test on `codexsmoketest` is useful, but it is not the final sign-off target.
