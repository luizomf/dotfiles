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

`scripts/synchosts` uses that fleet and delegates remote directory creation to
`run_all_hosts`. Its legacy rsync routes are retained for participating hosts;
new fleet members (including additions to the default list) receive every
configured directory, push-only. Optionally add hosts for one invocation:

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

Legacy routes intentionally remain asymmetric: only `m4128` is pulled from, Pi
is push-only, and the duplicate tmux push to `fedoraair` is preserved. There is
no automatic self-host detection. `--update` still skips newer destination files,
`.git` is included, and `--delete` applies only to tmux. This is not conflict-aware
synchronization: deleted files may return and concurrent edits can be lost or
leave Git inconsistent. Stop agents/writers on participating directories first.
Pi synchronization still includes the entire `~/.pi/` tree, including local
credentials and sessions; only add trusted hosts. Hosts need SSH/rsync. Before
each push, the script creates the destination with remote `mkdir -p`, relative
to that host's home. If creation fails, it reports the error and skips that
transfer; the remaining plan continues. Pulls are unchanged. Rsync creates
subdirectories inside each destination as it copies them.

Before tmux transfers, `scripts/lib/prepare_tmux_resurrect.py` stages a temporary
copy of the resurrect directory. In the snapshot referenced by `last`, only the
pane-directory field's exact local-home prefix becomes `#{HOME}`, a tmux format
expanded on the destination machine. Older `~/...` directory fields are upgraded
too; commands and other fields are untouched. Do not use literal `~` here:
resurrect expands it for new windows, but not new sessions or split panes, which
can silently fall back to the home directory. The staged `last` points to the
staged snapshot using a relative link, even when the original link was absolute. The local snapshot and
link are not edited. If staging fails, tmux transfers are skipped; other copies
continue. Staging requires Python 3 and is removed on normal script exit.
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
`zsh -n scripts/synchosts`.

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
