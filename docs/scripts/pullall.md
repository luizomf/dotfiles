# `pullall`

`scripts/pullall` updates `~/dotfiles` and each direct child of `PROJECTS_DIR`
that is a Git checkout.

## Behavior

For each clean checkout, it runs:

```sh
git pull --all --prune --ff-only
```

Dirty checkouts and non-repository directories are skipped. A failure in one
repository does not prevent attempts on the others. The final summary lists
updated, dirty, non-repository, and failed entries.

The command exits nonzero when:

- the required `~/dotfiles` checkout is missing;
- Git inspection or pull fails;
- `PROJECTS_DIR` cannot be listed; or
- a temporary repository list cannot be created or removed.

## Pull timeout

Each pull has a 60-second timeout, followed by TERM and up to 5 seconds before
KILL. This bounds each pull, not the whole command or Git inspection.

GNU coreutils `timeout` or `gtimeout` must be on PATH. It is provided by
coreutils on Linux and by `homebrew/Brewfile` on macOS. The script aborts instead
of falling back to an unbounded pull when the command is missing or incompatible.

Exit 124 means timeout. Exit 137 is reported as timeout or SIGKILL because GNU
timeout cannot distinguish its escalation from an external KILL.

Timeout signals Git's process group, but it is not complete descendant
supervision. Detached children may survive. An interrupted pull is not rolled
back and Git metadata is not cleaned automatically; inspect the checkout and
remaining processes before retrying.

## Verification

From the repository root:

```sh
python3 -m unittest tests.test_pullall
```

The test uses isolated repositories and fake timeout/Git commands.
