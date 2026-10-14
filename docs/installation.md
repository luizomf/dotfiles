# Installer maintenance

## GitHub access on a fresh machine

The public clone URL in the root README uses HTTPS and does not require GitHub
SSH host trust or a personal SSH key. An existing checkout may instead have an
SSH origin. In that case, `Host key verification failed` during `git pull` means
SSH could not establish trusted server identity; it is not evidence that the
repository files or installer are broken. The exact cause can be a missing trust
entry or a conflicting key, so do not assume every failure is first use.

For SSH, verify the offered fingerprint against GitHub's independently trusted
[published host-key fingerprints](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)
before accepting or provisioning the host key. Then test the connection with
`ssh -T git@github.com`. Account authentication is separate: a
`Permission denied (publickey)` result needs the appropriate account key/access,
not a host-verification bypass. The installer does not provision either trust or
private keys. Never disable `StrictHostKeyChecking`, blindly append
`ssh-keyscan` output, or remove a conflicting trust entry without verification.

For this public repository, a one-off HTTPS update is an alternative. First
confirm that `~/dotfiles` is a clean checkout on `main` (`git status --short`
should be empty); preserve local changes or branch work before proceeding:

```sh
cd ~/dotfiles
git fetch https://github.com/luizomf/dotfiles.git main
git merge --ff-only FETCH_HEAD
```

This does not change `origin`, SSH trust, or credentials. Later plain pulls
still use the configured origin and may need SSH setup. A diverged branch is not
reset by `--ff-only`; investigate instead of adding `--force` or discarding
local work. Fetching/updating dotfiles does not require rerunning `install.sh`.

## One package catalog

Edit [`config/packages.list`](../config/packages.list) for native and Homebrew
package selections. `install.sh` and `homebrew/Brewfile` consume it directly;
there is no generated file to refresh or second package list to synchronize.
Existing macOS, Ubuntu and Fedora selections are retained (Ubuntu's Zsh is now
declared alongside its other native packages).

Each non-comment line is whitespace-separated:

```text
platforms provider package [option]
```

- Selectors: platform names from `config/install-platforms.list` (`darwin`,
  `ubuntu`, `debian`, `fedora`, `arch`, `alpine`, `lfs`) or their Linux package
  managers (`apt`, `dnf`, `pacman`, `apk`). Combine selectors with commas,
  without spaces. A row is selected once when either the platform or its manager
  matches. `apt` shares both native and Brew selections between Debian and
  Ubuntu; use a platform name for exceptions. The macOS Brewfile selects only
  `darwin` rows.
- `native`: apt on Debian/Ubuntu, DNF on Fedora, pacman on Arch/Omarchy, apk on
  Alpine. Use the package name that each distro actually provides; differing
  names need separate rows.
- `brew`: Homebrew formula/tool on the selected platforms.
- `cask`, `tap`, `uv`: macOS Bundle declarations only. `uv` keeps the existing
  Brewfile's Python-tool selections; it does not configure the Python runtime.
- Optional fourth field: `unlinked` for a macOS formula, `trusted` for a tap, or
  the executable to probe on an LFS-only Brew row (for example, `neovim nvim`).
- Use whole-line `#` comments, not inline comments or shell/Ruby expressions.

For example, bat needs just one declaration:

```text
darwin,apt,fedora,arch brew bat
```

Distro name differences remain explicit:

```text
apt,fedora native fd-find
arch native fd
darwin brew fd
```

Do not add every new package to `install.sh`'s final `required_commands` list:
that checks the core installation contract, not every optional CLI. Runtime
bootstrap (nvm, pyenv, uv), npm's Prettier, Python development tools, and editor
plugins remain in their existing setup code/lockfiles; the catalog does not
replace those workflows.

`homebrew/Brewfile` is a small Ruby reader of the catalog. Normal
`brew bundle --file=~/dotfiles/homebrew/Brewfile` still works on macOS. Do not
run `brew bundle dump --force` over it. Neither the `brewupdate` alias nor
`scripts/updateall` exports the current machine's installed inventory over the
tracked Brewfile anymore; package updates leave the catalog reader intact.

