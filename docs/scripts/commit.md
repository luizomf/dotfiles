# Checked commits with a local model

`scripts/commit` commits an explicitly staged selection with the configured
local model. Stage the intended files yourself, then run:

```sh
git add path/to/file
commit --check
commit
```

## Quick check and troubleshooting

- `commit --check` runs only the staged checks: no model, no commit, no fixes.
- `commit --help` works outside a repository and without a model.
- With nothing staged, `--check` succeeds with
  `No staged changes; nothing checked.`; unstaged edits are never checked.
- On failure, fix the issue named above the final message, stage the fix, and
  rerun `commit --check`.
- A missing executable means the caller's PATH lacks it; see
  [checker dependencies](check_staged.md#checks-and-dependencies).

Hook activation is local Git configuration
(`git config --show-origin --get core.hooksPath` should show `.githooks`); see
[activation](check_staged.md#activate-in-this-checkout).

## Commit behavior

It first runs [`check_staged`](check_staged.md) and exits before calling the
model when nothing is staged, a staged file also has unstaged edits, or a check
fails.

After the checks pass, the existing `MODEL` and `LOCAL_MODEL_REASONING` route is
used. The host sends the staged diff in the prompt and gives this Sannux
invocation a private temporary workspace, **not the repository**. By default, Pi
receives only the `write` tool, without context-file, skill or prompt-template
discovery. Its only job is to save an English Conventional Commit message to
`/workspace/commit-message.txt`.

The host then validates the message (present, not a symlink, Conventional Commit
subject), confirms HEAD and the staged tree did not change during generation,
reruns the checks on the host, and runs `git commit --file=...` with hooks
enabled. Afterwards it verifies HEAD moved to the selected tree. Nothing is
retried or rolled back on failure; avoid changing the selection while the
message is generated.

`-v`/`--verbose` and extra Pi arguments (after `--`) apply only to this
invocation. Keep `commit` and `check_staged` side by side if copying them
elsewhere.
