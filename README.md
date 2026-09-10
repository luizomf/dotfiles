# Dotfiles

This repository is intentionally highly opinionated. It installs the exact
personal development environment I use every day; it is not a general-purpose
bootstrap framework.

## Before changing anything

**These dotfiles affect the live environment and commands used by other projects.**
Installed configuration is symlinked into this checkout, so edits may take effect
without reinstalling. Follow the [required change checklist in AGENTS.md](AGENTS.md#required-checklist-for-every-change)
before editing and before handing off, including documentation-only changes.
Check downstream consumers, protect public data, and report validation gaps and
any required reloads or migrations. Never commit `.env` files or secrets, and do
not run the installer or operational commands merely as a check.

## Tested systems

**Installer platforms: macOS, Ubuntu, and traditional Fedora / Fedora Asahi Remix.**

| System | Hardware | Validation |
| --- | --- | --- |
| **Ubuntu 24.04** | ARM | Clean installation; less day-to-day use |
| **Ubuntu 26.04** | ARM | Clean installation; less day-to-day use |
| **macOS Sequoia** | Apple Silicon | Clean installation |
| **macOS 26.6.2** | Apple Silicon VM | Clean installation, including toolchains and plugins |
| **Fedora Asahi Remix 44 — KDE Plasma** | ARM64 | Ongoing day-to-day use; full installer on an existing environment; Zsh and tmux/Resurrect validated |

**Fedora is validated through ongoing use; Ubuntu mainly through repeated clean installations.**
These are different kinds of coverage, not a reliability ranking.

**Fedora has not been clean-install tested.** Traditional Fedora is accepted by
the installer but has not been separately validated. Other versions remain
untested. Atomic/OSTree Fedora variants and other Linux distributions are rejected.
See [Fedora and safe reruns](#fedora-and-safe-reruns) for the package policy and limits.

## Before installing

`install.sh` installs system packages and replaces existing configuration with
symbolic links into this repository. Existing targets are moved to a timestamped
backup under `~/.dotfiles-backups/` before links are created.

The repository must be cloned at `~/dotfiles`; deployed shell configuration and
shared scripts rely on that location.

Review the script before running it. In particular, it:

- installs packages with Homebrew, APT or DNF without upgrading the whole OS;
- downloads installers and source code from third-party projects;
- installs the current stable Neovim formula with Homebrew;
- configures the UTF-8 locale on Ubuntu and preserves Fedora's selected locale;
- changes the default shell to Zsh on Ubuntu and Fedora;
- installs Vim, Neovim, and Tmux plugin managers and plugins;
- installs shell, editor, terminal, Git, and Pi configuration.

Do not run it on a machine whose current configuration has not been backed up.

## Installation

Install Git first, then run:

```bash
git clone https://github.com/luizomf/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

The script asks for confirmation before making changes. For disposable automated
test environments only, set `OM_INSTALL_ASSUME_YES=1` to skip that confirmation.

By default, the installer also configures the latest Python 3.14 available to
pyenv, the current Node.js LTS, Python and Node developer tools, Vim, Neovim,
and Tmux plugins, configured Mason tools, and Treesitter parsers. Set
`OM_PYTHON_VERSION` to select a specific Python release.
Disposable test runs may skip these slower stages with
`OM_INSTALL_SKIP_TOOLCHAINS=1` or `OM_INSTALL_SKIP_PLUGINS=1`.

Start a new login shell after installation.

### Fedora and safe reruns

`scripts/lib/install-platform.sh` contains the Fedora package policy, based on
installed development packages and CLI providers on the Fedora Asahi host. DNF
supplies the compiler/Python build dependencies, Zsh, tmux, fastfetch and Just;
Homebrew supplies Neovim and the selected CLI tools. Fedora's `zlib-devel` and
`wget` capabilities can resolve to zlib-ng and wget2 packages. The installer does
not add third-party RPM repositories, install Asahi kernels/drivers, change boot
or SSH configuration, or provision personal services/projects such as Ollama and
EdgeTTS. Fedora keeps its existing terminal; the Ghostty Ubuntu installer is not
used there. This does not replicate every package installed on the reference host.

Reruns preserve matching configuration links and reuse existing tool managers.
If pyenv or nvm cannot be detected but their target directory already exists,
installation stops rather than deleting that directory. Repair the installation
or PATH before retrying. A rerun is not a frozen environment: package installation
may update requested packages/dependencies, Node LTS and Python selection may
change, and plugin bootstrap restores the repository's locked versions. Use the
existing toolchain/plugin skip flags when intentionally preserving those layers.

Failure diagnostics use the installer's final exit status, rather than reporting
expected third-party probes as failures on macOS Bash 3.2. Unhandled failures in
commands, functions, command substitutions and subshells still abort and report
failure.

Focused policy tests do not invoke the installer or real package managers:
`python3 -m unittest tests.test_install_platform`.

## Shared host paths

`config/paths.sh` is the source of truth for host paths needed by interactive
shells and unattended scripts. It currently defines `PROJECTS_DIR`. Supported
callers may select a machine-specific replacement with `OM_PATHS_FILE`.
`omnivoice_m4128_half` also accepts `OMNIVOICE_REMOTE_APP` when the remote
checkout differs from the local one.

## Daily Paper audio logs

On the configured Daily coordinator, use `watch -n 1 daily-paper-logs` for the
last two lines of each worker log, selected post/date and recorded stage states.
The thin `scripts/daily-paper-logs` shim requires the local Daily Paper checkout
at `${AUTOMATION_ROOT:-${PROJECTS_DIR:-$HOME/Desktop/tutoriais_e_cursos}/daily-paper}`
(with AUTOMATION_ROOT selecting the checkout directly). It delegates all policy
to `maintenance/daily-paper-logs.sh` there; see that repository's README.
Requires Bash and Python 3.9+. It does not run its own watcher, query Queue/SSH,
start workers or clean runtime files. Without a recorded in-progress marker it
explicitly displays last-known audio, not a claim of current generation.

## Local site Git automation lock

Bash callers that mutate a shared local site checkout source
`scripts/site_git_automation_lock`, call `site_git_lock_acquire "$repo"`, and
arrange `trap site_git_lock_release EXIT` after successful acquisition. The repo
must have a `.git` directory. Acquire/release belong in the same owning shell,
not a command substitution; acquire is not reentrant. Source the helper once
before acquiring. Release is safe to call again after it has completed.

`SITE_GIT_LOCK_TIMEOUT_SECONDS` remains a nonnegative integer (default 60;
0 means an immediate attempt). An unavailable tool fails with 69, invalid
configuration with 64, and contention timeout with 75. Never ignore acquisition
failure and continue a Git mutation. Unknown operating systems fail closed.

- **macOS:** preserves `/usr/bin/shlock` and the legacy
  `.git/om-site-automation.lock` PID-file protocol. `SITE_GIT_SHLOCK_BIN` retains
  its trusted executable override. Release removes the file only when its PID
  matches the caller; stale-owner handling remains delegated to shlock. A stale
  PID file may need a second attempt, so a zero timeout can fail during recovery.
- **Linux:** requires Bash 4+ and util-linux `/usr/bin/flock`; select another
  absolute executable with `SITE_GIT_FLOCK_BIN`. An explicit shlock override on
  Linux is rejected, not silently ignored. A dynamically allocated descriptor
  holds an exclusive lock on `.git/om-site-automation.flock`. The file is opened
  without truncation and **is never unlinked by release**. Closing the final
  inherited descriptor releases the kernel lock, including after a process
  crashes; no stale-PID cleanup is necessary. Other flock errors propagate.

Linux child processes inherit the descriptor deliberately. Protected Git work
must remain protected if its shell crashes. If a child outlives the caller,
release/exit of the parent alone does not release that child's copy: the lock
remains until the child closes it or exits. Do not launch unrelated detached
processes while holding the lock. Callers must finish their protected child work
before release. Existing consumers' synchronous subprocesses fit this contract.

These are **local, cooperative, non-interoperable backends**, not distributed
locking. Every writer to a checkout must use the same protocol. Linux refuses
an existing legacy `.lock` entry (including a symlink); inspect ownership and
drain old consumers before migrating rather than deleting evidence automatically.
This check is not an atomic bridge to a concurrently started shlock writer.
Drain all holders and waiters before changing backends, replacing/synchronizing
`.git`, or restoring a backup. Never unlink/replace the Linux `.flock` inode
while a holder or waiter exists: new callers could otherwise lock a different
inode. A retained file does not mean a lock is currently held, and copying its
bytes to another machine does not copy the kernel lock. Network/shared-filesystem
semantics and cross-host synchronization are not validated by this helper.
The `.git` directory must be trusted; path checks are not a defense against a
local actor concurrently replacing its entries.

Focused tests: `python3 tests/test_site_git_lock.py`. They use disposable repo
directories and bounded test-owned processes, not the real site or services.
Native macOS tests cover the PID protocol; native Fedora tests cover descriptor
exclusion, timeout, waiters sharing one inode, crash/child lifetime, and failure
cleanup. Platform-specific tests skip on the other OS. These tests do not prove
publication, Queue ownership, or safe deployment into an active consumer.

## Optional Docker route-PMTU MSS correction (Linux)

[`scripts/docker-route-pmtu.py`](scripts/docker-route-pmtu.py) and
[`config/systemd/docker-route-pmtu.service`](config/systemd/docker-route-pmtu.service)
are **opt-in**, not installed by `install.sh`. They preserve the tested host
helper/unit byte-for-byte; a checkout update does not replace installed copies.
The helper's review-warning docstring is retained intentionally.

Requires rootful local Docker (`/var/run/docker.sock`), Python 3, systemd,
iptables/ip6tables with the **nf_tables** backend and the TCPMSS extension.
Application requires firewalld to report **inactive**; it never starts it or
changes its backend. This path was validated on Fedora Asahi, not every installer
platform. It is not a macOS Docker Desktop or rootless Docker fix.

Eight comment-owned mangle/FORWARD rules clamp forwarded TCP SYN and SYN-ACK
using kernel source/destination route PMTU. They cover both IP families and both
directions for `docker0` and the `br-+` interface-prefix selector. Reserve
`docker0`/`br-*` for Docker: custom Docker bridge names outside that set are not
covered, and non-Docker bridges using those names would be overmatched.
`check-scope` verifies current naming, not future interface ownership. Default-
named bridge recreation needs no rule reload. No outbound uplink, gateway,
numeric MSS/MTU, NAT, DNS, route or sysctl change is configured.

Mangle/FORWARD precedes the filter established-connection fast path, so returning
SYN-ACKs are handled too. An already smaller MSS is not raised. This affects new
TCP handshakes, not existing connections or UDP/QUIC. A dead VPN peer retaining
its route **does not silently fall back** to another uplink. Kernel-known PMTU
can still miss downstream black holes or asymmetric-path constraints.

### Manual installation and checks

Run from this repository root only with explicit host-change authorization.
First retain a private before-state (`iptables-save -c`, `ip6tables-save -c`,
routes and unit state); never commit it or restore it wholesale. Confirm trusted
root-owned destination parents, absent installation paths (including symlinks),
and no pre-existing `docker-route-pmtu:20260910:v1` rules. Stop on conflicts.
Already-installed hosts need no reapplication merely because source was updated.

```sh
python3 scripts/docker-route-pmtu.py plan-apply
python3 scripts/docker-route-pmtu.py plan-remove
sudo python3 scripts/docker-route-pmtu.py check-scope
sudo python3 scripts/docker-route-pmtu.py apply
sudo iptables-save -c -t mangle
sudo ip6tables-save -c -t mangle
```

Require exactly four owned rules per family and a real bounded Git regression
on the original Docker network before persistence. Do not zero counters. On
failure, use `sudo python3 scripts/docker-route-pmtu.py remove` and retain the
incident evidence. Application reconciles attempted additions after uncertain
command failure; cleanup errors report `ROLLBACK UNRESOLVED` without masking the
original error. Inspect exact owned state rather than blindly retrying.

After the runtime regression passes, inspect the actual Docker unit/drop-ins
for ordering compatibility. If `/usr/local/libexec` is absent, create it
root-owned0755; do not change an existing directory's permissions. With the two
installation paths still absent:

```sh
sudo install -m 0755 -o root -g root scripts/docker-route-pmtu.py /usr/local/libexec/docker-route-pmtu
sudo install -m 0644 -o root -g root config/systemd/docker-route-pmtu.service /etc/systemd/system/docker-route-pmtu.service
sudo systemd-analyze verify /etc/systemd/system/docker-route-pmtu.service docker.service
sudo systemctl daemon-reload
sudo systemctl enable --now docker-route-pmtu.service
systemctl is-active docker-route-pmtu.service
systemctl is-enabled docker-route-pmtu.service
```

Stop on any failed step. Verify effective unit/drop-ins before starting; do not
restart Docker or reload firewalld. The new oneshot runs before Docker on future
starts; `PartOf=docker.service` follows Docker stop/restart, not the reverse.
Docker Wants rather than Requires it: a failed clamp unit does not stop Docker,
so unit success remains a readiness check. Boot application does not query the
not-yet-started Docker API; the naming contract must remain valid.

### Rollback and validation limits

For installed copies, disable only this unit, then reconcile its exact rules:

```sh
sudo systemctl disable --now docker-route-pmtu.service
sudo /usr/local/libexec/docker-route-pmtu remove
```

Removal uses full rule specifications and the unique comment, not line numbers
or table flushes. Verify the owned comment is absent in both families. Remove
only verified task-owned installed files afterward and run `systemctl daemon-reload`;
do not stop Docker or restore other operators' firewall state. The helper lock
is `/run/docker-route-pmtu.lock`; never unlink it while a helper holds or awaits it.

Focused checks: `python3 -B tests/test_docker_route_pmtu.py` (seven mocked tests,
no firewall commands). Actual Fedora validation separately passed a full clone
on the original bridge and confirmed both-direction MSS reduction and preservation
of a smaller MSS. The user independently reported successful clones with and
without WireGuard. Those observations are **not** proof of reboot behavior, IPv6
dataplane, automatic dead-peer fallback, or support on every uplink. IPv6 rules
do not enable IPv6 addressing/forwarding. Do not run disruptive transitions or
production workloads merely to validate a source checkout.

## Local EdgeTTS command

`edgetts` (no hyphen) is launched by `scripts/edgetts` from the local checkout at
`$PROJECTS_DIR/edgetts`, with cache data in that checkout's `.cache/edgetts/`.
It is not installed by Homebrew Bundle: do not add `uv "edgetts"` to the Brewfile
when exporting installed tools. The bootstrap installs uv, not this personal
project. Clone or synchronize the project separately, including `pyproject.toml`
and `uv.lock`, before using the command on a new machine.

The launcher uses `uv run --locked --no-dev` and may install Python/dependencies
on first use. It preserves stdin, arguments, and the caller's working directory.
It accepts inherited `PROJECTS_DIR`, an `OM_PATHS_FILE` replacement, `EDGETTS_DIR`,
and `EDGETTS_CACHE_DIR`; absent overrides, paths come from `config/paths.sh`.
`clear_tts_cache` prefers this launcher for a local checkout and still accepts
`EDGETTS_BIN` for an explicit executable override.

Existing editable uv tool installations are not removed automatically. The Zsh
configuration puts `dotfiles/scripts` ahead of `~/.local/bin`; use `rehash` or
open a new shell if an existing session still resolves the old command. External
callers with a different PATH should use `$HOME/dotfiles/scripts/edgetts` directly.
Audio generation sends text to Microsoft's online TTS service.

## Manual host synchronization

`scripts/run_all_hosts` owns the default fleet (`m132`, `m4128`, `fedoraair`),
validates/deduplicates additional SSH aliases, and runs SSH commands. Existing
`run_all_hosts 'COMMAND'` calls still use a TTY. A failed command or SSH connection
is reported without stopping the remaining hosts; a final summary lists failures,
and the script exits with the first failed SSH invocation's status (zero if all
succeeded). No failed command is retried. Use `--no-tty` for unattended calls,
`--host HOST` for exactly one destination, or `--list` to list the fleet without
contacting it. For programmatic reads, `--host HOST --capture 'COMMAND'` emits
only SSH stdout/stderr, disables TTY/stdin and password prompts, and uses a
10-second connection timeout. It replaces the wrapper with SSH so the caller
can enforce a whole-command timeout directly.

```sh
run_all_hosts --list --additional-hosts utmvm1
run_all_hosts --additional-hosts utmvm1 -- 'hostname'
run_all_hosts --host utmvm1 --no-tty 'mkdir -p ~/.config'
```

`scripts/synchosts` uses that fleet and delegates remote operations to
`run_all_hosts`. Projects, Pi, and shared directories use two phases: collect
from every peer into the caller, then distribute the collected files to every
peer. Additional hosts participate in both phases. Optionally add hosts for one
invocation:

```sh
synchosts --additional-hosts utmvm1 another-vm
```

Without that option, no additional hosts are used. `--help` shows usage without
running synchronization, and invalid arguments are rejected before side effects.
`shared_directories` lists the common home-relative directories; projects, Pi,
and tmux have separate path variables because their options differ. Local paths
use `$HOME`; remote paths use `~`, so
the sender's macOS/Linux absolute home is never reused on another machine. The
projects path remains `~/Desktop/tutoriais_e_cursos` on each host.

An SSH alias matching the caller's short hostname (case-insensitively) is
excluded from rsync transfers; arbitrary aliases for the same machine are not
automatically resolved. `--update` skips newer destination files and `.git` is
included. The existing runtime/dependency/build exclusions remain in force,
including `.omnews-data/`, `node_modules/`, and `dist/`. This is not conflict-aware
synchronization: concurrent edits, equal-mtime divergent files, clock differences,
and copied Git internals can lose changes or leave inconsistent state. Stop
agents/writers on participating directories first, including ephemeral runners.
Pi synchronization still includes credentials, configuration, and resource
snapshots, but excludes agent sessions; only add trusted hosts. Symlink targets
and paths inside files are copied verbatim, not rewritten for the receiving
machine.

Hosts need SSH, rsync, Zsh, and `trash` or GIO (`gio trash`, notably on Linux).
Directories are created relative to each host's own home before collection or
distribution, so an empty new peer can
contribute nothing and then receive the collected files. Failed prerequisites,
directory preparation, or transfers stop the script with a failing exit status.
A failed collection prevents distribution; already completed local changes are
not rolled back. A distribution failure can leave only some peers updated.
Unavailable hosts therefore prevent a successful complete run; no retry is made.
Prerequisite checks depend on helper exit statuses: `pullall` currently does not
reliably propagate individual `git pull` failures, so inspect its output. This
script is not a clean-Git gate.

### Manual idle cleanup boundary

Run `synchosts` only after **all** work is idle, including audio generation,
retries, upload, publication and deploy continuations. It does not establish
Queue ownership or stop Pi/Omnews. A live agent-home consumer or unavailable
local Docker inspection blocks transient cleanup, rather than being killed.
Deploy the updated scripts to every participating host before using this path.

Before transfers, every host (including additional hosts) previews
`clear_sannux_transients`, runs `stop_omnivoicetts`, then applies transient
cleanup. OmniVoice stop keeps its existing process-match scope: TERM, bounded
wait, KILL if necessary, and a final no-writer check **before** generic cache
clearing. Inspection failure or a surviving matching writer prevents clearing.

`clear_sannux_transients` defaults to preview. `--apply --idle-confirmed` is the
explicit standalone destructive mode. It removes only generated
`~/sannux-data/agent-homes/<name>.ephemeral-runs/run.XXXXXX` directories (six
alphanumeric suffix characters) and the contents, including hidden entries, of
`pi-daily-paper-sessions`. It preserves that directory, namespace directories,
and persistent Pi/Codex auth/config homes. Canonical owned roots are mandatory;
symlinked roots and mounted subtrees are refused. Links inside disposable
contents are unlinked, never followed. Unexpected temporary names are reported
and preserved; custom roots outside this fixed tree are not swept.

Python with symlink-safe `shutil.rmtree`, `ps`, and a reachable local Unix-socket
Docker context are required when candidates exist. Checks are not a launcher
lock: the operator must keep work idle until maintenance ends. There is no
force-bypass for an uninspectable or busy owner.

Sync excludes `.scratch/`, `.cache/`, `.astro/`, transient Sannux homes, Daily
sessions, known agent session stores, Linux Daily node_modules and legacy
Daily hook state. Exclusions apply in both directions and **do not erase old
copies**. Incident Scratch evidence stays on its originating host. Persistent
auth, resources, configuration, unrelated workspaces and intentional shared
backups keep their existing transfer behavior.

Daily coordinator/worker attempts, audio, consumer logs and trusted markers are
**not generic cache** and are not removed here. Their retention belongs to
Daily Paper's existing `maintenance/prune-runtime-history.sh`, which currently
covers five newest runs/briefings, current-day protection and Trash. Extending
that tool to remote TTS bundles, with active/unresolved/retry protection and
Linux-compatible Trash, remains separate work; do not substitute `rm -rf`
or silently drop failed attempts to make this cleanup look complete. GIO/Trash
moves do not empty Trash or necessarily free disk space immediately.

Shared data uses neither `--delete` nor deletion markers. A file removed from
only one host can return, including from a host that was offline. For intentional
fleet-wide removal, stop affected writers and move the exact intended path to
Trash on every participating host; check the command's failure summary. For
example, after replacing the placeholder with the authorized path:

```sh
run_all_hosts 'source ~/.zshrc; trash "$HOME/path/to/remove"'
```

Do not add `|| true`: it conceals failures and a surviving copy can reappear.
This is not automatic versioned backup: ordinary rsync overwrites do not move
every previous file version to Trash.

Tmux remains separate: publish the caller's portable snapshot once to each peer,
never collect or merge remote tmux snapshots. Old local and remote resurrect
entries (including dotfiles and symlinks) go through `trash`, not `rm` or rsync
`--delete`. Remote cleanup explicitly loads that peer's `.zshrc` when present so
Linuxbrew-installed `trash` is available to a non-interactive SSH command. Failed
Trash operations abort; a later transfer failure may require recovering that
peer's previous snapshot from Trash.

Before tmux transfers, `scripts/lib/prepare_tmux_resurrect.py` stages a temporary
copy of the resurrect directory. In the snapshot referenced by `last`, only the
pane-directory field's exact local-home prefix becomes `#{HOME}`, a tmux format
expanded on the destination machine. Older `~/...` directory fields are upgraded
too; commands and other fields are untouched. Do not use literal `~` here:
resurrect expands it for new windows, but not new sessions or split panes, which
can silently fall back to the home directory. The staged `last` points to the
staged snapshot using a relative link, even when the original link was absolute. The local snapshot and
link are not edited. If staging fails, tmux transfers are skipped; other copies
continue. Staging requires Python 3; the temporary staging directory is also moved to
Trash on script exit. A staging failure skips tmux transfers and makes the final
exit status nonzero, even if data transfers succeeded.
Staged `#{HOME}/...` paths were checked with local tmux 3.7c through resurrect's
actual new-session, new-window, and split-pane functions, including directories
with spaces. Other hosts/versions and full application restoration have not
been verified. If a bad restore was subsequently saved, its original project
path may already be lost; recover that snapshot from the source or a backup
before synchronizing again.

`scripts/zsh_history_sync.py` uses the same fleet and SSH runner. It accepts
`--additional-hosts HOST ...` and `--dry-run` (which still reads remote histories).
It skips the local hostname and unavailable hosts, retaining the 120-second
per-host read timeout, merge rules, atomic replacement, and ten local backups.
Its existing Python 3.14 launcher requirement is unchanged. A host-list failure
aborts before history is modified. `synchosts` forwards additional hosts to the
history merge as well as rsync; service stops still use only the default fleet.

No installation or reload is needed after editing this script. Running it has
real effects, including history synchronization, tmux cleanup, service stops,
`pullall`, and remote writes. Check syntax without running synchronization with
`zsh -n scripts/synchosts`. Run `python3 -m unittest tests.test_synchosts` for
isolated CLI regression tests using fake SSH/services/Trash and real rsync between
disposable homes; those tests do not contact the fleet or validate the real Trash
provider's ability to recover files.

## Zsh startup and local service environments

The interactive loader sources `~/.env` when it is a file, or each
`~/.env/.env.*` file when it is a directory. Keep these files private and split
by service so containers and unattended consumers can select only what they
need. This shell loader still loads all of them; it does not provide container
or queue environment isolation.

Guard macOS Keychain assignments in those local files, rather than skipping an
entire service file on Linux:

```sh
if [ "$(uname -s)" = Darwin ] && command -v security >/dev/null 2>&1; then
  export EXAMPLE_API_KEY="$(security find-generic-password -s example-service -w)"
fi
```

On Linux (or without `security`), this preserves an inherited value and leaves
an unset variable unset. Supply Linux values through the parent environment or
private per-service configuration loaded by the appropriate consumer. There is
no automatic Linux secret-store provider, and skipping a Keychain lookup does
not create a credential. Never commit real values. Unguarded `security` calls
can trigger Fedora's PackageKit command-not-found searches in every restored
shell.

CLI completion generation for Codex, GH, Just, Docker and OMQueue is deferred
until the first completion request for each command in each shell. Successful
loads register the generated completion directly; failed generation can retry
on the next Tab. Existing availability gates remain: Just's override requires
`Justfile` in the shell's startup directory, and Docker's override requires
`~/.docker/completions/_docker`. Other completions remain managed by the existing
configuration. NVM and Pyenv still initialize before the prompt so the toolchain
PATH is ready for the first command. The selected NVM Node directory takes
priority over Homebrew's Node, including when a new Homebrew dependency installs
its own Node; the NVM default alias is not changed by this PATH correction.

Automatic pane-title updates run without blocking Zsh startup inside tmux. The
title can appear slightly later and automatic tmux updates are best-effort and
silent; an overlapping restore or another title writer can still replace it.
Manual `title` commands remain synchronous and report errors. Outside tmux, the
startup title update remains synchronous.

Changes apply to new shells; do not restart a live tmux server just to apply
them. Focused isolated checks: `python3 -m unittest tests.test_zsh_startup`.
These do not measure a real restore or verify live credentials.

## Tmux window picker

The `prefix Ctrl+l` / right-click window picker lists windows across sessions by
most recent visit. Switching windows or attaching/switching sessions updates the
order; terminal output does not. Unvisited windows fall back to session/index
order. Typing a query still ranks matches by relevance.

Visit history lives only in the running tmux server and starts empty after a
server restart. Reload the tmux config (`prefix r`) to enable tracking in an
existing server. Focused regression checks (requires tmux and fzf):
`python3 -m unittest tests.test_tmux_fzf`. They use disposable isolated servers.

## Pi Coding Agent

The installer links the static configuration under `pi/agent/` into
`~/.pi/agent/`. Credentials, sessions, trust decisions, generated model state,
and machine-specific model configuration remain local.

## Optional runner keepwarm

`scripts/keepwarm` launches a background loop that periodically calls configured
Sannux runners to refresh persistent authentication. These are real provider
calls; it is not a read-only authentication check. Starting it terminates older
matching workers. Linux requires procps `pkill` with `--ignore-ancestors` (`-A`)
so replacement does not kill its own launcher; macOS already excludes ancestors.
Load the normal runner environment before invoking it.

Codex maintenance pings omit `--model` by default, so the persistent Codex
runner uses its own configured default. An optional nonempty
`KEEPWARM_CODEX_MODEL` environment variable supplies one literal model argument;
unset or empty values keep the default. Low reasoning and the other existing
Codex flags are unchanged. This setting does not change the Pi ping route or
Daily Paper's editorial model selection. Supply any override in the environment
of the keepwarm owner, not only in an unrelated interactive shell.

After deploying script changes or changing the override, the existing background
owner must be restarted through its normal authorized lifecycle to use them.
Deployment alone does not update an already-running loop. Restarting makes real
provider calls and terminates older matching workers; do not do it as a syntax
or configuration check.

Focused model-argument tests: `python3 tests/test_keepwarm_model.py`. They fake
pkill, Sannux, sleep and OS selection, use disposable HOME/process groups, and
never contact a provider or signal an existing keepwarm owner.

The isolated regression test runs no provider calls and only signals uniquely
named fixture processes: `python3 -m unittest tests.test_keepwarm`.

## Related public repositories

This repository is only one part of the development environment. Some of its
configuration and commands integrate with other repositories, usually checked
out under `$PROJECTS_DIR`:

- [omskills](https://github.com/luizomf/omskills) maintains the Pi skills;
- [ompi](https://github.com/luizomf/ompi) maintains the Pi extensions;
- [loudterm](https://github.com/luizomf/loudterm) provides local audio and TTS
  workflows used by some commands;
- [sannux](https://github.com/luizomf/sannux) provides the sandboxed containers
  used by the `sannux` commands;
- [otaviomiranda.com.br](https://github.com/luizomf/otaviomiranda.com.br)
  provides the site checkout expected by publishing commands;
- [edgetts](https://github.com/luizomf/edgetts) provides the local EdgeTTS project
  used by `scripts/edgetts`;
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) provides the image
  upscaler used by `imgupscale`.

These repositories are not required for the base installation, but the related
commands will not work without them.

## License

See [LICENSE](LICENSE).
