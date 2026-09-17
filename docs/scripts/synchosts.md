# `synchosts`

`scripts/synchosts [--sync-auth] [--additional-hosts HOST ...]` copies personal
working files between the trusted hosts in `scripts/run_all_hosts`.

The policy is **copy whole roots, minus explicit exclusions**. New files do not
need an allowlist entry. This is personal, private file synchronization, not a
public-data export, deployment pipeline, or credential manager. The script and
documentation are public; the files they transfer must not be committed here.

## What travels

| Root                            | Scope                                                                                                                            |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `~/Desktop/tutoriais_e_cursos/` | Projects, with the project exclusions below                                                                                      |
| `~/.agents/skills/`             | Whole directory, with shared exclusions                                                                                          |
| `~/.pi/`                        | Whole directory, including settings, models, sessions, resources and new/unlisted files; known auth uses the separate flow below |
| `~/sannux-data/`                | Whole directory except `workspaces/` and `worktrees/`, with shared exclusions and known auth rules                               |
| `~/.ollama/service/`            | Whole directory, including catalogs, docs/history, source, binaries and backups; shared exclusions still apply                   |
| `~/.config/omxterm/`            | Whole directory: config, snippets, themes, assets and new files, with shared exclusions                                          |
| `~/.codex/`                     | **Only `auth.json`, with `--sync-auth`**; never the whole host Codex home                                                        |
| `~/.local/share/tmux/lazy/`     | Only the caller's exported portable `state.json`; no broader `~/.local/` synchronization                                         |

The whole Sannux tree includes its nested agent homes and metadata; the
host-only restriction on `~/.codex/` does not turn those homes into an
allowlisted subset. Private SSH/browser/config files stored there may travel.
Only use trusted peers and keep the sources idle, as with the original personal
sync workflow.

Symlinks are preserved by rsync, **not dereferenced**. Relative links under
`~/.pi/agent/extensions` stay relative. Their targets must exist at the same
relative location on each host; the script does not rewrite links or paths. Use
relative symlink targets across macOS/Linux home layouts. Literal `$HOME` or `~`
inside a symlink target is not expanded; those forms work in shell expressions
or configuration formats that explicitly support expansion.

Copying a binary or service template does not install, run, rebuild or activate
it. Platform-specific files may be stored on another OS without becoming
portable executables. Builds, dependencies, runner setup and service management
remain manual. See [local models](../local-models.md) for catalog generation and
what `test_models` does separately.

## What is excluded

`project_excludes` in the script is the shared source of truth. It excludes:

- `.git` at every depth, including worktree/submodule files;
- `*.db`, `*.sqlite`, `*.sqlite3` and their `-*` sidecars, with the backup
  exception below;
- `*.ephemeral-runs/`, even when something was accidentally left behind;
- `node_modules/`, `dist/`, `.venv/`, `venv/`, Python bytecode/test/lint caches,
  `.cache/`, and `.astro/`;
- `.omnews-data/` in full, including `$PROJECTS_DIR/omnews/.omnews-data/`;
- the existing Daily `run_dir`, OmniVoice data/output and Loudterm output paths.

The project-root transfer additionally retains its existing `.pi`, `.codex`,
`.claude`, and nested `tutoriais_e_cursos/` exclusions. They do not suppress
these directories inside the separately synchronized Pi/Sannux roots. The
project-root `/omxterm-issue-278/` worktree is also explicitly excluded.

**Backup exception:** `.db`, `.sqlite` and `.sqlite3` files beneath
`~/sannux-data/backups/` travel; their sidecars remain excluded. Keep completed,
self-contained snapshots there, not live databases. The script does not detect
whether a DB is open or create a consistent backup. Other DB locations retain
the shared exclusions, including backups inside excluded `.omnews-data/`.

`~/sannux-data/workspaces/` and `~/sannux-data/worktrees/` are excluded in both
directions: worktrees there stay host-local and must be transferred manually
when needed. Existing peer copies are not removed. Worktrees outside these
directories still travel unless explicitly excluded; the script does not detect
worktrees from Git metadata.

Create new Git worktrees at `~/sannux-data/worktrees/<repo>/<worktree_name>`.
Existing worktrees are not relocated automatically.

There are no blanket exclusions for Sannux sessions, backup directories,
installation metadata, or unlisted files. Git metadata and the shared
filename/path exclusions still apply inside those directories.

The rest of host `~/.codex/`, the rest of `~/.local/`, Queue state/config under
unlisted machine-local roots, and other unlisted home directories do not travel.
Custom runtime paths inside a copied root need an explicit exclusion if the
shared filters do not cover them.

## Continuing work on another machine

`.scratch/` travels with the copied roots: investigation notes and handoffs
should not need to be recreated on another host. Shared exclusions still apply
inside scratch directories. Notes about PIDs, containers, running jobs or local
paths are historical context, not proof of the other host's current state.

Default generated audio is already covered:

- EdgeTTS writes its cache to the checkout's `.cache/edgetts/`, excluded by
  `.cache/`. Both its CLI and the dotfiles wrapper support overrides; an
  `EDGETTS_CACHE_DIR`, `--cache-dir` or explicit `--output` outside excluded
  paths follows that destination's normal sync rules.
