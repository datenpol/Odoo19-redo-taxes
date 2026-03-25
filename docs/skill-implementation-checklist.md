# Skill Implementation Checklist

## Scope

This document turns the self-contained skill packaging plan into an implementation worklist for the `datenpol-euro-demo` Codex and Claude artifacts.

No item below changes the target operator contract. The public runtime contract remains:

- `run`
- `doctor`
- `validate`
- `apply`

## Canonical Sources

Keep these as the only source of truth:

- `src/odoo_demo_austria`
- `data/austria-cosmetic-mapping-spec.draft.yaml`
- `data/at-company-reference-values-2026-03-12.json`

Do not make `.agents/skills` or `.claude/skills` the editable source of truth.

## New Source Files To Add

Add:

- `tools/build_datenpol_euro_demo_skill.py`
- `skill_src/datenpol-euro-demo/codex/SKILL.md`
- `skill_src/datenpol-euro-demo/codex/agents/openai.yaml`
- `skill_src/datenpol-euro-demo/claude/SKILL.md`
- `skill_src/datenpol-euro-demo/scripts/datenpol_euro_demo.py`

Responsibilities:

- the build script packages the runtime and writes generated artifacts
- the Codex templates define Codex-only metadata and prompt behavior
- the Claude template defines Claude-only metadata and prompt behavior
- the shared launcher script stays tool-agnostic and is copied into both generated artifacts

## Generated Outputs

Generate and commit:

- `.agents/skills/datenpol-euro-demo`
- `.claude/skills/datenpol-euro-demo`

Each generated artifact should contain:

- `SKILL.md`
- `scripts/datenpol_euro_demo.py`
- `runtime/odoo_demo_austria/*.py`
- `data/spec.json`
- `data/at-company-reference-values-2026-03-12.json`

Codex also needs:

- `agents/openai.yaml`

## Minimum Engine Changes

The minimum engine change set is intentionally small.

Change:

- `src/odoo_demo_austria/spec_loader.py`

Required behavior:

- support `.json` in addition to `.yaml`
- use stdlib `json` for `.json`
- avoid a mandatory top-level `import yaml`
- import `yaml` only when a YAML file is actually loaded
- reject unsupported spec extensions with a clear `SpecValidationError` that names supported extensions

Reason:

- the packaged runtime should work without a runtime `PyYAML` dependency
- `cli.py` imports `load_spec`, so a top-level `yaml` import would still break the packaged launcher even if the packaged spec is JSON

Do not change business-logic modules in phase 1 unless a packaging test proves that it is required.

## Engine Files That Should Stay Untouched In Phase 1

Avoid modifying:

- `src/odoo_demo_austria/cli.py`
- `src/odoo_demo_austria/_cli_runtime.py`
- `src/odoo_demo_austria/json2_client.py`
- `src/odoo_demo_austria/_planner_builders.py`
- `src/odoo_demo_austria/_planner_resolvers.py`
- `src/odoo_demo_austria/validator.py`
- `src/odoo_demo_austria/models.py`

Phase 1 should not change Odoo behavior. It should only make the engine packageable.

## Launcher Responsibilities

`skill_src/datenpol-euro-demo/scripts/datenpol_euro_demo.py` should:

- resolve its own skill root from `__file__`
- add `runtime/` to `sys.path`
- default to `run`
- accept `doctor`, `validate`, and `apply` as explicit first arguments
- accept `URL API_KEY`
- set `ODOO_API_KEY` in-process
- preserve `ODOO_DB` if already set in the environment
- call `odoo_demo_austria.cli.main(...)` directly
- always pass `--format json`
- always pass `--spec <skill-root>/data/spec.json`

The launcher must never read from repo-root `src`, repo-root `data`, or `tools/`.

## Build Script Responsibilities

`tools/build_datenpol_euro_demo_skill.py` should:

1. delete and recreate the generated output directories
2. load the YAML spec and write raw-equivalent JSON to `spec.json`
3. copy the runtime package from `src/odoo_demo_austria`
4. copy the shared launcher into both generated artifacts
5. copy Codex and Claude templates into their respective outputs
6. copy the reference snapshot JSON into both generated artifacts
7. fail if required source files are missing
8. exclude cache artifacts while copying runtime (`__pycache__/`, `*.pyc`, `*.pyo`)

Keep the build simple. Do not serialize the dataclass model. Converting the YAML mapping to raw JSON is enough because the packaged runtime will still validate and parse it into `ProjectSpec`.

## Skill Metadata Rules

Codex template:

- disable implicit invocation
- keep interface metadata minimal and accurate
- document the explicit invocation form only

Claude template:

- keep `disable-model-invocation: true`
- keep the command explicit
- point to the bundled launcher, not repo `tools/`

## Tests To Add Or Extend

Add:

- `tests/test_skill_packaging.py`
- `tests/test_skill_launcher.py`

Extend:

- `tests/test_spec_loader.py`

Test responsibilities:

- YAML and JSON versions of the spec load to equivalent `ProjectSpec` values
- JSON spec loading succeeds even when `yaml` is unavailable in the runtime environment
- YAML spec loading still works when `PyYAML` is available
- YAML loading without `PyYAML` fails with a clear dependency error
- unsupported spec extension fails with a clear validation error
- the build script produces the expected artifact layout
- the build script excludes cache artifacts in generated runtime trees
- the generated launcher imports cleanly without `PyYAML`
- the generated launcher remains self-contained when invoked from outside the repository root
- the generated launcher handles invalid arguments cleanly

## Migration And Cleanup

After the generated Codex artifact exists:

- remove or clearly deprecate `skills/codex/datenpol-euro-demo`

After generation is in place:

- stop treating `.claude/skills/datenpol-euro-demo` as hand-edited source
- treat both generated skill folders as build outputs

## Minimum Safe Delivery Order

1. Add JSON support in `src/odoo_demo_austria/spec_loader.py`.
2. Add YAML/JSON parity tests.
3. Add the `skill_src/` templates and shared launcher source.
4. Add the build script.
5. Generate `.agents/skills/...` and `.claude/skills/...`.
6. Add packaging and launcher tests.
7. Remove or deprecate the old repo-bound Codex prototype path.
8. Clean up stale docs that still describe packaging as only planned once generation is implemented.

## Definition Of Done

Packaging is done only when all of these are true:

- a generated Codex artifact can be installed and used without this repository checkout
- a generated Claude artifact can be copied to `~/.claude/skills` and used without this repository checkout
- neither artifact reads from repo-root `src`, repo-root `data`, or `tools/`
- the packaged runtime works without a runtime `PyYAML` dependency
- the operator UX stays `$datenpol-euro-demo URL API_KEY` and `/datenpol-euro-demo URL API_KEY`
