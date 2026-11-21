# `synchosts`

`scripts/synchosts [--skip-pull] [--sync-auth] [--additional-hosts HOST ...]`
copies personal working files between the trusted main hosts in
`scripts/run_all_hosts`, and can publish the result to temporary receive-only
hosts.

The policy is **copy whole roots, minus explicit exclusions**: new files need no
allowlist entry. This is private file synchronization between trusted peers, not
a deployment pipeline or credential manager. The script is public; the files it
transfers must never be committed here.

## Main fleet and temporary destinations

The `hosts=(...)` array in `scripts/run_all_hosts` is the single main-fleet
list. The caller must be in it (matched by short hostname, case-insensitively);
an unlisted machine fails before any transfer.

```sh
synchosts
synchosts --additional-hosts sandbox-vm
synchosts --skip-pull --additional-hosts sandbox-vm
synchosts --sync-auth --additional-hosts sandbox-vm test-vps
```

- **Main hosts:** collect from every other main host, keeping the newest
  modification time per file, then distribute the result among them.
- **Additional hosts:** receive the consolidated data (checksum-based, ignoring
  their mtimes) but are never collection sources, including for Zsh history.
  Their own extra files are neither deleted nor sent back. An alias that is
  already a main host stays bidirectional.

Timestamps are not intent: a regenerated or emptied file on a main host still
wins if it is newest. Keep consumers idle during sync so a running process does
not write its old state back, and keep backups for recovery.

## What travels

| Root                            | Scope                                                                                                                         |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `~/Desktop/tutoriais_e_cursos/` | Projects, with the project exclusions below                                                                                   |
| `~/.agents/skills/`             | Whole directory                                                                                                               |
| `~/.pi/`                        | Whole directory; known auth uses the separate flow below                                                                      |
| `~/.claude/`                    | Settings, `CLAUDE.md`, skills, agents, commands, and per-project `memory/` only; sessions, caches, and credentials stay local |
| `~/sannux-data/`                | Whole directory except `workspaces/`, `worktrees/`, `WIP/`, and `backups/fedora-network/`                                     |
| `~/.ollama/service/`            | Whole directory                                                                                                               |
| `~/.config/omxterm/`            | Whole directory                                                                                                               |
| `~/.codex/`                     | **Only `auth.json`, with `--sync-auth`**                                                                                      |
| `~/.local/share/tmux/lazy/`     | Only the caller's exported `state.json`                                                                                       |
| `~/.zsh_history`                | Merged from the main fleet, then sent to every destination                                                                    |

Shared exclusions apply everywhere. The Sannux tree includes its nested agent
homes, so private SSH, browser, and config files stored there travel too.

Symlinks are preserved, not dereferenced or rewritten. Use relative targets that
exist at the same relative location on every host; `$HOME` or `~` inside a link
target is not expanded.

Copying a binary or service template does not install, build, or activate it.
`~/dotfiles` itself is not copied: unless `--skip-pull` is given, `pullall` runs
over SSH on every selected host first (skipping dirty checkouts), so commit and
push dotfiles changes before syncing.

## What is excluded

`project_excludes` in the script is the source of truth:

- `.git` at every depth;
- `*.db`, `*.sqlite`, `*.sqlite3` and their `-*` sidecars, except completed
  snapshots under `~/sannux-data/backups/` (sidecars still excluded; the script
  does not check whether a DB is open);
- `*.ephemeral-runs/`;
- `node_modules/`, `dist/`, `.venv/`, `venv/`, Python caches, `.cache/`,
  `.astro/`;
- `.omnews-data/` in full;
- the Daily `run_dir`, OmniVoice data/output, and Loudterm output paths.

The project root also excludes `.pi`, `.codex`, `.claude`, nested
`tutoriais_e_cursos/`, `/omxterm-issue-278/`, and each project's root
`release/`. These do not affect the separately synchronized Pi/Sannux roots.

Excluded directories are not removed from peers that already have copies.
Worktrees outside `~/sannux-data/worktrees/` still travel, since the script does
not detect them from Git metadata. Create new worktrees at
`~/sannux-data/worktrees/<repo>/<worktree_name>`.

`.scratch/` travels, so notes and handoffs follow you; notes about PIDs, jobs,
or containers describe the host that wrote them. Generated audio is already
excluded through `.cache/` and the OmniVoice/Loudterm output paths; do not
exclude audio globally, because OmniVoice's `samples/` must travel.

## Auth

```sh
synchosts --sync-auth
```

These files are excluded from normal collection and only pushed, from the
caller, with `--sync-auth`:

- `~/.codex/auth.json`;
- `~/.pi/agent/auth.json`;
- `~/sannux-data/agent-homes/*/.codex/auth.json`;
- `~/sannux-data/agent-homes/*/.pi/agent/auth.json`.

The caller's copy wins even if a peer's is newer, and auth is never pulled. Each
home keeps its own namespace. Recipients get mode `0600`; symlinked or missing
source files are skipped. Replacement is atomic per file (temporary file plus
`--delay-updates`), not across files or hosts. Keep consumers idle: a running
agent can keep a token in memory or overwrite the file, and a successful copy
does not prove the token works. Other credentials inside the copied roots follow
ordinary sync; OS keyrings are not handled.

## Rsync executable

On macOS the script prefers Homebrew rsync (`/opt/homebrew/bin/rsync`, then
`/usr/local/bin/rsync`) over Apple's OpenRSYNC, which rejects the auth step's
`--chmod=F600`. Remote commands get the same preference through `--rsync-path`.
Elsewhere it uses `rsync` from PATH; `RSYNC_BIN` overrides the local choice.

## Workflow and failures

Order: validate hosts, merge Zsh history, stage tmux state, run `pullall`,
collect from main peers, then distribute to main and additional peers. A
`pullall` failure is reported but does not stop the transfers. If any main-host
collection fails, data, history, and auth publication are skipped (already
collected files are not rolled back). A failed push does not stop the others.
The summary lists failures and exits nonzero.

Main-host data uses rsync's mtime merge (`-u`), not version control:
simultaneous edits are not resolved, and same-size, same-mtime changes can be
missed. There is **no deletion propagation**; remove unwanted files on each
host. See
[tmux synchronization](../../tmux/README.md#migration-and-synchronization).

Paths are relative to each host's own home; peer overrides such as
`PROJECTS_DIR` or `AGENT_HOME_PATH` are not discovered. Update the script on
every main host before relying on new filters. No real sync is needed to
validate a code change.

## Verification

```sh
python3 -m unittest tests.test_synchosts
```
