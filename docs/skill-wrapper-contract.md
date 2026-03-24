# Skill Wrapper Contract

## Scope

- Cosmetic-only.
- No `report-aware` path.
- No GUI.
- Python installation on operator machines is acceptable.

## Rollout Status

The staged cleanup has now reached the clean cosmetic engine contract.

Completed:

1. Wrapper/bootstrap behavior is stable through the local Python wrapper.
2. `--format json|text` and exit codes are frozen.
3. `run` is public.
4. Cosmetic target resolution is dynamic for the runtime path.
5. `doctor` is public and read-only.
6. Report-aware runtime surfaces are removed from the operator contract.

Still pending:

- Add the actual Codex and Claude skill assets.
- Add the operator runbook.
- Run the final live proof in `codexvalidation`.

## Operator UX

Current rollout invocation:

```text
$datenpol-euro-demo URL API_KEY
```

Current rollout behavior:

- The wrapper calls `run`.
- The wrapper assumes cosmetic-only operation.

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

Current public engine contract:

```text
odoo-demo-austria doctor --base-url URL [--format text|json]
odoo-demo-austria apply --base-url URL [--format text|json]
odoo-demo-austria validate --base-url URL [--format text|json]
odoo-demo-austria run --base-url URL [--format text|json]
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

- It is the default one-command operator path.
- It performs the same read-only preflight as `doctor` before any write.
- It aborts before write if preflight fails.
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

JSON output is the authoritative wrapper contract. Text output is only for human operators.

Expected top-level fields:

- `command`
- `mode`
- `base_url`
- `status`
- `summary`
- `exit_code`

Expected nested sections:

- `preflight`
- `apply`
- `validation`

Expected nested section fields:

- `status`
- `summary`
- `messages`

Command-specific optional fields:

- `operation_count`
- `issue_count`

Public commands emit `mode = cosmetic`.

## Non-Goals For V1

- No stored credential aliases.
- No login or password handling unless API-only turns out to be insufficient.
- No separate packaged GUI.
- No report-aware tax/report manipulation.
