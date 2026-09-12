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
