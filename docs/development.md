# Development tools

Python feedback tools are declared in `pyproject.toml` and locked in `uv.lock`.
This environment is for maintaining the dotfiles; installed scripts keep their
own runtime interpreter contracts. Prefer Bash for new operational scripts,
without hidden Zsh or interactive-shell dependencies, and keep Bash 3.2
compatibility where a script's contract requires it.

The installer syncs the checkout's ignored `.venv` from the lockfile
(`OM_INSTALL_SKIP_TOOLCHAINS=1` skips it). Alpine and LFS use the native
`/usr/bin/python3` with managed Python downloads disabled; on LFS, standalone uv
supplies Pyright, mypy, and Ruff through `uv tool install`, so `updateall` can
update them. If Python setup fails, the installer continues the other steps and
exits nonzero, reporting the failed operation.

Manual recovery, with Python 3.10 or newer:

```sh
uv sync --locked
```

Sync may remove undeclared packages. Do not put `.venv` on the global PATH or
use it from installed scripts, tmux hooks, queue jobs, or host maintenance.

## Focused checks

`scripts/check_staged` runs the non-fixing checks shared by `commit` and the
optional Git hook (`scripts/setup_git_hooks` activates it), using tools on PATH.
For locked manual checks on changed files:

```sh
uv run --locked ruff check --no-fix path/to/file.py
uv run --locked ruff format --check path/to/file.py
uv run --locked pyright path/to/file.py
```

Drop the paths (and add `--statistics` to `ruff check`) for a read-only
overview.

Ruff selects `ALL` except docstrings (`D`), `print` (`T201`), and `COM812`
(conflicts with the formatter). Tests also ignore `ANN201` and `S101`, and keep
unittest style by ignoring `PT009` and `PT027`. Pyright runs in `strict` mode
without requiring third-party stubs. Plain Ruff checks never apply fixes, but
Neovim's `ruff_fix` save step applies safe fixes, so review the diff after
saving Python files. Do not hide diagnostics with casts or broad ignores, and
avoid unrelated bulk fixes in legacy code.

Extensionless Python commands are listed in both discovery lists in
`pyproject.toml`. Set their Python-version overrides from the command's runtime
requirements, not from the development shell.

## Formatting

- Python uses Ruff settings from `pyproject.toml`. Neovim prefers the nearest
  `.venv/bin/ruff`, then Ruff on PATH.
- `.prettierrc.json` links to `nvim/config_files/prettierrc.json`.
- `.stylua.toml` links to `nvim/config_files/stylua.toml`.

Do not duplicate these settings or add a Node toolchain only for formatting.
Format changed files only, and keep large format-only migrations separate from
functional work. After changing Conform configuration, check `:ConformInfo` in a
new Neovim session.

## Neovim checks

Each `tests/test_nvim_*.lua` runs from the repository root with temporary
fixtures and installs nothing (most need the named plugins installed):

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_formatting.lua
```

Two rules the code does not make obvious:

- Do not add an early `syntax on` to core settings: it loads a command-line file
  before Lazy registers Tree-sitter and EditorConfig.
- Update plugins and restore pins as described in
  [Neovim updates](nvim-updates.md), never with a plain `Lazy restore`.
