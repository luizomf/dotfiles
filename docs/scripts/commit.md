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
used. The host sends the staged diff in the prompt and gives this Sannux
invocation a private temporary workspace, **not the repository**. By default, Pi
receives only the `write` tool, without context-file, skill or prompt-template
discovery. Its only job is to save an English Conventional Commit message to
`/workspace/commit-message.txt`.

The host then verifies the message and confirms HEAD and the staged tree did not
change during generation, reruns the checks, and executes
`git commit --file=...` with hooks enabled. Container tool availability is
irrelevant to these checks: Prettier, Ruff and the other project tools run on
the host, where the initial check ran. No `--no-verify` or other hook bypass is
used.

`-v`/`--verbose` and additional Pi arguments remain supported; wrapper options
before `--` are handled by `commit` itself. The temporary workspace override and
Pi options apply only to this invocation. They do not alter the shared Sannux
image, launcher defaults, agent home, or Daily Paper Compose override. Keep
`commit` and `check_staged` adjacent if copying them out of the dotfiles scripts
directory.

The command does not stage or auto-fix source files. Terminal-title updates are
best-effort, so a missing TTY or tmux pane does not abort a non-interactive run.
The configured model runner and its own environment requirements still apply.

A successful model process is not proof of a usable message. Missing, empty,
symlinked or malformed message files stop the command without a commit. The
first line must have a Conventional Commit subject; the file is passed directly
to Git, never evaluated as shell code. Temporary request/message files are
removed on exit, including failure or interruption. Errors are not automatically
retried.

Before reporting success, `commit` also verifies that HEAD changed and its tree
matches the selected tree. It never rolls back commits or restores files after a
failure. These checks detect ordinary state changes; they are not a sandbox or
atomic protection against concurrent edits. Avoid changing the selection while
the message is being generated.

Running this wrapper is optional: only an activated Git hook covers ordinary
`git commit` calls. Neither this wrapper nor a local hook replaces review or
remote enforcement.
