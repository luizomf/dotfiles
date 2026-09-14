# Staged checks and Git hook

`scripts/check_staged` checks the current repository's staged selection without
calling a model or committing. It is shared by [`commit`](commit.md) and this
checkout's optional `.githooks/pre-commit`.

For a quick pre-commit check, use `commit --check` (see `commit --help`). The
standalone equivalent is:

```sh
scripts/check_staged
```

It explicitly reports when nothing was checked because nothing is staged, and
prints a success summary after the configured checks pass. On failure, the final
message reminds you to fix the reported issue, stage the fix, and rerun
`commit --check`.

It exits successfully when nothing is staged, fails on a failed check or missing
required executable, and refuses files that have both staged and unstaged edits.
It never stages, unstages, restores, or auto-fixes source files. Resolve partial
staging before retrying; the gate does not stash work behind your back.

## Checks and dependencies

The gate runs from the target repository's root. Per-file tools receive only
staged, existing regular files, not symlinks or their resolved targets:

- `git diff --cached --check` for whitespace errors and conflict markers;
- shell syntax with Bash, POSIX shell, Ksh or Zsh, plus ShellCheck for non-Zsh
  sources. Detection uses conventional extensions/startup filenames, shebangs
  (including interpreter arguments), and ShellCheck dialect directives.
  ShellCheck follows sourced files in the checkout without executing them; those
  dependencies may affect results even when they are not staged;
- Ruff lint and formatting when `ruff.toml`, `.ruff.toml`, or a standard
  unquoted `tool.ruff` TOML table is present; table whitespace is accepted;
- whole-project Pyright when `pyrightconfig.json` or an unquoted `tool.pyright`
  table is present. Python deletions, renames out of Python, extensionless
  Python commands, stub files, and root type-config changes also trigger this
  check;
- Prettier for supported documentation, web, and configuration files when a root
  Prettier config or top-level `package.json` `prettier` field exists;
- repository-local ESLint for JavaScript/TypeScript, including `.mjs`, `.cjs`,
  `.mts` and `.cts`, when a recognized root ESLint config file exists;
- repository-local whole-project `tsc --noEmit` for TypeScript or root
  TypeScript config changes, when `tsconfig.json` exists.

Ruff, Pyright, Prettier, ShellCheck and applicable shell interpreters must be
available on the calling process's `PATH`. ESLint and TypeScript use
`node_modules/.bin` in the target repository. Node is needed to inspect Prettier
configuration in `package.json`. No tools are installed or synchronized, and no
package scripts are run.

The deployed checker deliberately does not use the dotfiles development `.venv`.
Tool versions come from these executables, not `uv.lock`; use the
[locked development commands](../development.md#focused-checks) for pinned
manual verification. The installer provisions ShellCheck on all supported
platforms and global Ruff/Pyright/Prettier unless toolchain setup is skipped.
Existing installations may need those tools prepared separately. IDEs and
non-interactive callers must provide their own appropriate `PATH`; the hook does
not source interactive shell startup files. A tool installed under an old NVM
Node version or a Homebrew prefix is not necessarily visible to SSH.

## Activate in this checkout

`git clone` brings the hook files, but Git does not activate them automatically.
After a successful installation, `install.sh` runs `scripts/setup_git_hooks` for
this checkout. You can do the same after a clone/pull without running the full
installer:

```sh
./scripts/setup_git_hooks
commit --help
```

The setup command only changes this checkout's local Git configuration. It
preserves any existing `core.hooksPath` (including inherited configuration) and
any non-sample files in the default hooks directory. Repeated setup is safe; a
preserved custom setup is reported as **not activated**, not silently replaced.
It does not install tools, run checks, change global Git config, or commit.

To inspect activation or resolve a preserved custom setup manually:

```sh
git config --show-origin --get core.hooksPath
```

If it is unset, also inspect `.git/hooks` (or the hooks directory reported by
`git rev-parse --git-path hooks`). Setting `core.hooksPath` replaces the active
hooks directory; it does not compose existing hooks. After preserving any
existing setup, run from the dotfiles root:

```sh
git config --local core.hooksPath .githooks
```

Once activated, normal `git commit`, including commits made by agents and
`commit_dotfiles`, runs the shared checks. The hook itself does not call a model
and does not need `MODEL`. `commit` still checks before calling its model, and
an enabled hook checks again at commit time; there is no skip flag passed
between them.

To undo a newly added setting, use `git config --local --unset core.hooksPath`.
If you replaced a previous local value, restore that value instead. This hook is
for the dotfiles checkout; do not configure it globally for arbitrary projects.
The standalone `check_staged` command can still inspect another repository when
invoked there through its absolute path or the dotfiles scripts `PATH`.

## Limits

This is root-only configuration discovery, not snapshot isolation. Whole-project
type checks and tool configurations use the current checkout. Unstaged or
untracked dependencies can therefore affect results. Concurrent staging or edits
during checks are not isolated. A Git-selected alternate index (for example,
`git commit --only`) still comes from Git, not an index assembled by this
script.

Checkers may create their normal caches or build metadata; `tsc --noEmit` can
still update `.tsbuildinfo` for incremental/composite projects. Project tool
configuration may execute code, so run checks only in trusted repositories.

Missing configuration is reported for recognized Python/JS/TS/Prettier file
families; it is not an error. Other files receive only the Git diff check. There
is no Biome, StyLua, behavior-test runner, secret scanner, query/N+1 detector,
or architectural review here. A passing gate only means the selected checks
passed.

Local hooks are bypassable (`--no-verify`, changed configuration, or edited hook
code). They are workflow guardrails, not a security boundary. Required CI and
branch protection would be a separate remote enforcement decision.
