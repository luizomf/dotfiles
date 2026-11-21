# Installer maintenance

## GitHub access on a fresh machine

The README's clone URL uses HTTPS and needs no SSH setup. An existing checkout
may use an SSH origin; there, `Host key verification failed` means SSH could not
verify GitHub's identity, not that the repository is broken. Verify the offered
fingerprint against GitHub's
[published fingerprints](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)
before accepting it, then test with `ssh -T git@github.com`.
`Permission denied (publickey)` is an account-key problem instead. Never disable
`StrictHostKeyChecking` or blindly append `ssh-keyscan` output. The installer
provisions neither host trust nor keys.

A one-off HTTPS update from a clean `main` checkout, without touching `origin`:

```sh
cd ~/dotfiles
git fetch https://github.com/luizomf/dotfiles.git main
git merge --ff-only FETCH_HEAD
```

If the branch diverged, investigate instead of forcing. Updating the checkout
does not require rerunning `install.sh`.

## One package catalog

Edit [`config/packages.list`](../config/packages.list) for native and Homebrew
package selections. `install.sh` and `homebrew/Brewfile` read it directly; there
is no generated file or second list.

Each non-comment line is whitespace-separated:

```text
platforms provider package [option]
```

- Selectors: platform names from `config/install-platforms.list` (`darwin`,
  `ubuntu`, `debian`, `fedora`, `arch`, `alpine`, `lfs`) or Linux package
  managers (`apt`, `dnf`, `pacman`, `apk`), comma-separated without spaces. A
  row matches when either the platform or its manager matches; `apt` covers
  Debian and Ubuntu. The macOS Brewfile selects only `darwin` rows.
- `native`: apt, DNF, pacman, or apk. Use each distro's actual package name;
  differing names need separate rows.
- `brew`: Homebrew formula on the selected platforms.
- `cask`, `tap`, `uv`: macOS Bundle declarations only.
- Optional fourth field: `unlinked` for a macOS formula, `trusted` for a tap, or
  the executable to probe on an LFS Brew row (for example, `neovim nvim`).
- Whole-line `#` comments only.

```text
darwin,apt,fedora,arch brew bat
apt,fedora native fd-find
arch native fd
darwin brew fd
```

Do not add every package to `install.sh`'s `required_commands`: that list checks
the core installation contract. Runtime bootstrap (nvm, pyenv, uv), Prettier,
Python development tools, and editor plugins keep their own setup code and
lockfiles.

`homebrew/Brewfile` is a small Ruby reader of the catalog, so
`brew bundle --file=~/dotfiles/homebrew/Brewfile` works on macOS. Never run
`brew bundle dump --force` over it.

## Adding a Linux distribution

`config/install-platforms.list` is the registry: each row declares the canonical
platform, its exact `/etc/os-release` IDs, and its package manager. Unknown IDs
and OSTree systems are rejected; `ID_LIKE` never opts a derivative in.

For a distro on an existing backend (`apt`, `dnf`, `pacman`):

1. Add its registry row; no new `case` branch in `install.sh` is needed.
2. Check the manager-shared rows in `config/packages.list` against its
   repositories and add platform-specific rows where needed. DNF and pacman rows
   currently name Fedora and Arch explicitly.
3. Add detection and package tests in `tests/test_install_platform.py`. A new
   package manager also needs a backend in `scripts/lib/install-platform.sh`.

Ubuntu's locale setup is an explicit Ubuntu-only step; the `fd`/`bat`
compatibility links apply to APT hosts. No Linux platform installs Ghostty, but
its configuration is still linked.

## Platform notes

Never run the whole installer as root; it needs sudo (or `doas` on Alpine) for
the normal user. Unattended mode uses non-interactive sudo and grants no
privileges.

### Debian

APT for native dependencies and the shared APT Homebrew selection for CLI tools
(including Neovim and tmux), plus the normal pyenv/nvm workflows. The system
locale is left alone.

### Arch and Omarchy

`ID=arch` and `ID=omarchy` are the same platform. Native dependencies use
`pacman -S --needed` against the existing sync database; the installer never
runs `pacman -Sy`, upgrades the system, or builds AUR packages. If downloads
fail on an outdated database, update the host normally and rerun. CLI tools use
the Fedora Homebrew selection. Omarchy's mise stays installed, but the shell
puts pyenv/nvm first.

