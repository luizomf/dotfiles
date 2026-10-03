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

- Platforms: `darwin`, `ubuntu`, `fedora`, `arch` (Arch and Omarchy). Combine
  platforms with commas, without spaces. There is no implicit inheritance.
- `native`: apt on Ubuntu, DNF on Fedora, pacman on Arch/Omarchy. Use the
  package name that each distro actually provides; differing names need separate
  rows.
- `brew`: Homebrew formula/tool on the selected platforms.
- `cask`, `tap`, `uv`: macOS Bundle declarations only. `uv` keeps the existing
  Brewfile's Python-tool selections; it does not configure the Python runtime.
- Optional fourth field: `unlinked` for a macOS formula, or `trusted` for a tap.
- Use whole-line `#` comments, not inline comments or shell/Ruby expressions.

For example, bat needs just one declaration:

```text
darwin,ubuntu,fedora,arch brew bat
```

Distro name differences remain explicit:

```text
ubuntu,fedora native fd-find
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

The installer switches the login shell to Zsh and replaces the normal dotfiles
targets, including Neovim, Ghostty and fastfetch configuration, with backups
under `~/.dotfiles-backups/`. This is not a transparent addition to Omarchy's
shell/editor defaults. It does not replace Bash configuration, but the existing
nvm bootstrap may append initialization to a shell profile (including `.bashrc`
when launched from Bash). Locale, Hyprland, boot, services, distro repositories
and the installed desktop terminal are left alone. The Ubuntu-only Ghostty
installer never runs on Arch/Omarchy.

## Verification

Isolated policy checks (no package installation):

```sh
python3 -m unittest tests.test_install_platform
bash -n install.sh scripts/lib/install-platform.sh
shellcheck -x install.sh scripts/lib/install-platform.sh
```

The tests exercise platform detection, package-manager arguments, catalog
selection, Bundle declarations, unattended behavior and failure propagation.
Ruby is needed for the inert Bundle DSL test; that test skips if Ruby is absent.
The shell tests also run on macOS Bash 3.2.

A full install and a repeat run were tested in a disposable Omarchy ARM64 VM,
including Python/Node, Vim/Neovim plugins, Mason and Tree-sitter. A new Zsh
login resolved both dotfiles tools and Omarchy commands. Plain Arch and x86_64
Omarchy have not had a clean-install test. macOS/Ubuntu/Fedora package
selections were compared with the previous installer; they were not freshly
reinstalled for this change.
