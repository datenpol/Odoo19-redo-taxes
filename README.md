# Datenpol Euro Demo Skill

This repository is the development surface for the `datenpol-euro-demo` Codex skill and the shared Python runtime behind it.

The install target is a global Codex skill. After installation, the skill runs from its own installed folder and does not need this repository checkout anymore.

## What This Repo Ships

- one public Codex install boundary: `skills/datenpol-euro-demo/`
- one packaged Claude artifact for manual copying: `dist/claude/datenpol-euro-demo/`
- one canonical Python runtime source tree: `src/odoo_demo_austria/`
- one canonical mapping spec source: `data/austria-cosmetic-mapping-spec.draft.yaml`

The generated skill bundles its own launcher, runtime package, packaged JSON spec, and reference snapshot.

## Install In Codex

User-facing install request in Codex:

```text
$skill-installer https://github.com/dmulec-dp/Odoo19-redo-taxes
```

Public install boundary in this repo:

- `skills/datenpol-euro-demo/`

Equivalent direct helper invocation:

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
py -3 (Join-Path $codexHome "skills\.system\skill-installer\scripts\install-skill-from-github.py") --repo dmulec-dp/Odoo19-redo-taxes --path skills/datenpol-euro-demo
```

After install, restart Codex to pick up the new skill.

## Use

Primary operator path:

```text
$datenpol-euro-demo URL API_KEY
```

Read-only diagnosis:

```text
$datenpol-euro-demo doctor URL API_KEY
$datenpol-euro-demo validate URL API_KEY
```

Apply-only path:

```text
$datenpol-euro-demo apply URL API_KEY
```

Interpreter preference inside the installed skill:

- Windows: `py -3`
- macOS and Linux: `python3`
- fall back to `python` only if the preferred launcher is unavailable

## Development

Regenerate packaged artifacts after changing runtime code or skill templates:

```powershell
python tools/build_datenpol_euro_demo_skill.py
```

Run the repository quality gates:

```powershell
python -m ruff check src tests tools
python -m mypy src tests tools
python -m pytest -q
```

The live GitHub installer smoke test is opt-in because it targets the published GitHub ref, not your unpushed local worktree:

```powershell
$env:RUN_GITHUB_INSTALL_TEST = "1"
python -m pytest -q tests/test_skill_github_install.py
```

## Notes

- The repo keeps `skill_src/datenpol-euro-demo/` as editable source and writes generated artifacts into `skills/` and `dist/`.
- The installed skill stays cosmetic-only and routes all business logic through the packaged Python runtime.
- Odoo 19 JSON-2 commits each API call separately, so if `run` fails after writes start, rerun the same `run` command once before changing data or code.
