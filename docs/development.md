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

- In this repository, Python uses Ruff settings from `pyproject.toml`. Neovim
  prefers the nearest `.venv/bin/ruff`, then falls back to Ruff on PATH.
- This repository's `.prettierrc.json` links to
  `nvim/config_files/prettierrc.json`.
- This repository's `.stylua.toml` links to `nvim/config_files/stylua.toml`.

Do not duplicate these settings or add a Node toolchain only for formatting.
After changing Conform configuration, open a new Neovim session and use
`:ConformInfo` to inspect the selected formatter. Format changed files only and
keep large format-only migrations separate from functional work.

## Neovim project-first formatting

Project configuration takes precedence over personal defaults. Discovery starts
at the edited file's directory, not just Neovim's current working directory.

- Prettier and StyLua use Conform's built-in configuration discovery, including
  parent directories. Prettier also supports configuration in `package.json`. An
  ancestor `.editorconfig` leaves configuration resolution to the formatter
  rather than forcing the personal preset.
- If neither a tool-specific project configuration nor `.editorconfig` is found,
  Prettier and StyLua use their respective presets under Neovim's
  `config_files/` directory. A discovered but invalid tool configuration is not
  silently replaced by the personal preset.
- Prettier prefers `node_modules/.bin/prettier` before PATH. Astro follows the
  same configuration policy; its Prettier plugin must still be installed and
  configured in the project. No plugins are installed by this fallback logic.
- Ruff retains its native configuration discovery for both fixes and formatting.
  Taplo runs from the nearest `.taplo.toml` / `taplo.toml` directory, or the
  edited file's directory when neither exists. No personal presets are imposed
  on these tools.
- Lint/type-check servers retain their tool-specific project configuration
  mechanisms; this is not a universal configuration format or a replacement for
  server settings.

Run the integration check from the repository root:

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_formatting.lua
```

This requires an installed Conform plugin plus Prettier, StyLua, Ruff and Taplo
(on PATH or, except Prettier, in Mason's bin directory). It formats in-memory
buffers using temporary project configurations, checks personal fallbacks and
invalid-config errors, and removes its fixtures on exit. It installs nothing and
does not save changes to project files.

## Neovim LSP formatting fallback checks

Saving and `<leader>f` use Conform formatters first, falling back to a capable
LSP formatter only when no Conform formatter is available. This does not start
or install a server, and does not retry formatter errors through LSP.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_lsp_formatting.lua
```

Run from the repository root with Conform installed. The test uses an in-process
LSP fixture, a Lua Conform formatter, and temporary files to exercise real saves
and the manual mapping. It checks fallback and provider priority without
launching language-server or formatter executables, and removes its fixtures on
exit.

## Neovim Ruff executable selection checks

When starting the Ruff LSP, search the workspace root and its ancestors for the
nearest executable `.venv/bin/ruff`. If none exists, or no workspace root is
available, use `ruff` from the existing PATH (normally supplied by Mason). The
process still receives the configured working directory, environment and
detachment options. No global PATH or other language-server policy is changed.

Conform already uses this upward-search policy from the buffer's directory; the
LSP starts from its workspace root. Nested environments below that root can
therefore differ. Selection happens when a client starts: an already running
client is not automatically restarted after changing the environment. A selected
project Ruff must support `ruff server`; startup failures do not silently select
a different version.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_ruff_command.lua
```

Requires installed nvim-lspconfig and Conform. The test uses temporary
executable fixtures, compares both configured command selectors, and intercepts
the LSP process-launch boundary. It covers ancestor selection, non-executable
candidates, PATH fallback, separate roots and preserved launch options. Mason
setup and LSP enabling are disabled in the fixture; no Ruff process or download
is started.

## Neovim snippet navigation checks

The completion menu keeps priority for Tab/Shift-Tab. Otherwise, LuaSnip's
local-jump predicates avoid returning to a departed snippet, while Tab can still
expand a new snippet at the cursor. The installed LuaSnip checks whether the
cursor is on a line occupied by the snippet; this is not a column-exact
boundary. Other completion mappings and Enter selection are unchanged.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_snippet_navigation.lua
```

