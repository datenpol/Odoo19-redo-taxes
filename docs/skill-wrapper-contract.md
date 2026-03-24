# Skill Wrapper Contract

## Scope

- Cosmetic-only.
- No `report-aware` path.
- No GUI.
- Python installation on operator machines is acceptable.

## Rollout Status

The end-state operator contract stays the same, but the implementation lands in stages.

Reason:

- The current cosmetic engine still depends on frozen database IDs in the mapping spec.
- A public `doctor` command would therefore be misleading until the resolver layer can find all required targets dynamically.

Implementation order:

1. Fix wrapper/bootstrap behavior.
2. Freeze `--format json|text` and exit codes.
3. Add public `run`.
4. Replace fixed-ID assumptions with dynamic resolution.
5. Make `doctor` public only after dynamic resolution is real.
6. Remove legacy development-only surfaces and add the actual Codex/Claude skill assets.

During this transition:

- `run`, `apply`, and `validate` are the public engine commands.
- `doctor` remains internal.
- Legacy developer surfaces such as `plan`, `--mode`, and `--dry-run` may exist temporarily, but they are not part of the operator contract and must not be used by skill wrappers.

## Operator UX

Current rollout invocation:

```text
$datenpol-euro-demo URL API_KEY
```

Current rollout behavior:

- The wrapper calls `run`.
- The wrapper does not call `doctor` directly.
- The wrapper assumes cosmetic-only operation.

End-state behavior after the resolver refactor:

1. `doctor`
2. `apply`
3. `validate`

Optional support commands for consultants:

```text
$datenpol-euro-demo validate URL API_KEY
```

`doctor` becomes an optional consultant support command only after the resolver refactor is complete and the command is made public.

## Architecture

- One shared Python core in this repo.
- One Codex skill wrapper.
- One Claude skill wrapper.
- Skills stay thin and call the same Python engine.

Do not put Odoo business logic into the skill instructions. Keep the logic in Python so the two skill implementations do not drift.

## Engine Commands

Current staged public engine contract:

```text
odoo-demo-austria apply --base-url URL [--format text|json]
odoo-demo-austria validate --base-url URL [--format text|json]
odoo-demo-austria run --base-url URL [--format text|json]
```

Target end-state engine contract:

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
- Not public until the resolver layer replaces fixed-ID assumptions.

`apply`

- Applies cosmetic changes only.
- Assumes preflight already passed.

`validate`

- Read-only.
- Validates expected cosmetic end state.

`run`

- In the current rollout it is the only public one-command operator path.
- In the end-state contract it executes `doctor -> apply -> validate`.
- In the end-state contract it aborts before write if `doctor` fails.
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

Public commands in this rollout always emit `mode = cosmetic`.

## Non-Goals For V1

- No stored credential aliases.
- No login or password handling unless API-only turns out to be insufficient.
- No separate packaged GUI.
- No report-aware tax/report manipulation.
