# Lazy tmux

Lazy tmux keeps one normal tmux server and native sessions, windows, and panes;
there is no persistence daemon. Save the structure with **prefix Ctrl-s**. A
cold start recreates saved panes without their processes, starts login shells in
the return window, and starts other windows when you visit them. Already-running
panes are never suspended or respawned by lazy activation. Killing the server
still ends its processes; this is not process checkpointing or service
supervision.

## Requirements and limits

Requires **tmux >= 3.5** and **Python >= 3.9**; no third-party Python packages
are required. Prefer Homebrew tmux on macOS and Linux; the launcher respects
`PATH`. The installer provisions Python/toolchains and installs Homebrew tmux on
Fedora, while retaining the distro fallback for explicit or non-interactive
callers. This configuration does not load or install TPM, Resurrect, or
Continuum. Existing plugin directories and old Resurrect snapshots are left
untouched.

Saved structure includes sessions, windows, panes, layouts, titles, working
directories, active locations, and zoom state. It does not include process
commands or process state. Grouped sessions and linked windows are unsupported.
Names and working directories containing tabs or newlines are rejected. A
missing working directory prevents activation instead of silently falling back
to the home directory.

## Terminal capabilities

The inner terminal remains `tmux-256color`; its terminfo entry must also exist
on remote hosts where applications run. The outer terminal is negotiated
separately. `.tmux.conf` adds `RGB` (true colour) and `usstyle` (underline
styles and colours) for Ghostty, Kitty, foot, Alacritty, WezTerm, and the
generic `xterm-256color` identity used by some modern emulators. Other terminal
types keep tmux's built-in detection; this is not a blanket override for every
client.

`xterm-256color` does not identify an emulator or guarantee these features. Its
entry assumes a modern terminal; remove or narrow that entry if an older client
using the same name renders incorrectly. These settings advertise capabilities;
they cannot implement features missing from a terminal. `allow-passthrough` is
not a replacement for capability negotiation.

Feature entries use fixed array indices starting at 3, preserving tmux's
built-in entries at 0-2 and avoiding duplicate appends on reload. Extended-key
behaviour is unchanged. No new graphics or clipboard passthrough policy is
introduced.

After changing capabilities, use **prefix r**, then detach and reattach the
client and reopen Neovim so both layers can renegotiate. Do not kill the server
or its running panes. Inspect the attached client's features with:

```sh
tmux list-clients -F 'term=#{client_termname} features=#{client_termfeatures}'
```

Matching clients should include `RGB` and `usstyle`. Visual verification of
coloured/styled underlines is still required in the actual terminal, including
any nested tmux or SSH layers. Neovim's spelling highlight keeps a plain
underline as a fallback; this change does not switch it back to an undercurl.

## Everyday use

In a new Zsh terminal outside tmux, `tmux`, `tmux a`, `tmux attach`, and
`tmux attach-session` without additional arguments call `tmux-lazy start`.
Explicit tmux commands and socket or target arguments remain native, including
calls from scripts and agent sessions. Other shells can use the launcher
directly:

```sh
tmux-lazy start
```

The launcher uses the default socket, not a separate everyday "lazy" server. If
that server is already running, it configures hooks and attaches without
restoring or replacing anything. To exercise a cold restore, save first, detach,
and stop the server only when all its processes can safely end. Do not stop the
server hosting an agent just to reload this configuration.

```sh
tmux-lazy status
tmux-lazy save
# Destructive: ends ALL processes in the selected server, without implicit save.
tmux-lazy stop --yes
tmux-lazy start
```

- **Prefix c:** opens a new window in the active pane's working directory.
- **Prefix % / Prefix ":** splits side by side / top and bottom in the active
  pane's working directory.