## Adding a Linux distribution

`config/install-platforms.list` is the registry: each row declares the canonical
platform, comma-separated exact `/etc/os-release` IDs, and package manager.
Aliases map to the same platform. Unknown IDs and OSTree systems are rejected;
`ID_LIKE` never opts an untested derivative in automatically.

For a distro using an existing backend (`apt`, `dnf`, `pacman`):

1. Add its registry row. Detection and package-manager dispatch use that row; no
   new `case` branch in `install.sh` is needed.
2. Check the manager-shared rows in `config/packages.list` against its actual
   repositories, and add platform-specific selections where necessary. DNF and
   pacman selections currently name Fedora and Arch explicitly; sharing those
   requires an intentional catalog edit.
3. Add detection/package tests in `tests/test_install_platform.py` and document
   what was actually checked. A new package manager still needs a backend in
   `scripts/lib/install-platform.sh`.

Ubuntu's locale setup remains an explicit Ubuntu-only exception in `install.sh`;
the `fd`/`bat` command-name compatibility links apply to APT hosts. New distros
otherwise keep their system locale. Ghostty is neither installed nor required on
Linux; its configuration is still linked for users who install it separately.
The macOS cask is unchanged.

## Debian

Debian uses APT for native dependencies and the shared APT-platform Homebrew
selection for current CLI tools (including Neovim and tmux). It uses the
existing pyenv/nvm workflows, changes the login shell to Zsh, and links the same
dotfiles with the normal backups. Extra native Python build libraries are
declared for Debian in the catalog. Sudo must already be installed and
authorized for the normal user; do not launch the installer as root.

Debian does not install Ghostty or change the system locale. Ghostty
configuration is still linked, but its executable is not required. Debian 13
ARM64 package availability was inspected read-only; no full Debian installation
has been performed by the agent. The maintainer will test it.

## Arch and Omarchy

The installer recognizes `ID=arch` and `ID=omarchy` as the same package
platform. It does not accept arbitrary `ID_LIKE=arch` derivatives. Keep the host
up to date using its normal update workflow before installation.

Native build dependencies use `pacman -S --needed` against the existing sync
database. The installer deliberately does not run `pacman -Sy`, perform a full
system upgrade, add repositories, or build AUR packages. If an outdated database
causes download failures, update the host normally and rerun. Unattended mode
adds `--noconfirm`; missing sudo authorization or package failures remain fatal.

CLI tools use the same Homebrew selection as Fedora, including the preferred
interactive tmux, while retaining native tmux as a fallback. Python and Node use
the existing pyenv/nvm setup. Omarchy's existing mise installation is not
removed; the dotfiles shell prioritizes its own pyenv/nvm tools.

Node bootstrap explicitly selects `~/.nvm` before invoking nvm's installer,
matching the shell configuration even when `XDG_CONFIG_HOME` or an inherited
`NVM_DIR` points elsewhere. It creates the new target directory before that
call, as upstream requires for an explicit non-default destination. Existing nvm
installations elsewhere (such as `~/.config/nvm`) are left intact, not migrated
or removed. If an older install placed nvm in `~/.config/nvm` but then failed to
load `~/.nvm/nvm.sh`, update the checkout and rerun; no manual move is needed.
An incomplete existing `~/.nvm` still requires manual repair, as before.

The installer switches the login shell to Zsh and replaces the normal dotfiles
targets, including Neovim, Ghostty and fastfetch configuration, with backups
under `~/.dotfiles-backups/`. This is not a transparent addition to Omarchy's
shell/editor defaults. It does not replace Bash configuration, but the existing
nvm bootstrap may append initialization to a shell profile (including `.bashrc`
when launched from Bash). Locale, Hyprland, boot, services, distro repositories
and the installed desktop terminal are left alone. No Linux platform runs a
Ghostty installer.

## Alpine

