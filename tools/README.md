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
python tools/odoo_demo_austria.py plan --base-url https://codexplayground.odoo19.at
python tools/odoo_demo_austria.py apply --mode cosmetic --dry-run --base-url https://codexplayground.odoo19.at
python tools/odoo_demo_austria.py validate --mode cosmetic --base-url https://codexplayground.odoo19.at
python tools/odoo_demo_austria.py plan --mode report-aware --base-url https://codexplayground.odoo19.at
python tools/odoo_demo_austria.py validate --mode report-aware --base-url https://codexplayground.odoo19.at
```

Notes:

- The patcher reads the API key from `ODOO_API_KEY` by default.
- `plan` and `apply --dry-run` are safe discovery steps and do not change the environment.
- `cosmetic` now covers company identity, currencies, journals, Austrian-looking fiscal positions, tax labels, and Austrian 4-digit account codes.
- `report-aware` is implemented and extends the cosmetic plan with tax-country and repartition-line tagging changes.
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
