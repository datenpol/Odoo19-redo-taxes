# Odoo demo API tools

This repo is demo-only. Keep things fast, but avoid changes that could brick the instance.

## Setup (PowerShell)

Set your connection details as environment variables:

```powershell
$env:ODOO_BASE_URL = "https://dmdemousa.odoo19.at"
$env:ODOO_API_KEY  = "<your api key>"
# optional (only if needed)
$env:ODOO_DB       = "<db name>"
```

## Quick checks

```powershell
python tools/odoo_json2.py version
python tools/odoo_json2.py context
```

## Austria demo patcher

The production-oriented patcher lives under `src/odoo_demo_austria` and can be run directly through the wrapper script:

```powershell
python tools/odoo_demo_austria.py run --format json --base-url https://codexplayground.odoo19.at
python tools/odoo_demo_austria.py doctor --format text --base-url https://codexplayground.odoo19.at
python tools/odoo_demo_austria.py validate --format text --base-url https://codexplayground.odoo19.at
python tools/odoo_demo_austria.py apply --format text --base-url https://codexplayground.odoo19.at
```

Target direction for operator-facing skills:

```text
$datenpol-euro-demo URL API_KEY
```

The planned shared engine contract for the skill wrappers is documented in `docs/skill-wrapper-contract.md`.

Operator guidance and wrapper installation notes live in `docs/operator-runbook.md`.

Skill packaging paths in this repo:

- Source templates: `skill_src/datenpol-euro-demo`
- Public Codex install boundary: `skills/datenpol-euro-demo`
- Generated Claude artifact: `dist/claude/datenpol-euro-demo`

Generate artifacts:

```powershell
python tools/build_datenpol_euro_demo_skill.py
```

Notes:

- The patcher reads the API key from `ODOO_API_KEY` by default.
- `cosmetic` now covers company identity, currencies, journals, Austrian-looking fiscal positions, tax labels, and Austrian 4-digit account codes.
- The intended product direction is now cosmetic-only for staff-facing operation.
- Dynamic target resolution now powers the runtime path, so `doctor`, `apply`, `validate`, and `run` all operate on the cleaned cosmetic contract.
- `run` remains the default one-command surface for operators and future skill wrappers.
- The Codex distribution policy is global-only. Do not rely on repo-local `.agents/skills` auto-discovery for this skill.
- Report-aware runtime behavior is not part of the operator contract.
- Odoo 19 `JSON-2` commits each API call separately. If a `run` fails after starting writes, rerun the same `run` command once before changing code or data.
- Trusted partner bank accounts cannot have `acc_number` changed in place. The patcher detects that Odoo lock and skips immutable bank-account fields instead of failing the whole run.
- On Odoo 19 `JSON-2`, `create` expects `vals_list`, not `vals`. The client already handles that quirk.

## Generic calls (JSON-2)

Call any model method via `POST /json/2/<model>/<method>` by providing the request JSON payload.

Examples:

```powershell
# res.partner.search(domain)
python tools/odoo_json2.py call res.partner search '[[\"id\",\"=\",5]]'

# res.partner.read([ids], [fields])
python tools/odoo_json2.py call res.partner read '[[5],[\"name\",\"country_id\"]]'
```

Notes:
- `ODOO_BASE_URL` should be the instance root (usually **not** ending in `/odoo`).
- The script reads the API key from `ODOO_API_KEY` (so you don’t accidentally commit it).
- `create` calls on Odoo 19 `JSON-2` must use `vals_list`; this helper handles that for you.
