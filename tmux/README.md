# Lazy tmux

One normal tmux server, native sessions/windows/panes, and no persistence daemon.
Save the structure with **prefix Ctrl-s**. A cold start recreates it with empty
panes and starts login shells only in the return window. Visiting another window
starts its shells once. Already-running panes are never suspended or respawned by
lazy activation. Killing the server still ends its processes; this is not process
checkpointing or service supervision.

Requires **tmux >= 3.5** and **Python >= 3.9**, using Python's standard library.
Prefer Homebrew tmux on macOS and Linux; the command respects PATH. The installer
already provisions Python/toolchains and now also installs Brew tmux on Fedora,
while retaining the distro fallback for explicit/non-interactive callers.
No TPM, Resurrect or Continuum plugin is loaded or installed by this configuration.
Existing plugin directories and old Resurrect snapshots are not deleted.

## Everyday use

In a new Zsh terminal outside tmux, `tmux`, `tmux a`, `tmux attach` and
`tmux attach-session` (without additional arguments) call `tmux-lazy start`.
Explicit tmux commands and socket/target arguments remain native, including calls
from scripts and agents. Other shells can use the launcher directly:

```sh
tmux-lazy start
```

The launcher uses the default socket, not a separate everyday "lazy" server. If
that server is already running, it configures hooks and attaches without restoring
or replacing anything. To exercise a cold restore, save first, detach and stop
that server **only when all its processes can safely end**, then start again.
Do not stop the server hosting an agent just to reload this configuration.

```sh
tmux-lazy status
tmux-lazy save
# Destructive: ends ALL processes in the selected server, without implicit save.
tmux-lazy stop --yes
tmux-lazy start
```

- **Prefix Ctrl-s:** save structure and confirm through `display-message`.
- **Prefix Ctrl-l / existing mouse picker:** same fzf/MRU navigation. Pending
  windows show `Z` in the existing activity-marker position; loaded windows keep
  the normal `✚`/blank marker. This does not modify tmux's real `Z` (zoom) flag.
- **Prefix Ctrl-r:** explains the cold-restore workflow; never runs Resurrect.
- **Prefix r:** reload the normal config. Reload only configures hooks; it never
  restores, kills or respawns panes. It is not a migration of the running server.
- Automatic startup and activation are silent. A success message here would hold
  client redraw and could hide an already-ready shell behind a black pane.

The minimal status bar is unchanged; there is no demo label or extra lazy column.
Wait for the prompt before typing into a newly activated window: empty panes do
not buffer keyboard input. Missing cwd is an error, not a silent fallback to home.
Correct the directory (or close/recreate that window); revisiting retries pending
panes without replacing any running process.

## State and quiet commands

The implementation is `tmux/scripts/lazy.py`; `scripts/tmux-lazy` is the PATH entry.
Default state is `~/.local/share/tmux/lazy/state.json` (honoring `XDG_DATA_HOME`).
The JSON stores session/window identities, names and indices, pane cwd/titles,
layouts, active panes and zoom. New objects and explicit deletions are captured on
save. Unvisited panes retain their saved cwd rather than an empty placeholder cwd.
`focus.json` records last-visited location separately from the manual structure
checkpoint. `state.lock` coordinates the local operations; writes replace JSON
atomically. These files are private local state, never repository deliverables.

Home-relative cwd is explicit in the JSON and resolves against each host's home.
Paths outside home stay absolute. Do not assume external mounts or project paths
exist on another host. Grouped sessions, linked windows and names/cwd containing
tabs or newlines are refused rather than silently corrupted. A failed save leaves
the previous snapshot intact. A failed fresh restore leaves its partial server for
inspection; stop/retry explicitly when safe rather than replacing live work.

All CLI actions accept `--quiet` before or after the action. It suppresses
confirmations, not errors/warnings or requested `status` JSON. It does not alter
future key bindings. For optional scheduled saves:

```sh
tmux-lazy save --quiet --if-running
```

