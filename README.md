# dotfiles

These are my personal dotfiles. They install the exact environment I use every
day, and they are intentionally opinionated.

I have tested clean installations on:

- Ubuntu 24.04 and 26.04 on ARM;
- macOS Sequoia and macOS 26 on Apple Silicon.

I also use them daily on Fedora Asahi Remix 44 (ARM64), but Fedora has not been
tested from a clean installation yet. Traditional Fedora is accepted; Atomic or
OSTree variants and other Linux distributions are rejected by the installer.

No major problems have shown up so far. That is not a promise that the installer
will work on your machine.

Before running anything, open `install.sh` and check what it does. It installs
packages and replaces shell, editor, terminal, Git, tmux, and Pi configuration.
Existing targets are moved to a timestamped directory under
`~/.dotfiles-backups/`, but you should still keep your own backup.

If you still want to run it, install Git first and use:

```bash
git clone https://github.com/luizomf/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

The repository is expected to live at `~/dotfiles`. Start a new login shell when
the installation finishes.

**⚠️ This will replace your configuration. You have been warned. Tamo junto.**

## A note about the scripts

The `scripts/` directory contains personal commands and automation used across
my machines. Some of them contact remote hosts, stop processes, synchronize
files, submit background work, or change system configuration. Read a script
before running it and do not assume it is safe for your setup.

The test suite is intentionally limited to behavior where a regression could
delete data, corrupt shared state, break installation, or leave background work
in a bad state. Tests use isolated fixtures; they do not make these scripts a
supported public API.

## Host synchronization and idle maintenance

`scripts/pullall` updates `~/dotfiles` and direct-child Git checkouts under the
inherited `PROJECTS_DIR`, using `git pull --all --prune --ff-only`. Dirty
checkouts and non-repository directories are skips, not failures. Broken Git
inspection, pull failures, a missing required dotfiles checkout, or
missing/unreadable project listing make the final exit nonzero. Independent
repositories still run. Its final summary counts updates/skips and lists
failures with paths and exit codes.

`scripts/synchosts [--additional-hosts HOST ...]` is ordinary file sync, **not
idle maintenance**. It keeps services running and does not invoke agent-home
cleanup, OmniVoice stops/cache deletion, or Daily Paper media pruning. It merges
local Zsh history through the existing helper (offline history peers remain
optional), runs `pullall`, collects files from every peer, then distributes the
collected result. Hosts still come from the editable `scripts/run_all_hosts`
fleet.

The intentionally conservative transfer scope is:

- Project working files under `~/Desktop/tutoriais_e_cursos` on each host and
  `~/.agents/skills/`. This home-relative sync path is still a personal fixed
  policy, not discovery of remote `PROJECTS_DIR` or `OM_PATHS_FILE` overrides.
- **No `.git` entries**, whether directories, worktree/submodule files, or
  links, at any depth. Existing Git metadata is not removed or repaired. Git
  owns each host's branches, objects, stashes, reflogs and configuration. An
  empty peer must get a real checkout through explicit Git bootstrap; rsync
  alone no longer creates one. Working-file synchronization can still make
  checkouts dirty.
- No `~/.pi`, `~/sannux-data` (including persistent homes, workspaces and
  backups), `~/.ollama/service`, `~/.config/omxterm`, or `~/.codex/automations`.
  No other `~/.agents` state. These may have live writers, credentials,
  machine-specific state or publication continuations; an arbitrary backup file
  is not a verified consistent snapshot. Static Pi/terminal configuration
  remains Git-managed.
- Within transferred trees: no `.pi`, `.codex`, `.claude`, SQLite-style `*.db`,
  `*.sqlite`, `*.sqlite3` files or their `-*` companions. Existing scratch,
  cache, dependency/build, `.omnews-data` and website `run_dir` exclusions
  remain. OmniVoice `data/`, `output/`, `outputs/` and Loudterm `output/` also
  stay local. Daily Paper's `~/.local/state` runtime/media is outside the
  transfer roots.
- Only the caller's validated staged tmux `state.json` is published separately;
  see [tmux synchronization](tmux/README.md#migration-and-synchronization).

A failed collection still allows other collections to finish, but blocks **all
collected-data pushes** in that run: projects and skills may depend on each
other. The caller may already contain partially received files; there is no
rollback. The caller-only tmux snapshot is independent. Save/export/staging
failures block only tmux publication; a failed push does not block other peers.
`pullall` failure is reported but does not block file collection/publication (it
is not the rsync collection phase). The final summary lists failures and blocked
phases and exits nonzero for incomplete work, including staging cleanup
failures. Interruptions report incomplete work, not a transaction rollback.
History's optional offline skips retain the helper's separate best-effort
contract.

There is no `--delete`, fleet transaction, live database backup, conflict
resolver or protection against simultaneous source edits/peer tmux saves. Keep
transferred working files quiescent during sync, without stopping unrelated
services. Review custom runtime/output locations before using this personal
script: unknown state inside project trees is not automatically classified or
snapshotted. Exclusions do not delete old copies on peers. Deploy the updated
script to **all callers** before relying on the Git exclusion; existing
duplicate packs require separate, explicitly authorized idle Git maintenance,
not metadata deletion or rsync repair.

Destructive maintenance remains opt-in through the existing standalone commands:
`clear_sannux_transients` previews and requires `--apply --idle-confirmed` to
remove eligible transients; its process/container guards remain intact.
`stop_omnivoicetts` stops workers before clearing caches. Daily Paper's
`maintenance/prune-runtime-history.sh --tts-media-*` workflow requires checking
**every host before applying on any host**, with publication continuations idle;
follow that checkout's maintenance instructions. None is a prerequisite for
ordinary sync, and running them is not a verification step.

Focused isolated checks (no real SSH, synchronization or service stops):

```sh
python3 -m unittest tests.test_pullall tests.test_synchosts tests.test_idle_cleanup
```

## Development feedback

Python tooling lives in `pyproject.toml`, with versions locked in `uv.lock`.
This is a **development-only** environment, not a package containing the
dotfiles. The installer creates or updates the checkout's `.venv` from the
lockfile after setting up Python, including on reruns. It does not upgrade the
lockfile or activate that environment globally. `OM_INSTALL_SKIP_TOOLCHAINS=1`
skips this step with an explicit reminder.

For an existing checkout, use uv and Python 3.10 or newer to update only the
development tools, without rerunning the installer:

```sh
uv sync --locked
```

This is a dedicated environment: sync can remove packages not declared in the
lockfile. Keep unrelated project dependencies in their own virtual environments.

The local `.venv` is ignored. Do not add it to the global PATH or use it for
installed scripts, tmux hooks, Queue payloads or host maintenance. Each command
keeps its existing runtime interpreter contract; the tooling's Python version is
not a new requirement for every script.

Run feedback checks on the files you are changing, for example:

```sh
uv run --locked ruff check --no-fix tmux/scripts/lazy.py
uv run --locked ruff format --check tmux/scripts/lazy.py
uv run --locked pyright tmux/scripts/lazy.py
```

Ruff checks common mistakes, imports and compatible upgrades; Pyright uses
`standard` checking rather than requiring exhaustive annotations. These are
useful diagnostics, not a contest to eliminate warnings. Investigate relevant
issues instead of adding casts, blanket ignores or abstractions to satisfy a
tool. Existing code has outstanding diagnostics and formatting differences;
compare the affected files before/after a change and report what remains. Keep
using focused tests for behavior, not lint/type checks as substitutes for them.

For a read-only overview, use `uv run --locked ruff check --statistics`,
`uv run --locked ruff format --check` and `uv run --locked pyright`. Both tools
include the extensionless Python commands listed in `pyproject.toml`; update
those lists when adding one. Python-version overrides follow known interpreter
requirements, with a conservative fallback, not the developer's current shell.

Formatting uses the same policies as Neovim:

- Python: Ruff's configuration in `pyproject.toml` (88 columns, double quotes).
  Conform prefers the nearest `.venv/bin/ruff` for its Ruff operations, falling
  back to the existing PATH formatter when absent. This lets the editor use the
  project's locked version without globally activating its environment.
- Prettier-supported files, including JS/TS: root `.prettierrc.json` links to
  `nvim/config_files/prettierrc.json`. Use `prettier --check path/to/file.js`.
- Lua: root `.stylua.toml` links to `nvim/config_files/stylua.toml`. Use
  `stylua --check path/to/file.lua` with the formatter available on PATH.

Do not duplicate these settings or add a Node package/toolchain just for
formatting. After changing the Conform configuration, open a new Neovim session;
`:ConformInfo` shows the selected formatter. Other installed editor tools may
have their own versions; compare them when investigating diagnostic differences.

Format only new/changed files, and review the diff. Existing format-on-save can
still normalize an entire legacy file on its first save; shared settings prevent
ongoing disagreement, not that initial migration. Keep substantial format-only
cleanup separate from functional work. There is no automatic repository-wide
rewrite, new CI gate or requirement to normalize every old script at once. See
[AGENTS.md](AGENTS.md#engineering-and-verification) for the agent policy.

## Tmux

Tmux now saves structure and restores shells lazily by window, without Resurrect,
Continuum or a persistence daemon. Prefix Ctrl-s saves; the existing fzf picker
marks pending windows with `Z`. Start a new Zsh login shell to use the normal
`tmux`/`tmux a` entry points, or run `tmux-lazy start` explicitly.

See [tmux/README.md](tmux/README.md) for migration, quiet/Queue-friendly saves,
`synchosts`, prerequisites and safe cold-restart instructions. Reloading config
never restarts existing panes; do not kill a server containing useful services or
agents merely to enable the new configuration.

## Shared host paths

`config/paths.sh` defines the shared `PROJECTS_DIR` used by shells and
unattended scripts. Supported callers can load machine-specific values with
`OM_PATHS_FILE`; `omnivoice_m4128_half` also accepts `OMNIVOICE_REMOTE_APP`.

The Zsh configuration adds Apple Silicon Homebrew paths and native-build flags
only on macOS. Linux preserves inherited build flags; it does not substitute
Linuxbrew libraries globally. Existing shells and daemons are not reloaded by
these file changes, and inherited flags are not automatically scrubbed.
Queue jobs can use a different PATH from interactive terminals: do not remove
distro packages merely because Homebrew shadows them in your shell.

## Pi Coding Agent

The installer links the static configuration under `pi/agent/` into
`~/.pi/agent/`. Credentials, sessions, trust decisions, generated resources, and
machine-specific model settings stay local and must not be committed.

Skills and extensions are maintained separately in
[omskills](https://github.com/luizomf/omskills) and
[ompi](https://github.com/luizomf/ompi).

## 😈 YOU ONLY LIVE ONCE (YOLO)

If you're feeling lucky... bet on it:

```bash
# 🚨 DANGEROUS (I mean it)
export OM_INSTALL_ASSUME_YES=1 && git clone https://github.com/luizomf/dotfiles && cd dotfiles && ./install.sh
```

50/50 chance everything is gonna be OK.

---

Made with hate, coffee, and a little bit of love.
