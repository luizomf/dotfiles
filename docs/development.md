# Development tools

Python feedback tools are declared in `pyproject.toml` and locked in `uv.lock`.
This environment is for maintaining the dotfiles; installed scripts must keep
their own runtime interpreter contracts. Prefer Bash for new operational scripts
without hidden Zsh or interactive-shell dependencies. Preserve existing POSIX
shell scripts and Bash 3.2 compatibility where their current contracts require
it.

The installer syncs the checkout's ignored `.venv` from the lockfile. Set
`OM_INSTALL_SKIP_TOOLCHAINS=1` to skip that step.

Python setup is recoverable: if pyenv, uv, tool installation, or sync fails, the
installer continues independent configuration and reports an incomplete
installation with a nonzero exit status. Later steps in that Python setup group
and its final checks are skipped, so `.venv`, Ruff, or Pyright may be
unavailable. The original command error remains in the terminal output; the
final summary identifies the operation and exit code. Other installer failures
remain fatal.

For manual recovery of the development environment, use Python 3.10 or newer and
run:

```sh
uv sync --locked
```

This is a dedicated environment, so sync may remove undeclared packages. Do not
put `.venv` on the global PATH or use it from installed scripts, tmux hooks,
queue jobs, or host-maintenance commands.

## Focused checks

The [`check_staged` gate](scripts/check_staged.md) documents the non-fixing
mechanical checks shared by [`commit`](scripts/commit.md) and the optional Git
hook. Deployed checks use tools on PATH rather than the development `.venv`; the
commands below provide locked manual verification.

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

## Neovim selection-wrapping checks

Run from the repository root:

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_wrap.lua
```

This uses scratch buffers and the real visual mappings and `:WrapIn` command; it
does not load the plugin manager or write edited files. It covers single
characters (including UTF-8), end-of-line and multiline selections, empty lines,
custom delimiters, and a missing selection. The checks use Neovim's default
inclusive selection mode, not blockwise or exclusive selections.

## Neovim editing-highlight checks

Spelling and redundant-whitespace markers apply to normal, modifiable, writable
buffers outside preview windows. Special buffers (including editable `nofile`
scratch buffers), diagnostic popups and plugin UI are excluded. The same
eligibility rule is shared by both features. Suppressing spelling preserves the
window's previous setting so visiting a read-only buffer does not undo a manual
`nospell` choice.

Run from the repository root:

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_editing_highlights.lua
```

The test uses a real diagnostic popup, buffer/window option changes and splits.
It does not load external plugins or write files. Check Telescope visually in a
normal editor session after changing this behaviour.
