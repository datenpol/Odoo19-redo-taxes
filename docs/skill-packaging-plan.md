# Skill Packaging Plan

## Scope

This document captures the target packaging model for `datenpol-euro-demo` as a self-contained Codex skill and a self-contained Claude skill.

Goal:

- install the skill and have it work on another machine without requiring this repository checkout
- keep one canonical Python engine and one canonical mapping spec in this repo
- generate tool-specific skill artifacts from that shared source

## Source Of Truth

Canonical source lives here:

- Python engine: `src/odoo_demo_austria`
- mapping spec: `data/austria-cosmetic-mapping-spec.draft.yaml`
- supporting reference snapshot: `data/at-company-reference-values-2026-03-12.json`

Operator machines should not need `src/odoo_demo_austria` after packaging. The source tree exists to build the packaged skill artifacts.

## Packaging Flow

Target flow:

```text
src/odoo_demo_austria + data/austria-cosmetic-mapping-spec.draft.yaml
-> build/package step
-> generated self-contained skill artifact
-> install/use on another machine
```

The installed skill must resolve all runtime files from its own folder and must not reach back into repo-root `src/` or `data/`.

## Target Artifact Paths

Codex:

- generated repo path: `.agents/skills/datenpol-euro-demo`
- intended use:
  - repo-local Codex skill when opening this repository
  - globally installable Codex skill when installed from the generated GitHub path via `$skill-installer`

Claude:

- generated repo path: `.claude/skills/datenpol-euro-demo`
- intended use:
  - project-local Claude skill when opening this repository
  - personal/global Claude skill when the generated folder is copied to `~/.claude/skills/datenpol-euro-demo`

## Target Artifact Contents

Codex artifact:

- `SKILL.md`
- `agents/openai.yaml`
- `scripts/datenpol_euro_demo.py`
- `runtime/odoo_demo_austria/*.py`
- `data/spec.json`
- `data/at-company-reference-values-2026-03-12.json`

Claude artifact:

- `SKILL.md`
- `scripts/datenpol_euro_demo.py`
- `runtime/odoo_demo_austria/*.py`
- `data/spec.json`
- `data/at-company-reference-values-2026-03-12.json`

The runtime package should be copied wholesale from `src/odoo_demo_austria` instead of hand-selecting files.

## Build Responsibilities

The packaging build should:

1. copy the runtime package from `src/odoo_demo_austria`
2. compile the YAML mapping spec to packaged JSON so the installed skill can avoid a runtime `PyYAML` dependency
3. generate tool-specific metadata and instruction files for Codex and Claude
4. ensure the packaged launcher resolves bundled files relative to its own `__file__`
5. keep the packaged runtime stdlib-only where practical

## Runtime Rules

- installed artifacts must not import from repo-root `src/`
- installed artifacts must not read from repo-root `data/`
- Codex packaging should disable implicit invocation for this write-capable skill
- Claude packaging should remain explicit-only
- packaged launchers should keep the public engine contract stable:
  - `run`
  - `doctor`
  - `validate`
  - `apply`
- JSON output remains the authoritative machine-readable launcher contract

## Current Status

This packaging model is planned and documented, but not yet implemented.

Current repo-bound prompt assets must not be described as globally installable self-contained skills.
