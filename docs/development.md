# Development tools

Python feedback tools are declared in `pyproject.toml` and locked in `uv.lock`.
This environment is for maintaining the dotfiles; installed scripts must keep
their own runtime interpreter contracts. Prefer Bash for new operational scripts
without hidden Zsh or interactive-shell dependencies. Preserve existing POSIX
shell scripts and Bash 3.2 compatibility where their current contracts require
it.

The installer syncs the checkout's ignored `.venv` from the lockfile. Set
`OM_INSTALL_SKIP_TOOLCHAINS=1` to skip that step. For an existing checkout, use
Python 3.10 or newer and run:

```sh
uv sync --locked
```

This is a dedicated environment, so sync may remove undeclared packages. Do not
put `.venv` on the global PATH or use it from installed scripts, tmux hooks,
queue jobs, or host-maintenance commands.

## Focused checks

The [`commit` staged-check gate](scripts/commit.md) documents the read-only
mechanical checks run before its local model is called.

Run checks only on files being changed:

```sh
uv run --locked ruff check --no-fix path/to/file.py
uv run --locked ruff format --check path/to/file.py
uv run --locked pyright path/to/file.py
```

For a read-only overview:

```sh
uv run --locked ruff check --statistics
uv run --locked ruff format --check
uv run --locked pyright
```

Ruff selects `ALL` except docstrings (`D`), `print` calls (`T201`), and
`COM812`, which conflicts with the Ruff formatter. Tests also ignore `ANN201`
and `S101` and retain their unittest style by ignoring `PT009` and `PT027`.
Pyright uses `strict` mode without requiring third-party type stubs.
Extensionless command discovery and Python-version overrides are configured
separately from lint rule selection.

Ruff and Pyright provide diagnostics, not behavior tests. Existing code may have
diagnostics or formatting differences; review affected files before and after
changes and avoid hiding warnings with casts or broad ignores. Plain Ruff checks
do not apply fixes (`fix = false`, `unsafe-fixes = false`). Neovim's explicit
`ruff_fix` save step can still apply safe fixes, so review the diff after saving
Python files under the expanded rules. Avoid unrelated bulk fixes when updating
legacy code.

Extensionless Python commands are listed in `pyproject.toml`. Update both tool
lists when adding one. Set Python-version overrides from the command's runtime
requirements, not from the development shell.

## Formatting

- Python uses Ruff settings from `pyproject.toml`. Neovim prefers the nearest
  `.venv/bin/ruff`, then falls back to Ruff on PATH.
- Prettier-supported files use `.prettierrc.json`, linked to
  `nvim/config_files/prettierrc.json`.
- Lua uses `.stylua.toml`, linked to `nvim/config_files/stylua.toml`.

Do not duplicate these settings or add a Node toolchain only for formatting.
After changing Conform configuration, open a new Neovim session and use
`:ConformInfo` to inspect the selected formatter. Format changed files only and
keep large format-only migrations separate from functional work.
