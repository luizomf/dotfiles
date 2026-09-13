# Staged commit checks

`scripts/commit` commits an explicitly staged selection with the configured
local model. Stage the intended files yourself, then run:

```sh
git add path/to/file
commit
```

The command never stages, unstages, restores, or edits files. It exits before
calling the model when nothing is staged, when a staged file also has unstaged
edits, or when a check fails. Resolve partial staging before trying again so
per-file checks inspect the same content that was selected for the commit.

## Checks

The gate runs from the repository root and checks only staged, existing files
when passing paths to per-file tools:

- `git diff --cached --check` for whitespace errors and conflict markers;
- shell syntax using the source's Bash, POSIX shell, or Zsh dialect, followed by
  ShellCheck for Bash and POSIX shell sources;
- Ruff lint and formatting through `uv run --locked --no-sync` when Ruff is
  configured;
- whole-project Pyright through `uv run --locked --no-sync` when Pyright is
  configured, including after staged Python deletions or type-config changes;
- Prettier for supported staged documentation, web, and configuration files when
  a root Prettier configuration file or top-level `package.json` `prettier`
  field exists;
- a repository-local ESLint for staged JavaScript and TypeScript when
  configured;
- a repository-local whole-project `tsc --noEmit` when `tsconfig.json` applies.

A configured check with a missing required executable is an error. If staged
content has no corresponding configured checker, the command says so rather than
claiming a tool ran. The command does not install or synchronize tools and does
not run package scripts.

This is intentionally a root-only project-tool policy, not snapshot isolation.
Whole-project type checks and tool configuration use the current checkout, while
per-file check arguments come only from staged paths. Untracked and merely
unstaged files are never passed to per-file checks. Shell detection is limited
to explicit shebangs, ShellCheck dialect directives, conventional shell
extensions, and standard Zsh startup filenames.

After the checks pass, the existing `MODEL` and `LOCAL_MODEL_REASONING` route is
used. The model is instructed only to read the staged diff, write its commit
message, and commit that selection. `-v`/`--verbose` and additional Pi arguments
remain supported.
