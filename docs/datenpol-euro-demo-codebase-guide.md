# Datenpol Euro Demo Codebase Guide

## Start Here

This repo is not an Odoo add-on.

It is a small Python engine plus a packaged Codex skill that talks to Odoo 19 over the JSON-2 API and makes a demo company look Austrian on the surface.

That surface includes:

- company identity
- partner contact details
- bank display details
- currency labels
- tax groups
- taxes
- journals
- fiscal positions
- account names and Austrian-looking 4-digit account codes

It is cosmetic-first. It is not a real accounting migration tool.

If you remember only five things, remember these:

1. `src/odoo_demo_austria/` is the real engine.
2. `data/austria-cosmetic-mapping-spec.draft.yaml` is the main source of truth for business intent.
3. `skill_src/datenpol-euro-demo/` is the source for the skill wrapper and skill text.
4. `skills/datenpol-euro-demo/` and `dist/claude/datenpol-euro-demo/` are generated output.
5. The engine still assumes a partly seeded accounting setup. It does not support a truly bare instance today.

## What This Repo Ships

At a high level, the repo has four jobs:

1. Define the desired Austrian demo state in one mapping spec.
2. Resolve the current Odoo records that should be changed.
3. Build a safe list of write or create operations.
4. Package that engine into an installable Codex skill and a Claude artifact.

## Source Of Truth vs Generated Output

| Path | What it is | Edit by hand? |
| --- | --- | --- |
| `src/odoo_demo_austria/` | Canonical Python engine | Yes |
| `data/` | Canonical mapping spec and reference snapshot | Yes |
| `skill_src/datenpol-euro-demo/` | Canonical skill templates and launcher source | Yes |
| `tools/` | Local wrappers and build helpers | Yes |
| `tests/` | Safety net and packaging checks | Yes |
| `skills/datenpol-euro-demo/` | Generated Codex install boundary | No |
| `dist/claude/datenpol-euro-demo/` | Generated Claude artifact | No |
| `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/` | Tool caches | No |

The practical rule is simple:

- change `src/`, `data/`, `skill_src/`, `tools/`
- rebuild when needed
- do not hand-edit `skills/` or `dist/`

## The One-Screen Mental Model

```text
skill wrapper / local wrapper
        ->
      cli.py
        ->
  spec_loader.py + json2_client.py
        ->
 _planner_resolvers.py
        ->
 _planner_builders.py
        ->
  _runtime_apply.py
        ->
    validator.py
        ->
 JSON/text report with exit code
```

That is the whole engine in one line:

- load spec
- talk to Odoo
- resolve real records
- plan changes
- apply changes
- validate result
- report outcome

## Command Surface

The engine exposes four commands:

- `doctor`: resolve everything and make sure planning works, but do not write
- `apply`: resolve, plan, then write, but do not validate
- `validate`: read the current state and compare it against the spec
- `run`: resolve, plan, write, then validate

There are two normal entry points:

- local dev wrapper: `python tools/odoo_demo_austria.py ...`
- installed skill wrapper: `$datenpol-euro-demo URL API_KEY`

## Exit Codes

The public exit codes are stable and live in `_cli_contract.py`.

- `0`: success
- `2`: bad invocation
- `3`: API or transport failure
- `4`: preflight failure
- `5`: apply failure
- `6`: validation failure
- `7`: internal error

This matters because wrappers and automation can react to these codes without parsing free text.

## Directory Map

### `src/odoo_demo_austria/`

This is the real engine. Everything important lives here.

### `data/`

This holds the business inputs:

- `austria-cosmetic-mapping-spec.draft.yaml`: the editable spec
- `at-company-reference-values-2026-03-12.json`: the harvested reference snapshot

The current spec shape is broad enough to describe:

- source and reference environments
- localization rules
- company and bank identity
- currencies
- tax groups
- taxes
- journals
- fiscal positions
- explicit accounts
- validation notes

## What In The Spec Is Actually Executed

This is easy to misunderstand, so it is worth stating plainly.

