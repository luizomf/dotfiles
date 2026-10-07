# Installer maintenance

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
  `ubuntu`, `debian`, `fedora`, `arch`, `alpine`) or their Linux package
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
- Optional fourth field: `unlinked` for a macOS formula, or `trusted` for a tap.
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
otherwise keep their locale. Ghostty is neither installed nor required on Linux;
its configuration is still linked for users who install it separately. The macOS
cask is unchanged.

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

The tmux Python popup uses `/usr/bin/python3` on Alpine; other systems retain
their existing pyenv command.

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