Alpine uses only native `apk` packages from its existing repositories. Install
Bash and Git first, enable the release's `main` and `community` repositories,
and authorize `doas` (preferred when available) or sudo for your normal user. Do
not launch the entire installer as root. Unattended mode uses `doas -n` or the
existing `sudo -n` behavior; it grants no privileges.

The native path targets Alpine 3.24 with musl. It installs Zsh, tmux, Vim,
Neovim, native Node/Python/uv, build tools, terminal utilities, clipboard tools
and a Nerd Font. It does not install Homebrew, nvm, pyenv, a glibc compatibility
layer, a different init system, containers, or a desktop. It does not upgrade
the distro or rewrite its repositories. Existing non-Alpine package selections
and toolchain setup are unchanged.

With toolchain setup enabled, npm installs Prettier, Pyright and Pi into
`~/.local`, without privileged npm or changing the global npm configuration.
Python remains `/usr/bin/python3`; `OM_PYTHON_VERSION` does not replace it on
Alpine. The checkout's development environment still uses `uv sync --locked`,
with that interpreter and managed Python downloads disabled. A failed sync
retains the existing incomplete-installation reporting and does not prevent
independent configuration steps. `OM_INSTALL_SKIP_TOOLCHAINS=1` skips npm tools
and the development-environment sync, not the native package selection.

The tmux Python popup uses `/usr/bin/python3` on Alpine and LFS; other systems
retain their existing pyenv command.

Neovim uses native Ruff, Taplo, Lua Language Server, Rust Analyzer and StyLua,
while Mason supplies the remaining language servers. On Alpine, native PATH
entries take precedence over Mason's bin directory and native tools are not
requested from the Mason registry. Bootstrap checks their availability before
installing the remaining tools and compiling the Tree-sitter parsers. Other
platforms keep the existing Mason policy. Pi instructions, settings and auth
remain outside this repository; their existing private synchronization is
separate from installation.

This is a native terminal/development subset, not every macOS/Homebrew utility.
The installer does not install OMXTerm/Electron or Ghostty on Alpine; their
configuration links do not imply working binaries. Electron's prebuilt glibc
runtime did not execute in the Alpine experiment, including with `gcompat`.
Generating an AppImage using native squashfs tools did not solve runtime
compatibility, so neither workaround is part of this installer.

Alpine 3.24 ARM64 package installation, Zsh/tmux, Pi version startup, Neovim
plugins, 38 Tree-sitter parsers and Python LSP initialization were exercised in
a disposable VM. After a snapshot reset, the candidate package, Node, Python and
Neovim setup components also passed; repeating the package/Python/Neovim
components passed without Homebrew or managed runtimes. The tmux popup binding
was checked on Alpine and macOS. Those checks are not a completed full-installer
or repeat full-install test. Other Alpine versions and architectures are
unverified.

## LFS

The `lfs` platform accepts exact `ID=lfs` and `ID=lebasix` values. Its
`linuxbrew` backend is distinct from the macOS Bundle backend: it selects only
LFS formula rows, never macOS casks or taps.

Start with a working glibc base, Bash, Git (including submodule and transport
helpers), curl with working HTTPS, `/usr/bin/python3` (3.14 or newer for all
personal scripts), and sudo access. Homebrew's runtime prerequisites must
already work, including `stty`, `flock`, `nice`, and the matching glibc
compatibility libraries required by its portable runtime. Homebrew need not be
preinstalled. Network, certificates, locales, boot, services and the base system
are owned by the host, not this installer. This is not a BLFS bootstrapper or a
promise of compatibility with arbitrary LFS builds.

On a runtime-only base without `cc` in the host paths listed below, the
installer loads or installs Homebrew, runs `brew install glibc` before the
formula batch, and then runs `brew postinstall gcc`. The last step also repairs
an already installed GCC whose earlier post-install failed. Failures stop
installation; correct the reported problem and rerun without deleting the Brew
prefix. This uses Brew's own development runtime, not a replacement for the
operating system's libc. The `cc` presence check is deliberately narrow: it does
not verify headers, startup objects, or partially installed native development
tools.