Some parts of the YAML drive runtime behavior directly.
Some parts are kept mostly as structured documentation.
One top-level section is currently ignored by the Python engine.

### Executed by the engine

These sections are actively used in planning, applying, or validating:

- `source_environment`
- `reference_environment`
- `localization.primary_display_language`
- `localization.reference_snapshot_file`
- `identity`
- `currency`
- `tax_groups`
- `taxes`
- `journals`
- `fiscal_positions`
- `chart`

### Parsed, but mostly informational today

These values are loaded into `ProjectSpec`, but the current runtime does not branch much or at all on them:

- `version`
- `status`
- `localization.reference_harvest_date`
- `localization.translation_write_policy`
- `validation.api_assertions`
- `validation.ui_spot_checks`

In other words:

- the runtime validates real Odoo records with Python code
- it does not currently execute the human-readable validation notes from the YAML

### Present in YAML, but not loaded into `ProjectSpec`

- `design_principles`

Right now that section is documentation for humans, not input for the engine.

### `skill_src/datenpol-euro-demo/`

This is the editable skill source.

- `codex/SKILL.md`: Codex-facing skill instructions
- `codex/agents/openai.yaml`: small UI metadata file
- `claude/SKILL.md`: Claude-facing skill instructions
- `scripts/datenpol_euro_demo.py`: thin installed-skill launcher

### `skills/datenpol-euro-demo/`

Generated Codex artifact. This is the install boundary for GitHub skill installs.

### `dist/claude/datenpol-euro-demo/`

Generated Claude copy artifact.

### `tools/`

Repo-local helpers:

- `odoo_demo_austria.py`: local dev wrapper into `src/`
- `odoo_json2.py`: generic JSON-2 helper for manual API calls
- `build_datenpol_euro_demo_skill.py`: packages the skill artifacts
- `README.md`: quick tool usage notes

### `tests/`

The tests are split by responsibility:

- spec parsing
- resolving
- planning
- applying
- validation
- CLI contract
- launcher packaging
- public skill boundary
- live GitHub install smoke test
- file-length budget

### `docs/`

This folder now has two kinds of docs:

- operator and project docs that already existed
- this engineering guide

The existing docs are roughly:

- `odoo19-demo-austria-handoff-plan.md`: project history and rollout context
- `operator-runbook.md`: how operators run the tool
- `python-quality-standards.md`: quality gates
- `skill-wrapper-contract.md`: wrapper behavior contract
- `skill-packaging-plan.md` and `skill-implementation-checklist.md`: packaging and implementation planning
- `vertrieb-datenpol-euro-demo.md`: sales-facing quickstart

## Runtime File Map

### Entry, CLI, and transport

- `cli.py`
  The public CLI entry point. It parses arguments, loads the spec, builds the client, runs the selected command, and prints a report.

- `_cli_runtime.py`
  The orchestration layer. This is where `doctor`, `apply`, `validate`, and `run` are actually defined.

- `_cli_contract.py`
  The output contract. It defines the report dataclasses and stable exit codes.

- `json2_client.py`
  A thin Odoo JSON-2 client. It knows how to call `read`, `search_read`, `write`, `create`, and `context_get`.

### Spec loading and in-memory data model

- `models.py`
  All dataclasses for the parsed spec and for resolved runtime targets.

- `spec_loader.py`
  Loads YAML or JSON and turns raw data into a typed `ProjectSpec`.

- `_spec_sections.py`
  Parses the main top-level spec sections.

- `_spec_project_extras.py`
  Parses the chart and validation sections.

- `_spec_support.py`
  Small, strict helpers for type checks, translated text parsing, and reference snapshot path resolution.

### Planning and resolution

- `planner.py`
  The small public planner surface. It re-exports the pieces the rest of the repo uses.

- `_planner_name_matching.py`
  Name matching helpers. This is where `ae/oe/ue/ss` and umlaut variants are handled.

