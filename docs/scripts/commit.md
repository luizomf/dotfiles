# Checked commits with a local model

`scripts/commit` commits an explicitly staged selection with the configured
local model. Stage the intended files yourself, then run:

```sh
git add path/to/file
commit --check
commit
```

## Quick check and troubleshooting

- `commit --check` runs only the staged checks: no model, no commit, no staging
  or source fixes. Use it on its own, without model/verbose options.
- `commit --help` (or `commit -h`) shows the workflow without requiring a Git
  repository or model configuration.
- Success says `Staged checks passed (configured checks only).`
- With nothing staged, `--check` exits successfully but explicitly says
  `No staged changes; nothing checked.` It does not check your unstaged edits.
- On failure, read the tool's diagnostic above the final failure message, fix
  the named issue, stage that fix with `git add path/to/file`, and rerun
  `commit --check`. Partial staging must be resolved explicitly.
- A missing executable means the calling process's PATH needs preparation; see
  [checker dependencies](check_staged.md#checks-and-dependencies). Missing tool
  configuration is a warning, not proof that that tool checked your files.

To verify which hook directory Git is using:

```sh
git config --show-origin --get core.hooksPath
```

An activated dotfiles hook uses `.githooks` in local repository configuration.
An unset result means it was not activated this way; see
[activation](check_staged.md#activate-in-this-checkout). The setting is local,
not committed: `install.sh` prepares it, or run `./scripts/setup_git_hooks`
after cloning/pulling without reinstalling. Existing custom hook setups are
preserved.

## Commit behavior

It first runs [`check_staged`](check_staged.md), the same checker used by the
optional Git hook. It exits before calling the model when nothing is staged,
when a staged file also has unstaged edits, or when a check fails. See the
checker documentation for supported tools, dependencies, hook activation, and
limits.

After the checks pass, the existing `MODEL` and `LOCAL_MODEL_REASONING` route is
used. The model is instructed only to read the staged diff, write an English
Conventional Commit message, and commit that selection. `-v`/`--verbose` and
additional Pi arguments remain supported; wrapper options before `--` are
handled by `commit` itself. Keep `commit` and `check_staged` adjacent if copying
them out of the dotfiles scripts directory.

The command does not stage or auto-fix source files. Terminal-title updates are
best-effort, so a missing TTY or tmux pane does not abort a non-interactive run.
The configured model runner and its own environment requirements still apply.

A successful model process is not proof of a commit. Before reporting success,
`commit` verifies that HEAD changed and that its tree matches the staged tree
captured before calling the model. If the model does nothing or commits
different content, the command fails and asks you to inspect Git status. It does
not roll back commits, restore files, or automatically retry. This is a
postcondition check, not a sandbox or protection against concurrent edits.

Running this wrapper is optional: only an activated Git hook covers ordinary
`git commit` calls. Neither this wrapper nor a local hook replaces review or
remote enforcement.