Before plugin installation, LFS automatically selects C/C++ drivers: native
`cc`/`gcc` and `c++`/`g++` first, otherwise the highest numeric complete
`gcc-N`/`g++-N` pair under `brew --prefix gcc`. Explicit `CC` and `CXX` are
preserved independently, including when only one is supplied. Each value must be
one executable name or path, without flags, and successfully answer `--version`;
unusable choices fail with a correction hint rather than silently falling back.
This validates driver startup, not actual compilation/linking.

Compiler defaults are confined to the plugin subprocess and cover both locked
Neovim restoration and the subsequent tooling bootstrap. They do not affect Brew
package installation or persist in the user's shell. Skipping plugins skips
compiler selection. Later parser rebuilds outside `install.sh` still need usable
compiler names or explicit `CC`/`CXX`, using the installed GCC version; no
global compiler aliases or shell exports are created.

The runtime-only ordering and compiler selection have isolated fixture coverage.
A fresh compiler-free ARM64 base with no Brew, full installation, C/C++
execution, and repeat full installation remain integration acceptance
requirements.

Before requesting formulas, the installer checks each command in host paths:
`/usr/local/sbin`, `/usr/local/bin`, `/usr/sbin`, `/usr/bin`, `/sbin`, `/bin`.
Existing executables are kept and their direct formula requests are skipped.
This is presence detection, not a general version or feature compatibility
solver; the host must supply usable native tools. Inherited Homebrew, nvm, pyenv
and user-tool PATH entries do not count as native. Missing commands come from
Homebrew, installed at its normal Linux prefix if absent. Homebrew still owns
transitive dependencies and may install its own version of a native tool or
library as a dependency. The installer does not unlink those dependencies or
force Homebrew to link against LFS libraries. During installation and in LFS Zsh
startup (`/etc/lfs-release` or `ID=lfs`/`ID=lebasix` in `/etc/os-release`), host
paths precede Brew paths so dependencies do not shadow the native Python or
other base tools. Explicit user-tool paths still retain their normal priority.

Node, Prettier and Pi follow the same native-first formula policy. There is no
nvm installation, pyenv build, or privileged npm installation. Python setup
removes an existing Homebrew uv formula and installs standalone uv in
`~/.local/bin` if absent, so `updateall` can use `uv self update`. Pyright, mypy
and Ruff are installed with `uv tool install` when missing from its tool list;
they are no longer requested as Homebrew formulas. Existing Brew Pyright/Ruff
formulas are left installed, with `~/.local/bin` taking precedence. Tool
installation and the checkout's locked `.venv` sync use `/usr/bin/python3`, with
managed interpreter downloads disabled. `OM_PYTHON_VERSION` does not replace the
native Python. `OM_INSTALL_SKIP_TOOLCHAINS=1` skips uv migration, tool
installation and sync, not the remaining formula selection.

For a Fedora-derived Lebasix rootfs, keep native runtime libraries available for
third-party Linux binaries. In particular, Pyright's Python wrapper may download
Node when Brew's Node is absent from PATH (for example, non-interactive SSH);
that Node requires the native `libatomic` package
(`sudo dnf install libatomic`). This does not require installing Fedora's
compiler toolchain.

GNU Patch uses the formula/command mapping `gpatch patch`: Homebrew names the
formula `gpatch`, but on Linux it installs the `patch` executable. A native
`patch` still skips that formula; its absence must not request a nonexistent
formula named `patch`.

The LFS formula list includes `jq` for Homebrew completion, with the same
native-first policy. Existing installations can run `brew install jq` if
missing; there is no need to rerun the full installer.

