# Dotfiles

Personal dotfiles, bootstrap automation, and standalone utilities for macOS,
Ubuntu, and traditional Fedora/Asahi—not a unified application or framework.
Preserve personal preferences and keep changes focused on the requested task.

## Working style

- Keep going while the next step is clear and within scope. Ask when missing
  information blocks progress or an action has destructive consequences the user
  has not already authorized. No mandatory planning or orchestration flow.
- Prefer code that is easy to understand and maintain. Add abstractions,
  dependencies, or shared helpers only when they solve a concrete current need.
- Do not grow this file with task history, obvious advice, or speculative rules.
  Put lasting technical details in `docs/`, preferably beside existing guidance.

## Real safety boundaries

- Tracked files and commits are public. Keep secrets, private host details,
  credentials, sessions, logs, and machine-local state out of Git. `pi/agent/`
  contains static configuration only.
- Deployed configs are often symlinks into this checkout: edits can affect the
  live environment immediately. Check affected consumers before changing paths,
  arguments, defaults, or environment-variable contracts.
- Never run `install.sh` as a check. Do not trigger sync, upload, SSH, queue,
  remote changes, or live reloads merely to validate code; those effects need
  task authorization. Prefer isolated checks.
- Preserve unrelated work. Clean up only task-owned temporary artifacts,
  processes, branches, and worktrees; preserve their useful work first.

## Repository conventions

- `README.md` covers installation and safety; `docs/` holds maintenance details.
  Correct affected documentation when changing behavior.
- `config/paths.sh` owns shared host paths. Preserve supported `OM_PATHS_FILE`
  overrides, platform compatibility, interpreter contracts, executable bits, and
  unattended execution requirements. Prefer `$HOME` and existing path variables
  over machine-specific absolute paths.
- Keep persistent scratch notes in `./.scratch/`, never in commits.
- Create worktrees under `~/sannux-data/worktrees/<repo>/<worktree_name>`.

## Checks and delivery

- Use focused syntax and behavior checks. For complex or risky behavior, use
  test-first development and test observable outcomes. Simple wrappers and
  static configuration do not need tests just for coverage.
- Format changed files with existing settings: `pyproject.toml` for Python,
  `.prettierrc.json` for Prettier, `.stylua.toml` for Lua. No unrelated cleanup.
- For Python, run Ruff lint/format checks and Pyright on affected files with
  `uv run --locked`; see [development tools](docs/development.md). Report
  pre-existing diagnostics instead of hiding them. `.venv` is for development,
  never a deployed runtime dependency. Register new extensionless Python
  commands in both discovery lists in `pyproject.toml`.
- For `scripts/bq` changes, run `python3 -m unittest tests/test_bq.py`.
- Review the diff for correctness and public-data safety. Commit and push the
  task's changes to the intended branch unless asked otherwise. Report checks
  run, blockers, and any required restart or migration; do not silently apply
  it.
