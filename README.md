# Dotfiles

This repository is intentionally highly opinionated. It installs the exact
personal development environment I use every day; it is not a general-purpose
bootstrap framework.

## Tested systems

Clean-install testing has been performed only on:

- Ubuntu 24.04 on ARM
- Ubuntu 26.04 on ARM
- macOS Sequoia on Apple Silicon

Other Ubuntu and macOS versions may work, but are not supported until tested.
The installer intentionally rejects other Linux distributions.

## Before installing

`install.sh` installs system packages and replaces existing configuration with
symbolic links into this repository. Existing targets are moved to a timestamped
backup under `~/.dotfiles-backups/` before links are created.

The repository must be cloned at `~/dotfiles`; deployed shell configuration and
shared scripts rely on that location.

Review the script before running it. In particular, it:

- installs packages with Homebrew or APT without upgrading the whole OS;
- downloads installers and source code from third-party projects;
- installs the current stable Neovim formula with Homebrew;
- configures the UTF-8 locale and changes the default shell to Zsh on Ubuntu;
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

## Shared host paths

`config/paths.sh` is the source of truth for host paths needed by interactive
shells and unattended scripts. It currently defines `PROJECTS_DIR`. Supported
callers may select a machine-specific replacement with `OM_PATHS_FILE`.
`omnivoice_m4128_half` also accepts `OMNIVOICE_REMOTE_APP` when the remote
checkout differs from the local one.

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
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) provides the image
  upscaler used by `imgupscale`.

These repositories are not required for the base installation, but the related
commands will not work without them.

## License

See [LICENSE](LICENSE).