- OmniVoice's root `output/`, `outputs/` and `.cache/` stay excluded.
- Loudterm's root `output/` stays excluded.

Do not exclude every MP3/WAV globally: OmniVoice's `samples/` contains reference
voices needed by the wrappers and must travel. Explicitly saved audio outside
the known generated directories is ordinary project data.

For an already-prepared peer, this transfers working files, private agent homes
and notes, not the entire running environment. A few boundaries remain visible:

- `~/dotfiles` itself is outside the rsync data roots. `pullall` runs on the
  caller, does not push commits, and skips dirty checkouts. Uncommitted dotfiles
  edits do not reach peers through this command. Commit and push intended
  versioned changes, then pull the updated dotfiles on peers before using the
  sync. Private sync data and scratch notes stay out of Git.
- Project `.pi`, `.codex` and `.claude` directories retain their existing
  exclusions. Project-local agent settings may therefore differ even though the
  whole host `~/.pi/` travels.
- Dependencies, installed tools, images, services and intentionally local Queue
  state are not installed or migrated. Use the existing manual setup on peers.

These are transfer boundaries, not new automatic exclusions or setup actions.

## Auth

```sh
synchosts --sync-auth
```

Known auth files have their own caller-authoritative publication:

- `~/.codex/auth.json`;
- `~/.pi/agent/auth.json`;
- `~/sannux-data/agent-homes/*/.codex/auth.json`;
- `~/sannux-data/agent-homes/*/.pi/agent/auth.json`.

These exact Pi/Sannux paths are excluded from normal data collection. With the
flag, the current machine sends its regular auth files, even if a peer copy has
a newer timestamp. It never pulls those auth files from peers. Each home keeps
its own namespace; host Codex auth is not transplanted into Sannux or converted
into Pi auth. Other credentials inside the broad copied roots follow ordinary
file synchronization; `--sync-auth` is not a universal secret scanner.

Recipients receive file mode `0600`; newly created auth directories use a
restrictive umask. Checksums detect different auth contents with identical
size/mtime. Source auth symlinks and absent files are skipped without changing
the peer. OS-keyring credentials and nondefault home overrides are not handled.

Auth uses rsync temporary-file replacement and `--delay-updates`, never
`--inplace` or `--append`: replacement is **atomic per file**, not across all
files or machines. Keep consumers idle; active processes may retain credentials
in memory or overwrite a transferred file. A successful transfer does not prove
token validity or prevent refresh-token races. OpenAI documents both
[auth-cache copying](https://learn.chatgpt.com/docs/auth#login-on-headless-devices)
and
[concurrent-session limitations](https://learn.chatgpt.com/docs/auth/ci-cd-auth).

## Rsync executable

On macOS the script prefers the installed Homebrew rsync at
`/opt/homebrew/bin/rsync`, then `/usr/local/bin/rsync`, over Apple's older
OpenRSYNC. Elsewhere it uses `rsync` from PATH. `RSYNC_BIN` can select an
explicit local executable, including an isolated test double.

Remote rsync commands prepend those Homebrew locations to their own PATH using
`--rsync-path`; this does not change the login shell's environment. The script
never sources `.zshrc` or changes the global PATH. This matters because an
interactive terminal and a non-interactive Zsh/SSH command can otherwise resolve
different rsync binaries. Auth's `--chmod=F600` requires the modern rsync;
Apple's OpenRSYNC rejects that option. Nothing is installed automatically.

## Workflow and failures

The command validates the host list, merges Zsh history, saves/stages tmux
state, runs `pullall`, then collects data from every peer before distributing
it. If any collection fails, data and optional auth publication are blocked;
already collected local files are not rolled back. Tmux publication is
independent. A failed push does not stop other pushes or the separate auth
phase. The summary reports failures and exits nonzero for incomplete work.

Normal data uses the existing mtime-based `rsync -u` merge. It is not version
control or an exact mirror: simultaneous edits are not resolved, and ordinary
equal-size/equal-mtime changes may be missed. Auth and tmux use their distinct
caller-owned publication rules. See
[tmux synchronization](../../tmux/README.md#migration-and-synchronization).

There is **no deletion propagation**, cleanup, or service shutdown. Missing auth
is not a fleet logout. Remove unwanted files explicitly on the intended hosts;
provider token revocation is a separate operation. No builds, installs, model
calls, resource refreshes or Queue jobs are added by these transfers. Existing
history, `pullall`, and tmux steps retain their effects.

Paths are relative to each host's own home. The script does not discover peer
`PROJECTS_DIR`, `OM_PATHS_FILE`, `AGENT_HOME_PATH`, or `CODEX_HOME` overrides.
Update the script on every machine where it is invoked before relying on these
filters. No real synchronization is needed to validate a code change.

## Verification

```sh
python3 -m unittest tests.test_synchosts
```

Tests use synthetic private files, fake remote commands and local rsync
fixtures. They cover whole-directory transfer, preserved relative links, shared
exclusions, auth publication with a selected rsync despite an older PATH
candidate, host Codex isolation, failure handling and tmux behavior.
