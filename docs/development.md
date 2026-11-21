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

The [`check_staged` gate](scripts/check_staged.md) runs the non-fixing checks
shared by [`commit`](scripts/commit.md) and the optional Git hook, using tools
on PATH. For locked manual checks on changed files:

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

## Neovim behavior and checks

Run each check from the repository root. They use temporary fixtures and install
nothing; most need the named plugins already installed.

### Project-first formatting

Project configuration wins over personal defaults, searched from the edited
file's directory upward. Prettier and StyLua use Conform's configuration
discovery (Prettier also reads `package.json`); an ancestor `.editorconfig`
leaves resolution to the formatter. With neither, they fall back to the presets
in Neovim's `config_files/`. An invalid project configuration is reported, not
replaced by the preset. Prettier prefers `node_modules/.bin/prettier`. Ruff
keeps its native discovery, and Taplo runs from the nearest `.taplo.toml` /
`taplo.toml` directory.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_formatting.lua
```

Needs Conform, Prettier, StyLua, Ruff, and Taplo.

### LSP formatting fallback

Saving and `<leader>f` use Conform first and fall back to an LSP formatter only
when no Conform formatter is available. Formatter errors are not retried through
LSP.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_lsp_formatting.lua
```

### TypeScript server selection

Each TypeScript workspace uses exactly one server: project TypeScript 7+ (found
in the nearest `node_modules/typescript` from the workspace root upward) selects
its own `node_modules/.bin/tsc --lsp --stdio`; older or missing TypeScript uses
`ts_ls` from Mason. A broken native installation is reported, not silently
replaced. Reopen Neovim after changing the project's TypeScript version.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_typescript.lua
```

### Ruff executable selection

The Ruff LSP uses the nearest executable `.venv/bin/ruff` from the workspace
root upward, otherwise `ruff` on PATH (normally Mason's). Selection happens when
the client starts; restart it after changing the environment. A project Ruff
must support `ruff server`.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_ruff_command.lua
```

### TOML

Taplo is enabled through the shared LSP setup with nvim-lspconfig's defaults; no
custom schema associations are set. Conform stays the primary formatter.

### Snippet navigation

The completion menu keeps priority for Tab/Shift-Tab. Otherwise, Tab jumps
within the active snippet only while the cursor is on one of its lines, and can
still expand a new snippet.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_snippet_navigation.lua
```

### Indentation

Tree-sitter indentation is enabled only when highlighting starts and the
language has an indentation query; otherwise the filetype's native indentation
stays. Spacing comes from EditorConfig and the two-space defaults in
`settings/vim.lua`. Do not add an early `syntax on` to core settings: it loads a
command-line file before Lazy registers Tree-sitter and EditorConfig.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_indentation.lua
nvim --clean --headless -i NONE -l tests/test_nvim_startup_indentation.lua
```

### Lazy bootstrap

A missing Lazy checkout is cloned from `stable` at
`stdpath("data")/lazy/lazy.nvim` (respecting `XDG_DATA_HOME` and
`NVIM_APPNAME`); an existing one is reused. The installer then runs the
[locked restore](nvim-updates.md#locked-plugin-restoration) to apply the tracked
pins. If the initial clone fails, `nvim/init.lua` reports the path, Git exit
status, and output instead of continuing into plugin setup; inspect any partial
clone before retrying.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_bootstrap.lua
```

### Session preferences

`plugins/session.lua` sets only eager loading, branch-based session names, the
suppressed directories, and the Telescope picker; everything else uses
AutoSession's defaults. Review those defaults when updating the plugin's pin.

### Commands and mappings

- `:Notify [message] [level] [timeout]` accepts level names (`TRACE` … `OFF`,
  case-insensitive) or `0`–`5`; invalid levels report an error. Defaults:
  `NO MESSAGE`, `INFO`, 2000 ms. Escape spaces:
  `:Notify hello\ world warn 3500`.
- `:Rename` saves under the new name, then deletes only the original, without a
  shell. Existing destinations are protected by `:saveas`; if deletion fails,
  the new file is kept and the error names both paths.
- Visual wrapping mappings and `:WrapIn` wrap the selection in delimiters.
- Spelling and trailing-whitespace markers apply only to normal, modifiable,
  writable buffers outside preview windows (not scratch buffers, diagnostic
  popups, or plugin UI). Visiting a read-only buffer keeps a manual `nospell`.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_notify.lua
nvim --clean --headless -i NONE -l tests/test_nvim_rename.lua
nvim --clean --headless -i NONE -l tests/test_nvim_wrap.lua
nvim --clean --headless -i NONE -l tests/test_nvim_editing_highlights.lua
```

See also [Neovim updates](nvim-updates.md) and
[Telescope file search](nvim-telescope.md).
