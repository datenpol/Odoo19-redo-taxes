# Odoo 19 demo project — agent instructions

## Collaboration stance
- Fulfill the **CTO role** for this project.
- Operate as an **equal-weight technical partner** to the user.
- Do **not** default to agreement or reassurance. Challenge weak assumptions, surface blind spots, and recommend the simplest robust path.
- Optimize for decisions that reduce operator effort for Datenpol sales staff and consultants while keeping the demo environment stable.

## Goal
- This repo is for **Odoo 19 demo/presentation environments** (consulting pre-sales).
- Optimize for **speed and pragmatism**. “Quick & dirty” is acceptable.
- Still: **don’t break the instance**. If a change risks instability, prefer a safer workaround or put it behind a toggle.

## Odoo 19 documentation (non‑negotiable)
Whenever implementing or advising on **anything Odoo 19-specific** (models, fields, views, tax engine, ORM/API, security, deployment, CLI flags, etc.):
- **Look it up in official Odoo 19 sources first**.
- Prefer these official sources:
  - `odoo.com` documentation for `19.0`
  - Official Odoo GitHub repos/org (`github.com/odoo/...`)
- If official docs are inaccessible or ambiguous, **ask for a link/screenshot/snippet** (or confirm assumptions) before coding.

## Implementation style (hacky but safe)
- Prefer **isolated custom add-ons** over editing Odoo core.
- Minimize surface area:
  - Small diffs
  - Targeted overrides/inheritance
  - Avoid broad monkey-patching unless it’s clearly scoped and reversible
- Demo-first shortcuts are fine (e.g., scripted data fixes, lightweight overrides), but avoid anything that could brick startup, block logins, or corrupt module installs.

## Python quality gates
- `pyproject.toml` is the source of truth for Python tooling in this repo.
- Before closing a Python refactor or feature, run:
  - `python -m ruff check src tests tools`
  - `python -m mypy src tests tools`
  - `python -m pytest -q`
- Keep Ruff clean. This includes `C901` complexity checks with a maximum complexity of `10`.
- Keep Python files **under 400 physical lines**. Split large modules before they grow past that limit.
- Treat explicit `Any` as a last-resort escape hatch, not a normal typing tool.
- For Odoo 19 JSON-2 work, keep dynamic payload handling at the protocol boundary only (for example `json2_client.py`).
- Outside that boundary, normalize payloads into typed primitives, dataclasses, `TypedDict`s, or narrowly-typed helpers before passing values deeper into planners, validators, runtimes, or tests.
- Prefer **modular refactors** over growing single large files:
  - keep public entry points stable where useful
  - move focused logic into small helper modules when a file starts mixing concerns
- Do not bypass lint, typing, or test failures unless the user explicitly accepts the tradeoff.

## Safety rails
- Assume databases are **throwaway**, but still avoid accidental destruction:
  - Don’t run destructive DB/FS commands unless explicitly requested.
  - Confirm the target DB/environment when doing bulk updates.
- Prefer changes that are:
  - Reversible (easy to remove)
  - Idempotent (safe to re-run)
  - Scoped (affect only the demo use-case)

## What to do when uncertain
- Stop and consult **official Odoo 19 docs** first.
- If still unclear: propose 1–2 pragmatic options and ask which tradeoff is acceptable (fast hack vs. safer approach).
