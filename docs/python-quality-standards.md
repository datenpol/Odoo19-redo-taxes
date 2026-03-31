# Python Quality Standards

## Source of truth

Python quality tooling is configured in `pyproject.toml`.

The current project standards are:

- `ruff` for linting and complexity checks
- `mypy` for static typing
- `pytest` for the test suite and structural guardrails

## Required checks

Run these commands before handing off Python changes:

```powershell
python -m ruff check src tests tools
python -m mypy src tests tools
python -m pytest -q
```

## Ruff and complexity

- Keep Ruff clean for `src`, `tests`, and `tools`.
- `C901` complexity is enforced through Ruff.
- Maximum allowed function complexity is `10`.

If a function starts pushing against the complexity budget, split responsibilities instead of adding ignores.

## Mypy

- Keep mypy clean for `src`, `tests`, and `tools`.
- New Python code should be typed enough to pass repository mypy settings without local exceptions.
- Prefer fixing uncertain types at the module boundary instead of suppressing errors downstream.
- Do not introduce explicit `Any` in normal application code.
- Acceptable exception: raw protocol-boundary code that deserializes untyped external payloads, such as Odoo JSON-2 transport helpers.
- Even at that boundary, convert external payloads into typed primitives, dataclasses, `TypedDict`s, or small focused helper return types as early as possible.
- Planners, validators, runtime orchestration, and business-rule helpers should consume typed values, not `dict[str, Any]` records passed through unchanged.

## Pytest

- `pytest` is the standard test runner for this repo.
- Tests live under `tests/`.
- The repo is configured so `src/` is on the test import path.

Use pytest even when the tests themselves are written with `unittest` style classes.

## File size and modularity

- Every Python file in `src`, `tests`, and `tools` must stay at or below `400` physical lines.
- This limit is enforced by the test suite.
- When a file starts approaching the limit, split it into focused helper modules instead of letting it grow.

Preferred pattern:

- keep a thin public facade module when external imports should stay stable
- move implementation details into smaller private helper modules
- group code by concern, not by chronology

## Refactor expectation

Refactors should leave the codebase easier to extend than before:

- avoid monolithic “do everything” modules
- separate builders, loaders, validators, helpers, and entry points where it improves clarity
- preserve behavior first, then improve structure in small steps
