# Development tools

Python feedback tools are declared in `pyproject.toml` and locked in `uv.lock`.
This environment is for maintaining the dotfiles; installed scripts must keep
their own runtime interpreter contracts.

The installer syncs the checkout's ignored `.venv` from the lockfile. Set
`OM_INSTALL_SKIP_TOOLCHAINS=1` to skip that step. For an existing checkout, use
Python 3.10 or newer and run:

```sh
uv sync --locked
```

This is a dedicated environment, so sync may remove undeclared packages. Do not
put `.venv` on the global PATH or use it from installed scripts, tmux hooks,
Queue payloads, or host maintenance.

## Focused checks

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

Ruff and Pyright are diagnostics, not substitutes for behavior tests. Existing
code has known diagnostics and formatting differences; compare affected files
before and after a change instead of hiding warnings with casts or broad ignores.

Extensionless Python commands are listed in `pyproject.toml`. Update both tool
lists when adding one. Python-version overrides should follow known runtime
requirements rather than the developer's current shell.

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