- `_planner_resolvers.py`
  The key preflight resolver. It looks up real Odoo records for company, bank, currency, taxes, tax groups, journals, fiscal positions, and accounts.

- `_planner_builders.py`
  Turns resolved records into a list of safe operations.

- `_planner_write_helpers.py`
  Builds the paired base-language and translated-language writes.

- `_planner_types.py`
  Defines operation types and the write/create allowlists.

- `_planner_fiscal_position_accounts.py`
  Converts fiscal position account mappings from spec IDs into account codes.

- `_planner_reference_tax_sync.py`
  Adds the optional “copy tax surface from the reference company” operation.

### Apply side

- `_runtime_apply.py`
  Executes planned operations against Odoo.

- `_runtime_reference_tax_sync.py`
  High-level driver for the reference-company tax sync.

- `_runtime_reference_tax_sync_read.py`
  Reads reference fiscal positions, taxes, tax groups, and accounts.

- `_runtime_reference_tax_sync_accounts.py`
  Resolves or creates target-side accounts and tax groups needed by synced taxes.

- `_runtime_reference_tax_sync_taxes.py`
  Resolves or creates target-side taxes and then reconnects tax relationships.

- `_runtime_reference_tax_sync_types.py`
  Small dataclasses used only by the sync runtime.

### Validation side

- `validator.py`
  Top-level validation entry point.

- `_validator_identity.py`
  Checks company, partner, and bank identity fields.

- `_validator_cosmetic.py`
  Checks currencies, tax groups, taxes, journals, fiscal positions, and accounts.

- `_validator_reference_tax_surface.py`
  When the reference company is in the same database, this compares the target tax surface against the reference tax surface instead of only checking static tax IDs.

- `_validator_support.py`
  Shared validation helpers and the `ValidationIssue` dataclass.

## How The Main Runtime Flow Works

### 1. Load the spec

`spec_loader.py` reads the YAML or JSON file and builds a typed `ProjectSpec`.

This is strict on purpose. If the spec is malformed, the tool fails early and loudly.

### 2. Resolve the real Odoo records

`_planner_resolvers.py` is the first real gate.

It resolves:

- the source company
- the company partner
- the company bank account
- the active company currency
- the displaced seeded currency
- taxes
- tax groups
- journals
- fiscal positions
- explicit accounts

This step does not write anything. It just proves that the engine knows what it is about to touch.

### 3. Build the cosmetic plan

`_planner_builders.py` turns the resolved targets into a list of operations.

Those operations are plain dataclasses. They are not executed yet.

The plan includes:

- write company identity
- write partner identity
- write bank details
- rename currencies
- rename tax groups
- rename and retune taxes
- rename journals
- align or create fiscal positions
- align or create explicit accounts
- replace fiscal-position account mappings
- optionally mirror tax surfaces from the reference company

### 4. Safety-check the plan

`_planner_types.py` rejects writes and creates that touch unexpected models or unexpected fields.

That is a big safety rail in this repo. The engine is intentionally small and explicit about what it is allowed to change.

### 5. Apply the plan

`_runtime_apply.py` executes each planned operation in order.

There are four operation kinds today:

- `WriteOperation`
- `EnsureCreateOperation`
- `ReplaceFiscalPositionAccountsOperation`
- `SyncFiscalPositionTaxesFromReferenceOperation`

### 6. Validate the result

`validator.py` re-resolves the target state and checks whether the visible surface now matches the spec.

If the reference company is in the same database, fiscal-position tax validation becomes dynamic and compares against the reference company instead of only comparing fixed target tax IDs.

## The Current Hard Failures

This is the part that matters most when something breaks.

The short version:

- the engine is strict
- preflight expects clean resolution
- “not found” and “found too many” are both blockers in many places

### The generic hard-failure rule

The most important hidden rule lives in `_planner_resolvers.py`:

- many lookups end in `_single_record(...)`
- `_single_record(...)` fails unless there is exactly one match

So the resolver does not only fail on “missing”.
It also fails on “ambiguous”.

That means preflight can stop if Odoo contains:

