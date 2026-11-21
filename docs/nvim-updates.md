# Neovim updates and targeted recovery

Configuration, plugins, parsers, and language-server executables update through
different mechanisms. Installed artifacts stay outside Git.

## Normal updates

- After pulling dotfiles, run the [locked restore](#locked-plugin-restoration)
  to apply `nvim/lazy-lock.json`. Pulling alone does not change installed plugin
  versions.
- `:Lazy update` upgrades plugins beyond the lockfile; review the lockfile diff
  before committing it.
- The Tree-sitter build installs missing configured parsers (including the
  custom tmux parser), then updates installed ones, failing on errors or after a
  ten-minute limit per phase. Lazy runs it only when the plugin needs a build;
  run `:Lazy build nvim-treesitter` to sync parsers explicitly. `:TSUpdate` is
  asynchronous: wait for its messages and check `:TSLog` on errors.
- `:MasonUpdate` refreshes registries, **not installed tools**. In `:Mason`, `C`
  checks outdated packages, `u` updates the selected one, `U` updates all. The
  bootstrap installs missing tools but never upgrades existing ones.
- Project dependencies (native TypeScript, project-local Ruff) belong to the
  project's package manager.

Restart Neovim after updates; loaded modules, parsers, and LSP clients do not
reload by themselves. Do not run overlapping update commands.

## Locked plugin restoration

Close other Neovim sessions, then run:

```sh
cd ~/dotfiles
nvim --clean --headless -i NONE -l ./nvim/restore.lua
```

This bootstraps a missing Lazy from `stable`, installs missing plugins, and
restores every configured Git plugin to its tracked commit, including Lazy's own
pin. The lockfile is never rewritten. Invalid locks, spec errors, unpinned
plugins, and failed restores exit nonzero; local plugin edits are not discarded.
A failure can leave some checkouts restored, so fix the reported cause and rerun
instead of deleting user data.

Do not use `nvim --headless '+Lazy! restore' +qa`: normal startup installs
missing plugins and then rewrites the lockfile with every installed revision
before restore reads it
([issue #11](https://github.com/luizomf/dotfiles/issues/11)). `restore.lua`
suppresses the lockfile writer through Lazy's internal `manage.lock.update` API,
so recheck its test when updating Lazy.

The lockfile uses Lazy's native one-entry-per-line format and is excluded from
Prettier; do not reformat it.

## When an update fails

Read the failed Lazy task and `:TSLog` before retrying. Force-reinstall one
confirmed broken parser with `:TSInstall! typescript` (substitute the language),
and reinstall a broken Mason tool from its UI.

Do not delete the Neovim data directory as an update strategy: it holds spelling
additions, sessions, and unrelated tools. Old plugin-local parser files can
coexist with `site/parser`; check which one loads with
`:lua =vim.api.nvim_get_runtime_file('parser/typescript.so', true)` (the first
result wins).

## Verification

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_locked_restore.lua
nvim --clean --headless -i NONE -l tests/test_nvim_treesitter_update.lua
```

The locked-restore test needs the Lazy revisions named in the test available
locally and downloads nothing. The Tree-sitter test needs nvim-treesitter.
