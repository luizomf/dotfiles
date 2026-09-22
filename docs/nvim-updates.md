# Neovim updates and targeted recovery

Configuration, plugins, parsers and language-server executables have different
update mechanisms. Installed artifacts stay outside Git because they are
machine-local state, not portable dotfiles.

## Normal updates

- After pulling dotfiles, open a fresh Neovim and use `:Lazy restore` to apply
  the plugin commits in `nvim/lazy-lock.json`. Pulling the repository alone does
  not restore installed plugin versions.
- Use `:Lazy update` when intentionally upgrading plugins beyond the current
  lockfile. Review the resulting lockfile changes before publishing them.
- The Tree-sitter build loads its configuration (including the custom tmux
  parser), waits for missing configured parsers to install, then waits for
  installed supported parsers to update. Each phase has a ten-minute wait limit;
  unsuccessful results, task exceptions and timeouts fail the build rather than
  being reported as completed work. The installer uses the same synchronization.
- Lazy runs the build when that plugin needs it, not on every startup or every
  unrelated plugin update. To synchronize parsers explicitly, including after a
  custom parser revision changes without a plugin update, run
  `:Lazy build nvim-treesitter`. No plugin checkout update is needed for this
  command. The native `:TSUpdate` command remains asynchronous: wait for its
  completion messages and inspect `:TSLog` on errors.
- Mason is separate: `:MasonUpdate` refreshes registries, **not installed tool
  versions**. In `:Mason`, `C` checks outdated packages, `u` updates/reinstalls
  the selected package, and `U` updates all installed packages. Prefer a
  targeted update when diagnosing one server. The bootstrap installs missing
  Mason tools; it does not upgrade every installed executable. Lazy's lockfile
  does not pin Mason package versions or project dependencies.
- Project dependencies (including native TypeScript and project-local Ruff)
  belong to that project's package manager. See the TypeScript/Ruff sections of
  [development.md](development.md) for executable selection.

Restart Neovim after plugin/parser updates. Already loaded Lua modules, parser
libraries and LSP clients need not change just because files on disk changed. Do
not start overlapping update commands or quit while work is still running.

## When an update fails

Read the failed Lazy task and `:TSLog` before retrying. A download, compiler or
ABI error requires addressing its reported cause; waiting correctly cannot
repair every installation. A timeout can leave background work still finishing.

For a confirmed broken parser, `:TSInstall! typescript` force-reinstalls only
that parser; substitute the affected language, such as `tsx`. This is an
explicit repair operation, not a default startup action. Restart afterward and
retest. For a broken Mason tool, update/reinstall that package from its UI
instead.

Do not delete the entire Neovim data directory as an update strategy: it can
contain personal spelling additions, saved sessions and unrelated tools. Legacy
plugin-local parser files can coexist with current `site/parser` files; check
runtime selection before assuming they are active or deleting them. For example,
inspect `:lua =vim.api.nvim_get_runtime_file('parser/typescript.so', true)`. The
first candidate is the normal parser lookup winner; duplicate files alone are
not evidence that the stale one is loaded.

## Verification

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_treesitter_update.lua
```

Requires installed nvim-treesitter. This checks the configured Lazy build and
installer entry point using real Tree-sitter async tasks and a synthetic
backend. It verifies waiting, failed results, exceptions and installer failure
exits without downloads, compilation, Mason operations or loading real parser
binaries. It does not reproduce the maintainer's historical incident or prove
every parser is current.