nvm is always installed to `~/.nvm`, even when `XDG_CONFIG_HOME` or `NVM_DIR`
points elsewhere; other existing nvm installations are left alone.

The installer switches the login shell to Zsh and replaces Neovim, Ghostty, and
fastfetch configuration, with backups under `~/.dotfiles-backups/`. Bash
configuration, Hyprland, locale, services, and repositories are untouched,
though nvm's installer may append to `.bashrc`.

### Alpine

Native `apk` packages only (no Homebrew, nvm, pyenv, or glibc layer). Install
Bash and Git first, enable the `main` and `community` repositories, and
authorize `doas` or sudo. Targets Alpine 3.24 with musl.

npm installs Prettier and Pyright into `~/.local`. Python stays
`/usr/bin/python3` (`OM_PYTHON_VERSION` is ignored), including for the tmux
Python popup. Neovim uses native Ruff, Taplo, Lua Language Server, Rust
Analyzer, and StyLua ahead of Mason, which supplies the rest. OMXTerm (Electron)
and Ghostty do not run on Alpine: Electron's glibc runtime fails even with
`gcompat`.

### LFS

`ID=lfs` and `ID=lebasix`. The `linuxbrew` backend selects only LFS formula
rows. The host must supply a working glibc base, Bash, Git, HTTPS curl,
`/usr/bin/python3` 3.14 or newer, sudo, and Homebrew's runtime prerequisites
(`stty`, `flock`, `nice`). Network, locales, boot, and services belong to the
host.

- **Native first:** a command already present in the host paths
  (`/usr/local/sbin`, `/usr/local/bin`, `/usr/sbin`, `/usr/bin`, `/sbin`,
  `/bin`) skips its formula. This is presence detection only, and Homebrew may
  still install its own copies as dependencies. In LFS Zsh sessions, host paths
  precede Brew paths so those dependencies do not shadow the native Python.
- **No compiler:** without `cc` in the host paths, the installer runs
  `brew install glibc` before the formulas and `brew postinstall gcc` after
  (which also repairs a failed earlier post-install). Rerun after fixing a
  failure; do not delete the Brew prefix.
- **Plugin compilers:** native `cc`/`c++` first, otherwise the highest complete
  `gcc-N`/`g++-N` pair under `brew --prefix gcc`. Explicit `CC`/`CXX` are kept
  and must answer `--version`. This applies only to the plugin subprocess; later
  parser rebuilds need usable compilers or explicit `CC`/`CXX`.
- **Python tools:** standalone uv in `~/.local/bin` (an existing Homebrew uv is
  removed), with Pyright, mypy, and Ruff from `uv tool install`.
  `OM_PYTHON_VERSION` is ignored.
- **DNF-based roots** get native `libatomic`, which Pyright's downloaded Node
  needs when Brew's Node is not on PATH (for example, over non-interactive SSH).
  Repair an existing root with `sudo dnf install libatomic`.
- GNU Patch maps as `gpatch patch`: the formula is `gpatch`, the executable
  `patch`.

## UTF-8 locale

On every platform, `zsh/config/env` sets `LANG` only when `LANG`, `LC_ALL`, and
`LC_CTYPE` are all unset or empty. It picks an installed `C.UTF-8`, then
`en_US.UTF-8`, and keeps it only if Zsh itself counts a UTF-8 character
correctly (`locale -a` and a packaged Zsh can disagree). `LC_ALL` is never set,
and explicit choices are preserved.

To check a new session: `locale charmap` should print `UTF-8`, and
`s='é'; print -- ${#s}` should print `1`. Inside tmux, fix future panes with
`tmux set-environment -g LANG en_US.UTF-8`.

## Verification

Isolated policy checks (no package installation):

```sh
python3 -m unittest tests.test_install_platform
bash -n install.sh scripts/lib/install-platform.sh scripts/lib/install-python.sh
shellcheck -x install.sh scripts/lib/install-platform.sh scripts/lib/install-python.sh
nvim --clean --headless -i NONE -l tests/test_nvim_alpine.lua
```

The Bundle DSL test needs Ruby and skips without it. The shell tests also run on
macOS Bash 3.2.
