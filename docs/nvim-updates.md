# Neovim updates and targeted recovery

Configuration, plugins, parsers and language-server executables have different
update mechanisms. Installed artifacts stay outside Git because they are
machine-local state, not portable dotfiles.

## Normal updates

- After pulling dotfiles, open a fresh Neovim and use `:Lazy restore` to apply
  the plugin commits in `nvim/lazy-lock.json`. Pulling the repository alone does
  not restore installed plugin versions. This is not currently a guarantee of an
  unchanged lockfile on a fresh or incomplete installation; see the
  [bootstrap limitation](#lazy-bootstrap-and-lockfile-limitation) below.
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

## Lazy bootstrap and lockfile limitation

The installer and editor clone the `stable` reference when Lazy is missing and
reuse existing manager directories. The tracked Lazy commit is a separate
selection: currently `306a05526ada86a7b30af95c5cc81ffba93fef97`, not the
`85c7ff3711b730b4030d03144f6db6375044ae82` stable release observed in
[issue #11](https://github.com/luizomf/dotfiles/issues/11).

Lazy setup automatically installs missing plugins **before** the installer's
`Lazy! restore` command runs. That installation restores missing plugins from
the lockfile, but skips an already installed manager. Its final lockfile write
records all installed commits, including the running manager. Consequently it
can replace the tracked manager pin before restore reads it. A repeat restore
then preserves the replacement; it does not recover the original Git version of
the lockfile. With no missing plugins, the isolated probe instead restored the
manager to the original tracked commit.

There is a second, independent difference: Lazy's writer always serializes the
lockfile with one entry per line. The tracked file currently uses expanded
Prettier formatting. Restore can therefore dirty the checkout even when every
commit is unchanged. Do not interpret formatting alone as a plugin upgrade.

An isolated probe using the two manager revisions and one inert local Git plugin
reproduced the startup overwrite and repeat behavior. Selecting the tracked
manager commit before setup prevented semantic drift, but not the formatting
rewrite. This does not verify a full installer or the real plugin set, and no
runtime correction has been applied yet.

A correction needs an explicit manager policy: selecting the lockfile commit
before setup for both new and existing managers changes the earlier
reuse-without-update startup policy; retaining that policy requires a separate
locked-install/restore path that runs before automatic missing-plugin setup.
Neither requires upgrading existing plugin pins. Byte-stable restoration also
needs a formatting policy, such as keeping Lazy's native serialization and
excluding this generated file from Prettier. Do not replace the manager pin with
today's `stable` commit merely to hide the discrepancy: `stable` can move again.
Until this is resolved, inspect and preserve lockfile diffs rather than
publishing bootstrap-generated changes as intentional upgrades.

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