`--if-running` skips a stopped server without creating/replacing a snapshot;
without it, save reports an error. No automatic save job is installed. For Queue
execution use verified absolute Python/script paths and an explicit PATH with the
chosen tmux and shell toolchains; do not assume an interactive login environment.
No shell background `&` or additional daemon is needed.

`--socket PATH` explicitly selects a server. Without it, commands use `$TMUX`
when inside tmux, otherwise the normal socket under `TMUX_TMPDIR` (or `/tmp`).
Custom/agent sockets get isolated state under `lazy/servers/<socket-hash>/` unless
explicitly overridden. `--state-dir DIR` or `TMUX_LAZY_STATE_DIR` selects another
state directory; an already-configured server retains its own directory. Do not
share one override across unrelated servers unless that is deliberately intended.

## Migration and synchronization

If the default server has no lazy JSON yet, its first cold start can import the
local `~/.local/share/tmux/resurrect/last` automatically. To import explicitly into
an empty lazy state directory:

```sh
tmux-lazy import --snapshot "$HOME/.local/share/tmux/resurrect/last"
```

Import ignores saved process commands and never changes the Resurrect files.
Existing lazy JSON is never overwritten by import. Home mapping assumes a local
snapshot or the portable `#{HOME}`/`~` paths produced by the old sync helper.

`scripts/synchosts` now saves the **default** server once with `--quiet
--if-running`, exports validated state to a disposable staging directory, and
publishes only `state.json`. No peer directory is cleared. Socket-specific data,
locks and local focus remain on their host; newer peer timestamps do not override
an explicit publication from the caller. Rsync stages replacement with
`--delay-updates --checksum`; other data retains the script's previous update rules.

This is publication, not a merge, fleet transaction or coordination with a
peer's concurrent save. Ordinary `synchosts` no longer stops services or
performs idle cleanup; see
[the sync scope and failure policy](../docs/scripts/synchosts.md).
Keep peer saves quiescent during publication, without stopping their running
panes or unrelated services. A failed local save/export blocks tmux publication,
not independent file transfers; a failed tmux push does not block other peers.
All participating hosts need this updated checkout before relying on the
snapshot. The personal script targets `~/.local/share/tmux/lazy/` on peers;
adjust its policy for nondefault state/XDG paths instead of assuming those
overrides are discovered remotely.

```sh
# Export to a NEW directory; only portable state.json is emitted.
tmux-lazy export /path/to/new-staging-directory
```

## Other helpers

- `tmux_make_sessions [PROJECTS_DIR]` remains an optional initial generator. It
  refuses an existing target server, creates the initial shells eagerly and saves
  through the same lazy command. Subsequent cold restores are lazy. It no longer
  deletes old snapshots; shared `OM_PATHS_FILE`/project-path rules are preserved.
- `tmux_respawn_all --yes` is explicitly destructive: save first, reset loaded
  panes to login shells in their current cwd, then save again. Pending panes stay
  pending. It no longer invokes Resurrect, history synchronization, remote
  maintenance or snapshot deletion.
- Bulk send helpers skip pending panes; `tmux_run_visible_panes` retains its
  existing **current-session** scope despite its historical name.
- `tmux_slop_nudger` refuses a pending target rather than silently sending to an
  empty pane. Direct external `send-keys` callers must similarly target a loaded
  pane. Existing ordinary native agent-created windows need no new protocol.
- `restart_terminal` remains a separate explicit destructive maintenance command;
  it is not part of lazy startup or restore.

## Verification

Run from the repository root:

```sh
python3 -m unittest tests/test_tmux_lazy.py tests/test_synchosts.py tests/test_install_platform.py
```

The tmux checks use private sockets and synthetic homes/state, including a real
pseudo-TTY client for the redraw regression. Sync checks use fake remote/maintenance
commands and local rsync fixtures. The focused suite has been exercised on macOS;
the core tmux checks also run on Linux/tmux 3.5a in a read-only Docker container
with an executable temporary filesystem for its test shell. No installer, real
sync, Queue job or live-server destruction is a validation step.
