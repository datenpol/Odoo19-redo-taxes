# Odoo 19 Demo Austria Conversion Handoff Plan

## Frozen scope

- Primary and only path: `cosmetic` mode, full Austrian look, no clean accounting migration.
- Sales fallback: chunked prompt pack with full cosmetic parity to the patcher, optimized for reliability rather than minimum prompt count.
- Build target: `codexplayground.odoo19.at`
- Final proof target: `codexvalidation.odoo19.at`

## Working assumption for fixed demo identity

- Demo company: `Datenpol Wohnatelier GmbH`
- Demo style: Austrian furniture and interior showroom tied to `datenpol.at`
- The exact legal and contact values will live in one mapping spec so they can be swapped centrally later.

## Core design decision

Keep one single source of truth for all cosmetic mappings. That mapping spec drives:

- API patcher behavior
- shared Python core engine behavior
- Codex skill wrapper behavior
- Claude skill wrapper behavior
- human prompt pack for Odoo AI
- documentation and validation checklist

The operator-facing workflow must stay as close to one command as possible. The intended skill UX is:

- `$datenpol-euro-demo URL API_KEY`

Skills are thin wrappers. Business logic stays in the shared Python core so Codex and Claude do not drift.

## Engineering guardrails

Python work in this repo now follows repository-level quality gates. The detailed reference lives in `docs/python-quality-standards.md`.

Current enforced rules:

- run `python -m ruff check src tests tools`
- run `python -m mypy src tests tools`
- run `python -m pytest -q`
- keep Ruff clean, including `C901` with max complexity `10`
- keep every Python file in `src`, `tests`, and `tools` at `400` lines or fewer
- split large modules into focused helper modules instead of growing monoliths

The mapping spec covers:

- company identity
- currency cosmetics
- journals
- fiscal positions
- tax groups
- taxes
- chart of accounts
- bank, account, and contact details
- validation expectations
- base values plus `de_DE` display values for translatable fields

## Implementation phases

1. Baseline the untouched `San Francisco` company in `codexplayground` and export the exact records that drive visible presentation.
2. Create the mapping spec as the single source of truth for company identity, currency cosmetics, journals, tax groups, taxes, accounts, bank and contact details, and validation expectations. The spec must be translation-aware so the Austrian-German UI is deterministic.
3. Implement the API patcher against Odoo 19 `JSON-2` with:
   - cosmetic-only scope
   - dynamic target resolution instead of fixed baseline IDs
   - skill-friendly CLI commands
   - machine-readable output for wrappers
   - idempotent behavior
4. Cosmetic mode only touches presentation-facing labels and metadata:
   - company master data
   - partner and contact data
   - currency labels, symbol, and symbol position
   - journals
   - Austrian-looking fiscal positions
   - tax names, tax group labels, and descriptions
   - chart of accounts names and Austrian 4-digit codes so `San Francisco` looks like Austrian seed data
   - bank and account display details
5. Expose the cosmetic engine through thin skill wrappers:
   - Codex skill wrapper
   - Claude skill wrapper
   - no GUI
   - Python install acceptable for operator machines
6. Generate the prompt pack from the same mapping spec, in chunks:
   - company and currency
   - tax groups
   - taxes
   - chart chunk 1
   - chart chunk 2
   - chart chunk 3
   - journals, bank, and details
   - verification prompt
7. Validate in `codexvalidation` from a clean start and compare results against the mapping spec instead of eyeballing.

## Operator Rollout Order

The implementation order for the operator-facing engine is intentionally staged so we do not freeze the wrong contract too early.

Completed:

1. Fix wrapper/bootstrap behavior and make the local wrapper dependable.
2. Freeze one machine-readable JSON schema plus stable exit codes.
3. Add public `run` so operators and future skill wrappers can use one command immediately.
4. Replace fixed database ID assumptions in the runtime path with dynamic target resolution.
5. Expose public read-only `doctor`.
6. Remove `report-aware` runtime surfaces from the operator contract.

Remaining:

1. Add the actual Codex and Claude skill assets.
2. Add the operator runbook.
3. Run the final proof in `codexvalidation`.

Why this order matters:

- The early rollout needed `run` before the resolver refactor was complete.
- `doctor` only became safe to expose after dynamic cosmetic resolution was real.
- Removing the `report-aware` runtime path keeps the operator contract aligned with the cosmetic-only scope.

Temporary rule during the rollout:

- Skill wrappers must target only the public cosmetic contract.

## Target Engine Contract

The shared Python engine should expose:

- `doctor`
- `apply`
- `validate`
- `run`

Current public contract:

- `doctor`
- `apply`
- `validate`
- `run`

Normal operator flow for skills:

- `run` only
- cosmetic only
- arguments: `URL API_KEY`

Skill wrappers should:

- parse `URL` and `API_KEY`
- pass the API key through the environment
- call the Python engine
- show concise success or blocker summaries

The engine should support machine-readable JSON output so both skill wrappers can consume the same result contract.

## Validation method

- API assertions for company, currency, journals, taxes, tax groups, and account labels in base and `de_DE` reads.
- Safety assertions: no posted moves deleted, no destructive operations, rerun stays stable.
- UI spot checks: accounting dashboard, chart of accounts, taxes, customer invoice, and vendor bill.
- Prompt pack test: run the fallback flow on a fresh environment and compare the visible result against the patcher outcome.
- Live contract proof: run the cleaned cosmetic engine in `codexvalidation` before freezing the skill assets.

## Deliverables

- mapping spec
- one-click patcher
- prompt pack with copy-paste blocks
- sales runbook
- validation checklist
- known-limits note that makes clear what remains fake and cosmetic