- **Prefix Ctrl-s:** saves the structure and confirms with a tmux message.
- **Prefix x:** confirms sleeping the **entire current window**, replacing
  tmux's default pane deletion. Ends its pane processes without deleting its
  structure; see [Sleeping a window](#sleeping-a-window).
- **Prefix Ctrl-l / the existing mouse picker:** opens the same fzf/MRU window
  picker. Pending windows show `Z` in the activity-marker position; this does
  not modify tmux's real `Z` (zoom) flag.
- **Prefix Ctrl-r:** displays the cold-restore workflow; it never runs
  Resurrect.
- **Prefix r:** reloads the normal config. Reloading only configures hooks; it
  never restores, kills, or respawns panes and is not a migration of the running
  server.

Before starting a restored shell, activation resets only its process-free pane's
terminal state. tmux gives empty panes a newline mode that `respawn-pane`
preserves; without this reset, TUI linefeeds can return to column zero and
overwrite line numbers or other content. Running panes are never reset by lazy
activation. This fix applies on the next activation, not retroactively to shells
that were already started.

Successful automatic startup and activation are silent. Wait for the prompt
before typing into a newly activated window: empty panes do not buffer keyboard
input. If a working directory is missing, correct it or close and recreate that
window; revisiting retries pending panes without replacing a running process.

## Sleeping a window

**Prefix x**, then **y**, ends the current window's pane processes and leaves
the window pending (`Z` in the picker). **n** or Escape cancels. Unsaved
application work is lost: this is termination, not process suspension. Detached
services are not supervised or guaranteed to stop, just as with native tmux pane
termination.

Sleep preserves the window, pane IDs, titles, layout, active pane, zoom and each
pane's current working directory. A window is **awake** when at least one pane
has a live process, including an idle shell. Empty restored panes and retained
dead panes do not count, even when a dead pane still reports its old PID.

Before stopping any processes, sleep chooses an already-awake destination:

1. The next awake window by numeric index in the same session, wrapping to the
   beginning and skipping sleeping windows.
2. Otherwise, an awake window in another session on the same server, ordered by
   session name and then numeric window index.
3. If none exists, refuse without stopping processes or changing focus. Open a
   window with **prefix c** or visit a sleeping one first.

A sleeping window is never awakened merely to provide a destination. Sleeping
linked windows or windows in grouped sessions remains unsupported; these are
also excluded as destinations. A session's only window can sleep if another
session has a supported awake window.

Focus moves before processes stop. When crossing sessions, all clients attached
to the source session follow to the destination window; clients in other
sessions are not switched. Window selection is still shared within each session,
as in native tmux. If navigation fails, no source process is stopped. Visit
hooks carry a window-local token so a visit queued before sleep cannot
immediately wake the source again, even if its now-detached session still
selects it.

Revisiting starts fresh login shells, not the applications that were ended. Dead
panes are temporarily retained with `remain-on-exit` so the structure survives
without an idle shell in every pane; their previous per-pane `remain-on-exit`
settings are restored on activation. Already-pending panes remain untouched.
Sleeping does not overwrite the saved snapshot: use **prefix Ctrl-s** to persist
updated directories/structure for a later server restart.

For an already-running server after updating this checkout, run
`tmux-lazy configure --quiet` once **before using prefix x** to install the
current binding and visit-token hooks without restarting processes. Existing
bindings remain installed until configured; older lazy sleep bindings refuse to
stop processes until the hooks are updated. The confirmation explicitly says
**Sleep window**. Native **prefix &** still deletes the entire window and its
structure after confirmation.

## State and quiet commands

The launcher is `scripts/tmux-lazy`, backed by `tmux/scripts/lazy.py`. Default
state is `~/.local/share/tmux/lazy/` (honoring `XDG_DATA_HOME`). The directory
contains private local JSON and lock files and is never a repository
deliverable. A failed save leaves the previous snapshot intact. A failed fresh
restore can leave a partial server for inspection; stop and retry explicitly
when it is safe.

Home-relative working directories resolve against each host's home; paths
outside home stay absolute. Do not assume external mounts or project paths exist
on another host. Save captures new objects and explicit deletions; unvisited
panes retain their saved working directories. `state.lock` serializes local
operations, and JSON writes replace files atomically. `focus.json` records the
last visited location separately from the manually saved structure. Only
portable `state.json` is exported or synchronized; socket-specific data, focus,
and locks stay local.

All CLI actions accept `--quiet` before or after the action. It suppresses
confirmations, not errors, warnings, or requested `status` JSON. It does not
change future key bindings. For optional scheduled saves:

```sh
tmux-lazy save --quiet --if-running
```

`--if-running` skips a stopped server without creating or replacing a snapshot;
without it, save reports an error. The dotfiles configuration installs no
automatic save job.

## Optional Queue autosave

An operator can enable an hourly OMQueue Schedule on each host, labeled
`tmux-lazy-autosave`, with cron `0 * * * *`. Autosave replaces the same
checkpoint as manual save; it does not keep snapshot history.

For Queue execution, use verified absolute Python and script paths and an
explicit `PATH` containing the chosen tmux and shell toolchains. Select the
host's default socket explicitly so an agent's custom socket cannot become the
autosave target. No shell background `&` or additional daemon is needed.

To change the interval on a host without creating a duplicate Schedule:

1. Find its ID with `omqueue_schedule --label tmux-lazy-autosave`.
2. Read the current revision with `omqueue schedule inspect <id> --json`.
3. Create a private temporary file with `document=$(mktemp)` and export with
   `omqueue schedule export <id> > "$document"`. Do not add `--json`; it wraps
   the portable document in an operational response.
4. Edit that document: add `scheduleId` from the inspection and set
   `baseRevision` to its `currentRevision`, then change `cron`. Use
   `*/30 * * * *` for every 30 minutes, `0 * * * *` for hourly, or `0 */2 * * *`
   for every two hours. These are wall-clock boundaries, not intervals measured
   from installation. Keep the remaining fields intact.
5. Apply with `omqueue schedule apply "$document" --json`, then remove the
   temporary document with `rm -- "$document"`. A stale revision is rejected;
   inspect again instead of creating a replacement Schedule. Repeat on each host
   that should change.

Use `omqueue schedule disable <id>` to pause and `omqueue schedule enable <id>`
to resume. Changes affect future occurrences, not already-created Jobs. Keep
exported Schedule documents local: they include host-specific command paths.

## Sockets and state directories

`--socket PATH` explicitly selects a server. Without it, commands use `$TMUX`
when inside tmux, otherwise the normal socket under `TMUX_TMPDIR` or `/tmp`.
Custom and agent sockets get isolated state under `lazy/servers/<socket-hash>/`
unless explicitly overridden.

`--state-dir DIR` or `TMUX_LAZY_STATE_DIR` selects another state directory. An
already-configured server retains its own directory. Do not share one override
across unrelated servers unless that is deliberate.

## Migration and synchronization

If the default server has no lazy JSON yet, its first cold start can import the
local `~/.local/share/tmux/resurrect/last` automatically. To import explicitly
into an empty lazy state directory:

```sh
tmux-lazy import --snapshot "$HOME/.local/share/tmux/resurrect/last"
```

Import ignores saved process commands, never changes the Resurrect files, and
never overwrites existing lazy JSON. Home mapping supports local snapshots and
the portable `#{HOME}` or `~` paths used by earlier snapshots.

`scripts/synchosts` saves the default server when running, stages validated
state, and publishes only `state.json`. It does not clear peer directories. This
is publication, not a merge, fleet transaction, or coordination with a peer's
concurrent save. Keep peer saves quiescent during publication, without stopping
their running panes or unrelated services. All participating hosts need this
updated checkout before relying on the snapshot. The sync script targets
`~/.local/share/tmux/lazy/` on peers; adjust its policy for nondefault state or
XDG paths instead of assuming those overrides are discovered remotely. A newer
peer timestamp does not override an explicit published snapshot. Snapshot rsync
uses `--delay-updates --checksum`; other data transfers retain their existing
update rules. See
[the sync scope and failure policy](../docs/scripts/synchosts.md).

```sh
# Export to a NEW directory; only portable state.json is emitted.
tmux-lazy export /path/to/new-staging-directory
```

## Other helpers

- `tmux_make_sessions [PROJECTS_DIR]` is an optional initial generator. It
  refuses an existing target server, creates initial shells eagerly, and saves
  through the same lazy command. Shared `OM_PATHS_FILE` and project-path rules
  are preserved.
- `tmux_respawn_all --yes` is explicitly destructive: save first, reset loaded
  panes to login shells in their current working directories, then save again.
  Pending panes stay pending.
- Bulk send helpers skip pending panes; `tmux_run_visible_panes` retains its
  existing **current-session** scope despite its historical name.
- `tmux_slop_nudger` refuses a pending target rather than sending to an empty
  pane. Direct external `send-keys` callers must likewise target a loaded pane.
- `restart_terminal` remains a separate explicit destructive maintenance
  command; it is not part of lazy startup or restore.

## Tests

From the repository root:

```sh
python3 -m unittest tests/test_tmux_lazy.py tests/test_synchosts.py tests/test_install_platform.py
```

The focused tests use private tmux sockets and temporary homes/fixtures; no
shared live server is needed.
