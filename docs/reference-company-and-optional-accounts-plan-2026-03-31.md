# Reference Company And Optional Accounts Plan

Date: 2026-03-31

## Goal

Stabilize the `datenpol-euro-demo` runtime across Odoo 19 demo seeds where:

- `AT Company` can appear with different database IDs
- optional cash journals may exist without their matching cash accounts

The change must stay cosmetic-only, keep the runtime predictable, and avoid broad softening of required accounting surface.

## Approved Decisions

### 1. Same-database reference company resolves by exact name

For `reference_environment` with `same_database = true`:

- `company_name` is the authoritative selector
- the runtime resolves the reference company by exact `res.company.name`
- the lookup must return exactly one record
- the resolved record ID becomes the reference company ID for planning and validation

`company_id` remains in the spec as legacy metadata and a debugging hint, but it is not the selector in same-database mode.

### 2. Source company stays ID-based

`source_environment.company_id` remains the authoritative selector for the target company being modified.

This keeps the runtime scoped and avoids changing target-company selection semantics during this bug fix.

### 3. Only the three cash accounts become optional

Add optional-account support only for these explicit account spec entries:

- spec id `291`, code `2700`
- spec id `292`, code `2710`
- spec id `293`, code `2720`

Semantic meaning:

- if the account exists, resolve it and apply the cosmetic rename
- if the account does not exist, skip it cleanly
- do not create it
- do not fail preflight or validation because it is absent

### 4. No blanket softening of required accounts

All other missing accounts keep their current semantics:

- either they must exist
- or they must already be modeled with `create_if_missing`

This prevents accidental masking of real setup gaps.

### 5. Optional accounts may not participate in fiscal-position account mappings

Any account referenced by:

- `fiscal_positions[].account_mappings[].source_account_id`
- `fiscal_positions[].account_mappings[].replacement_account_id`

must not be marked optional.

If that invariant is violated, spec loading must fail immediately with a clear validation error.

This avoids moving a bad configuration from preflight into apply or validate.

## Runtime Semantics

### Reference company resolution

When `same_database = true`:

1. If `company_name` is present, resolve `res.company` by exact name.
2. If zero records are found, fail with a clear reference-company error.
3. If more than one record is found, fail with a clear ambiguity error.
4. Use the resolved ID everywhere the runtime currently uses `reference_environment.company_id`.

When `same_database = false`:

- keep the current `company_id` behavior unchanged

This keeps the fix narrow and avoids inventing new cross-database semantics.

### Optional account behavior

For `chart.explicit_accounts[]`:

- `optional = true` means the account is cosmetic-only and may be absent
- a missing optional account resolves to `record_id = None`
- planners skip write/create operations for missing optional accounts
- validators skip missing optional accounts

For accounts without `optional = true`:

- existing behavior stays unchanged

## Implementation Worklist

### Spec model and parsing

- add `optional: bool = False` to `AccountSpec`
- parse `chart.explicit_accounts[].optional`

### Reference-company helpers

- add a shared helper that resolves the effective reference company record and ID
- use that helper in:
  - reference tax sync planning
  - reference tax surface validation

### Resolver changes

- allow missing optional accounts to resolve as `record_id = None`
- keep missing non-optional, non-creatable accounts as hard failures

### Planner changes

- skip missing optional accounts
- keep `create_if_missing` logic unchanged
- do not change account creation rules

### Validator changes

- skip missing optional accounts
- keep missing non-optional accounts as validation failures

### Spec guardrail

- after loading the spec, reject any optional account that is referenced by a fiscal-position account mapping

## Tests To Add Or Update

- spec loader parses optional accounts
- spec loader rejects optional accounts used in fiscal-position mappings
- reference-company planning resolves by exact `company_name` when `same_database = true`
- reference-company validation resolves by exact `company_name` when `same_database = true`
- missing optional accounts do not fail resolver output
- missing optional accounts do not produce planner operations
- missing optional accounts do not fail cosmetic validation

## Packaging And Rollout

After the `src/` changes and tests are complete:

1. Regenerate packaged skill artifacts.
2. Run:
   - `python -m ruff check src tests tools`
   - `python -m mypy src tests tools`
   - `python -m pytest -q`
3. Commit and push the branch.

## Non-Goals

- no change to source-company selection
- no new account creation for `2700/2710/2720`
- no blanket optional handling for all accounts
- no change to cross-database reference semantics beyond this fix
