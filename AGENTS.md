# Odoo 19 demo project — agent instructions

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