On every platform, `zsh/config/env` supplies a UTF-8 `LANG` only when `LANG`,
`LC_ALL` and `LC_CTYPE` are all empty or unset. It selects an installed
`C.UTF-8`/`C.utf8`, then `en_US.UTF-8`/`en_US.utf8`, as reported by `locale -a`,
and verifies that Zsh itself counts a UTF-8 character correctly with that
choice. The native `locale` command and a packaged Zsh can use different libc
locale data; an advertised name alone is insufficient. If none works, it leaves
the environment unchanged. Explicit choices (including `C`) and other `LC_*`
categories are preserved; `LC_ALL` is never set. This runs from `.zshenv` for
login, interactive and non-interactive SSH command sessions, without sourcing
`/etc/profile` or changing system files. After updating an existing checkout,
open a new Zsh session and check `locale charmap` for `UTF-8` and Zsh's own
`s='é'; print -- ${#s}` for `1`. An explicitly invalid inherited locale must
still be corrected at its source. For an existing session with an unusable
automatically selected locale, choose a verified working LANG (for example
`export LANG=en_US.UTF-8`). Inside tmux, update future panes too with
`tmux set-environment -g LANG en_US.UTF-8`; already running shells keep their
own environment. Do not globally force `LC_ALL`.

Zsh is registered in `/etc/shells` if necessary before changing the user's login
shell. Existing configuration targets, including `.vimrc`, are backed up before
linking. Bash configuration is not changed. The tmux Python popup uses system
Python. Vim/Neovim plugins, Mason tools and Tree-sitter parsers retain the
normal editor bootstrap; they are not distro packages. No desktop, terminal
binary, SSH configuration, sudo policy or network configuration is installed or
rewritten. Pi settings and credentials remain outside this repo.

A full install from a clean LFS ARM64 13.0 systemd base (without Homebrew) and a
repeat install completed successfully. The native-first PATH correction was
exercised on the repeat run, not a second snapshot reset. Fresh Zsh resolved
native Python 3.14, Vim, tmux and fzf; native executable and Bash-config hashes
were unchanged. The Vim-config backup survived, and the repeat created no extra
backup or duplicate shell registration. The Python popup binding, locked Python
environment, 14 Mason packages, all 34 configured parser names and Pyright
initialization were checked. Tree-sitter's install task reported 38 languages
including related parsers. Other LFS versions and architectures remain
unverified.

The editor bootstrap rewrote Lazy's own lockfile pin during that historical test
([issue #11](https://github.com/luizomf/dotfiles/issues/11)). The installer now
uses the separate
[locked restore command](nvim-updates.md#locked-plugin-restoration), which
protects the input lock before missing-plugin setup and verifies the installed
commits. Clean/partial and repeat restoration were checked with isolated local
Git fixtures, not a new full LFS installer run.

## Verification

Isolated policy checks (no package installation):

```sh
python3 -m unittest tests.test_install_platform
bash -n install.sh scripts/lib/install-platform.sh scripts/lib/install-python.sh
shellcheck -x install.sh scripts/lib/install-platform.sh scripts/lib/install-python.sh
nvim --clean --headless -i NONE -l tests/test_nvim_alpine.lua
```

The tests exercise platform detection, package-manager arguments, catalog
selection, Bundle declarations, unattended behavior and failure propagation.
Ruby is needed for the inert Bundle DSL test; that test skips if Ruby is absent.
The shell tests also run on macOS Bash 3.2. The Neovim test needs installed
nvim-lspconfig; it mocks platform detection and installation boundaries without
downloading tools or starting language servers.

A full install and a repeat run were tested in a disposable Omarchy ARM64 VM,
including Python/Node, Vim/Neovim plugins, Mason and Tree-sitter. A new Zsh
login resolved both dotfiles tools and Omarchy commands. Plain Arch and x86_64
Omarchy have not had a clean-install test. macOS/Ubuntu/Fedora package
selections were compared with the previous installer; they were not freshly
reinstalled by the agent for this change. The maintainer also reported
successful Fedora KDE and Ubuntu GNOME runs. A follow-up Omarchy test reproduced
the nvm path failure with `XDG_CONFIG_HOME` set, then completed the full
installer with the fix under that same environment; this was recovery from the
failed install, not a snapshot-reset test.
