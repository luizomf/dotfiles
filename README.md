# Dotfiles

Personal development environment for macOS and Ubuntu.

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
pyenv, the current Node.js LTS, Python and Node developer tools, and Neovim and
Tmux plugins. Set `OM_PYTHON_VERSION` to select a specific Python release.
Disposable test runs may skip these slower stages with
`OM_INSTALL_SKIP_TOOLCHAINS=1` or `OM_INSTALL_SKIP_PLUGINS=1`.

Start a new login shell after installation.

## Shared host paths

`config/paths.sh` is the source of truth for host paths needed by interactive
shells and unattended scripts. It currently defines `PROJECTS_DIR`. Supported
callers may select a machine-specific replacement with `OM_PATHS_FILE`.
`omnivoice_m4128_half` also accepts `OMNIVOICE_REMOTE_APP` when the remote
checkout differs from the local one.

## Pi Coding Agent

The installer links the static configuration under `pi/agent/` into
`~/.pi/agent/`. Credentials, sessions, trust decisions, generated model state,
and machine-specific model configuration remain local.

Skills and extensions are maintained separately in
[omskills](https://github.com/luizomf/omskills) and
[ompi](https://github.com/luizomf/ompi).

## License

See [LICENSE](LICENSE).