- zero matches
- two matches
- a missing many2one value where the engine expects a linked record

### What must already exist today

These things are expected to exist and resolve cleanly before the tool can do normal cosmetic planning:

- source company
- company partner linked from the company
- company bank account
- active company currency pointer
- displaced seeded currency record
- all taxes listed in the spec
- all journals listed in the spec
- tax groups inferred from the resolved taxes

If any of those are missing or ambiguous, preflight fails.

### The two hard failures you called out

These are real and they matter:

- missing fiscal positions fail unless `create_if_missing` is true
- missing accounts fail unless `create_if_missing` is true

In plain terms:

- if a fiscal position is optional-to-create in the spec, preflight can keep going and the planner will schedule an `EnsureCreateOperation`
- if it is not marked `create_if_missing`, preflight stops
- same idea for accounts

### Other hard failures that are easy to forget

These are the ones people usually do not remember off the top of their head:

- taxes must resolve cleanly; the normal cosmetic path does not create them
- journals must resolve cleanly; the normal cosmetic path does not create them
- tax groups are derived from the resolved taxes and must line up one-to-one
- if a fiscal position account mapping references an unknown spec account ID, planning fails
- if an account is marked `create_if_missing` but has no `account_type`, planning fails
- if reference tax sync is enabled, the reference company must exist
- if reference tax sync is enabled, the named fiscal positions must exist in the reference company too
- if reference tax sync cannot map a required account to one clear target account, apply fails
- if a create lookup finds more than one record, apply fails
- if a supposedly unique lookup by account code or fiscal position name returns multiple rows, apply fails

## Can This Work On A Truly Bare Instance?

No. Not today.

That is the blunt answer.

The engine can create some things, but not enough to bootstrap a raw accounting setup from scratch.

### What it can create today

- explicit accounts where the spec says `create_if_missing: true`
- fiscal positions where the spec says `create_if_missing: true`
- extra target-company accounts needed during reference tax sync
- target-company tax groups during reference tax sync
- target-company taxes during reference tax sync

### What it still assumes already exists

- a real source company
- a company partner linked to that company
- at least one company bank account
- the currencies it plans to rename
- the journals in the spec
- the base taxes used by the normal cosmetic path
- a usable reference company when `reference_environment.same_database` is true

So “no modules installed yet” is still out of reach.

The real blocker is not only the two lines about fiscal positions and accounts.
The bigger blocker is that the resolver still expects core accounting surface area to be there before planning starts.

## The Reference Tax Sync Path

This is the most dynamic part of the codebase.

It only activates when `reference_environment.same_database` is `true`.

When that is true, the engine does not treat the target taxes as fully static.
Instead, it:

1. reads fiscal positions in the target company
2. reads matching fiscal positions in the reference company
3. loads reference taxes and tax groups
4. loads reference accounts used by those taxes and groups
5. resolves or creates needed target accounts
6. resolves or creates needed target tax groups
7. resolves or creates needed target taxes
8. reconnects fiscal position and original-tax relationships on the target side

This is why the validation logic for fiscal positions is more complex than the rest of the engine.
When reference sync is enabled, validation compares the target tax surface to the reference company’s tax surface.

## Why The Engine Uses Account Codes So Heavily

This repo leans on account codes because they are more stable than translated display names once the cosmetic rename has happened.

The planner resolves accounts by name first, then falls back to code.
Fiscal-position account mappings are eventually applied by account code as well.

That is a deliberate choice.
Display names move around.
Codes are the stronger anchor for this repo’s purpose.

## Translation Handling

The repo writes both base values and translated display values.

The pattern is:

- write canonical base values with no language context
- write translated values with `context={"lang": "de_DE"}`

That logic lives in `_planner_write_helpers.py`.

This matters for:

- tax names
- tax descriptions
- invoice labels
- journal names
- fiscal position names
- account names
- currency labels

The resolver also knows how to match:

- original source names
- base target names
- translated target names
- ASCII spellings against umlaut spellings

