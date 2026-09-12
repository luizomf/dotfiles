# `synchosts`

`scripts/synchosts [--additional-hosts HOST ...]` synchronizes selected working
files between the hosts configured in `scripts/run_all_hosts`.

It is personal file synchronization, not a deployment pipeline, backup, fleet
transaction, or idle-maintenance command.

## Workflow

The command:

1. validates the host list;
2. merges Zsh history;
3. saves and stages portable tmux state when available;
4. runs `pullall`;
5. collects project and skill files from every peer; and
6. publishes the collected files only if every collection succeeded.

The caller's tmux snapshot is published separately. See
[tmux synchronization](../../tmux/README.md#migration-and-synchronization).

## Transfer scope

The synchronized roots are:

- `~/Desktop/tutoriais_e_cursos`;
- `~/.agents/skills/`; and
- the caller's staged tmux `state.json`.

The project path is an intentional home-relative policy. The script does not
discover a peer's `PROJECTS_DIR` or `OM_PATHS_FILE` override.

The rsync filters exclude:

- `.git` entries at any depth, including worktree and submodule files;
- `.pi`, `.codex`, `.claude`, SQLite files and their sidecars;
- dependency, cache, scratch, build, and known runtime-output directories; and
- OmniVoice and Loudterm output directories.

Git metadata remains owned by Git on each host. An empty peer needs a real clone;
rsync does not create one. Existing excluded files are not deleted because the
sync does not use `--delete`.

The script does not synchronize `~/.pi`, other `~/.agents` state,
`~/sannux-data`, `~/.ollama/service`, `~/.config/omxterm`, or
`~/.codex/automations`. These locations may contain credentials, live state, or
machine-specific data.

Review custom runtime and output paths before using the script. Unknown state
inside a transferred project is not automatically recognized.

## Failure behavior

All collections are attempted. If any collection fails, publication of collected
projects and skills is blocked for every peer. Files already received by the
caller are not rolled back.

Tmux staging and publication are independent: a save or staging failure blocks
tmux publication only, and one failed tmux push does not stop the others.
A `pullall` failure is reported but does not block file collection. The final
summary reports failures and blocked phases and exits nonzero for incomplete
work.

There is no conflict resolution or protection from simultaneous source edits and
peer tmux saves. Keep transferred files and peer tmux saves quiet during sync.
Deploy script changes to every caller before relying on new exclusions.

`synchosts` does not stop services or run destructive cleanup. Those remain
explicit operations; see [`clear_sannux_transients`](clear_sannux_transients.md)
and [`stop_omnivoicetts`](stop_omnivoicetts.md).

## Verification

From the repository root:

```sh
python3 -m unittest tests.test_synchosts
```

The test uses fake remote commands and local fixtures. Do not run real SSH or
synchronization as a verification step.