Requires installed nvim-cmp and LuaSnip. The test invokes the configured mapping
callbacks with real LuaSnip state, covering LSP-style placeholder navigation,
fallback outside the snippet's lines and expansion of a new snippet. It uses no
LSP or external completion sources and writes no files. Interactive key handling
and completion-menu appearance should be checked in a normal editor separately.

## Neovim indentation checks

Tree-sitter indentation is enabled only when its highlighting startup succeeds
and a usable indentation query exists for the buffer's language. Otherwise the
filetype's native indentation is left intact. This does not change spacing
options: native EditorConfig support still applies project settings, and
`settings/vim.lua` supplies the existing two-space, expand-tabs defaults.
Formatter configuration discovery is separate and remains unchanged; editing
indentation does not independently interpret Prettier or `pyproject.toml`.

Keep syntax activation in Neovim's normal startup sequence. An early `syntax on`
in core settings can load a command-line Lua buffer before Lazy has registered
Tree-sitter and the native EditorConfig handler, bypassing both for that initial
file. No extra syntax-enabling command is needed here.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_indentation.lua
nvim --clean --headless -i NONE -l tests/test_nvim_startup_indentation.lua
```

Requires installed nvim-treesitter plus its Lua parser and indentation query.
The test uses real filetype events, temporary native indent scripts, `=` and
EditorConfig, checking missing-parser/query fallbacks and supported indentation
with project spacing. The startup check additionally requires Lazy and opens a
Lua file from the command line in a child Neovim process. It runs the real init
sequence but restricts Lazy to the installed Tree-sitter plugin to avoid
unrelated session/server effects. Neither test installs anything or runs a
formatter or language server.

## Neovim Telescope search checks

See [Telescope file search](nvim-telescope.md) for the hidden-file/ignore policy
and the isolated `tests/test_nvim_telescope_search.lua` check. It requires
installed Telescope, Plenary and ripgrep, and uses only synthetic files.

## Neovim Lazy bootstrap checks

When the editor's initial Lazy clone fails, `nvim/init.lua` reports the target
path, Git exit status and captured output instead of proceeding into plugin
setup. Neovim may remain open without the rest of the custom initialization. No
automatic retry or deletion is performed; inspect any partial clone before
retrying. An existing installation is still reused.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_bootstrap.lua
```

This runs the real init file with isolated XDG directories and a failing Git
fixture. A minimal Lazy fixture also checks continuation with an existing
installation. It performs no downloads, loads no installed plugins, removes its
temporary files on exit, and does not exercise or change `install.sh`.

## Neovim notification command checks

`:Notify [message] [level] [timeout]` accepts case-insensitive level names
(`TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`, `OFF`) or their numeric values
(`0`–`5`). Invalid levels report an error instead of displaying the requested
message. Defaults remain `NO MESSAGE`, `INFO` and 2000 ms. Ex-escaped spaces
still work: `:Notify hello\ world warn 3500`. Notification visibility remains up
to the configured notification provider, especially for `TRACE` and `OFF`.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_notify.lua
```

This exercises the real command while capturing the public `vim.notify` output.
It checks severity normalization, invalid input and unchanged defaults/message
handling without loading plugins or writing files. Check notification appearance
in a normal editor separately.

## Neovim rename checks

`:Rename` saves the current contents under the requested name before deleting
only the original file, without a shell. Existing destinations remain protected
by `:saveas`. If deletion fails, the saved destination is retained and an error
identifies it, the original path and the filesystem error; no automatic retry or
rollback is attempted. Existing Ex filename argument handling is unchanged.

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_rename.lua
```

Run from the repository root. This uses the real command and temporary files,
without plugins. It checks original filenames containing spaces, quotes, UTF-8,
`%`, `#` and `!`, preservation of unsaved edits, overwrite protection and denied
deletion. The permission-denial case is explicitly skipped if directory
permissions cannot restrict the running user (for example, root). Fixtures and
permissions are cleaned up on success and failure.

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
