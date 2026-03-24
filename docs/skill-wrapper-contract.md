# Skill Wrapper Contract

## Scope

- Cosmetic-only.
- No `report-aware` path.
- No GUI.
- Python installation on operator machines is acceptable.

## Operator UX

Normal invocation:

```text
$datenpol-euro-demo URL API_KEY
```

The wrapper should assume cosmetic mode and execute the full safe flow:

1. `doctor`
2. `apply`
3. `validate`

Optional support commands for consultants:

```text
$datenpol-euro-demo doctor URL API_KEY
$datenpol-euro-demo validate URL API_KEY
```

## Architecture

- One shared Python core in this repo.
- One Codex skill wrapper.
- One Claude skill wrapper.
- Skills stay thin and call the same Python engine.

Do not put Odoo business logic into the skill instructions. Keep the logic in Python so the two skill implementations do not drift.

## Engine Commands

The target engine contract is:

```text
odoo-demo-austria doctor --base-url URL
odoo-demo-austria apply --base-url URL
odoo-demo-austria validate --base-url URL
odoo-demo-austria run --base-url URL
```

Authentication:

- Skill receives `API_KEY`.
- Skill passes the key through `ODOO_API_KEY`.
- Engine reads the key from the environment by default.

Advanced only:

- `--database DBNAME`

## Command Semantics

`doctor`

- Read-only.
- Resolves all required cosmetic targets dynamically.
- Fails before write if required targets are missing or ambiguous.

`apply`

- Applies cosmetic changes only.
- Assumes preflight already passed.

`validate`

- Read-only.
- Validates expected cosmetic end state.

`run`

- Executes `doctor -> apply -> validate`.
- Aborts before write if `doctor` fails.
- This is the default path for both skill wrappers.

## Exit Codes

- `0`: success
- `2`: bad invocation or missing required argument
- `3`: auth, connection, or API failure
- `4`: preflight failure
- `5`: apply failure
- `6`: validation failure
- `7`: unexpected internal error

## Output Contract

The engine should support:

```text
--format json
```

Both skill wrappers should consume the same machine-readable JSON contract.

Expected top-level fields:

- `command`
- `mode`
- `base_url`
- `status`
- `summary`

Expected nested sections:

- `preflight`
- `apply`
- `validation`

## Non-Goals For V1

- No stored credential aliases.
- No login or password handling unless API-only turns out to be insufficient.
- No separate packaged GUI.
- No report-aware tax/report manipulation.
