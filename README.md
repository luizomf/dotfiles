# dotfiles

These are my personal dotfiles. They install the exact environment I use every
day, and they are intentionally opinionated.

Since I use both Mac and Linux, most things here need to work on both (tested on
Fedora and Ubuntu).

See [`docs/`](docs/) for technical and maintenance documentation.

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

Install Git first, then run:

```bash
git clone https://github.com/luizomf/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

The repository is expected to live at `~/dotfiles`. Start a new login shell when
the installation finishes.

Python setup failures preserve the original error and do not stop independent
configuration steps. The installer skips the remaining Python setup and its
checks, then reports the failed operation and exit code at the end and exits
nonzero. This is an incomplete installation, not success. Other failures still
stop the installer immediately. Fix the reported cause before rerunning; nothing
is rolled back automatically.

The installer also enables this checkout's pre-commit checks, unless an existing
hook setup must be preserved. A plain clone does not activate Git hooks. For an
existing installation, run `./scripts/setup_git_hooks` after updating, without
rerunning the installer. Use `commit --help` and `commit --check` for the quick
workflow; see [hook setup and dependencies](docs/scripts/check_staged.md).

**⚠️ This will replace your configuration. You have been warned. Tamo junto.**

## 😈 YOU ONLY LIVE ONCE (YOLO)

If you're feeling lucky... bet on it:

```bash
# 🚨 DANGEROUS (I mean it)
export OM_INSTALL_ASSUME_YES=1 && git clone https://github.com/luizomf/dotfiles && cd dotfiles && ./install.sh
```

50/50 chance everything is gonna be OK.

---

Made with hate, coffee, and a little bit of love.