That name logic lives in `_planner_name_matching.py`.

## Packaging Flow

The build script is `tools/build_datenpol_euro_demo_skill.py`.

It does three simple things:

1. wipes the generated output folders
2. copies runtime code and launcher files into the skill artifacts
3. converts the YAML spec into packaged `spec.json`

It also removes old legacy repo-local skill output paths.

The important packaging rule is:

- the installed skill must be self-contained

That is why the build step copies `src/` and `data/` content into the packaged skill folders instead of pointing back into the repo.

## Tests And What They Cover

| Test file | What it proves |
| --- | --- |
| `test_spec_loader.py` | YAML/JSON spec loading, translations, optional fields, and clear error messages |
| `test_resolvers.py` | dynamic target resolution, translated names, and umlaut/ascii matching |
| `test_planner.py` | full plan shape, ordering, translated writes, account creation, and fiscal-position mappings |
| `test_runtime_apply.py` | ensure-create behavior and fiscal-position account rewrite behavior |
| `test_runtime_reference_tax_sync.py` | the reference-company tax copy path, including account and tax-group mapping |
| `test_validator_reference_tax_surface.py` | dynamic tax-surface comparison against the reference company |
| `test_cli.py` | public command contract, JSON output shape, and exit code behavior |
| `test_skill_launcher.py` | generated skill launcher behavior and JSON-spec bootstrapping |
| `test_skill_packaging.py` | artifact layout and packaged spec correctness |
| `test_skill_github_install.py` | public skill boundary and optional live installer smoke test |
| `test_file_lengths.py` | the 400-line budget rule for Python files |

## Quality Gates

The Python quality gates in this repo are strict and simple:

```powershell
python -m ruff check src tests tools
python -m mypy src tests tools
python -m pytest -q
```

There is also an enforced file-length budget:

- every Python file in `src/`, `tests/`, and `tools/` must stay at 400 lines or less

That design rule explains why the engine is split into many small helper files.

## Where To Change What

If you want to change business intent:

- edit `data/austria-cosmetic-mapping-spec.draft.yaml`

If you want to change runtime behavior:

- edit `src/odoo_demo_austria/`

If you want to change the installed skill wording or launcher:

- edit `skill_src/datenpol-euro-demo/`

If you want to change packaging:

- edit `tools/build_datenpol_euro_demo_skill.py`

If you change runtime or skill templates:

- rerun `python tools/build_datenpol_euro_demo_skill.py`

## Safe Next Step If Bare-Instance Support Becomes A Goal

The simplest robust path is not to weaken the current resolver.

The better path is to add a separate bootstrap phase or bootstrap mode behind an explicit toggle.

Why:

- today’s resolver is strict because the repo is optimized for demo stability
- silently turning missing taxes, journals, or company records into “best effort” behavior would make the demo less predictable
- a bootstrap path has different assumptions, different safety checks, and a different failure model

So if “works on a bare instance” becomes a real requirement, treat that as a new mode, not a small patch.

## Official Odoo 19 References Used For This Guide

These are the official Odoo 19 references that matter most for this repo:

- JSON-2 API transaction behavior:
  [External JSON-2 API](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)

- Fiscal position fields and behavior:
  [Fiscal Position model reference](https://www.odoo.com/documentation/19.0/developer/reference/standard_modules/account/account_fiscal_position.html)

- Tax behavior and fiscal-position tax mapping notes:
  [Taxes](https://www.odoo.com/documentation/19.0/applications/finance/accounting/taxes.html)

- Chart of accounts basics and account-code role:
  [Accounting cheat sheet](https://www.odoo.com/documentation/19.0/applications/finance/accounting/get_started/cheat_sheet.html)

The two Odoo facts that shape this repo most are:

- JSON-2 calls each run in their own SQL transaction, so multi-call runs can be partially applied
- fiscal positions in Odoo are where tax mappings and account mappings live

That is why this repo is:

- idempotent where possible
- strict in preflight
- careful about reruns after partial failure
