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

Install Git first. For a **new checkout** (`~/dotfiles` must not already exist),
run:

```bash
git clone https://github.com/luizomf/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

The repository must live at `~/dotfiles`. If you already cloned it, **do not
clone again**: use `cd ~/dotfiles && ./install.sh`. Run the installer as your
normal user, **not** with `sudo ./install.sh`; it requests elevated permissions
for individual system operations. Start a new login shell when installation
finishes.

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

`OM_INSTALL_ASSUME_YES=1` enables unattended mode, not quiet mode: logs and
errors remain visible. It skips confirmation and Git identity prompts, enables
Homebrew's non-interactive installer, disables Git credential prompts, and
closes stdin for child installers. Direct `sudo` calls use `-n`: missing
authorization fails instead of waiting for a password. Provision sudo access
beforehand; an interactive `sudo -v` can help for a local run, but its cached
authorization may expire during a long installation. Third-party commands that
require interaction may fail rather than complete unattended. No privileges are
granted by this flag.

### Local terminal: authenticate once, then skip installer prompts

**First installation only:** clone to the explicit destination, regardless of
which directory your terminal is currently in. `sudo -v` asks for your password
before the installer disables prompts.

```bash
# 🚨 DANGEROUS (I mean it)
git clone https://github.com/luizomf/dotfiles.git ~/dotfiles &&
  cd ~/dotfiles &&
  sudo -v &&
  OM_INSTALL_ASSUME_YES=1 ./install.sh
```

**Already cloned?** Use this instead; do not create another nested checkout:

```bash
cd ~/dotfiles && sudo -v && OM_INSTALL_ASSUME_YES=1 ./install.sh
```

If you see `sudo: a password is required`, authorization is missing or expired.
In a local terminal, authenticate again with `sudo -v` and rerun the command
above. If authorization keeps expiring, use normal interactive mode instead:

```bash
cd ~/dotfiles && env -u OM_INSTALL_ASSUME_YES ./install.sh
```

### Fully unattended automation

`sudo -v` is an interactive preparation step, not a solution for a job with
nobody available to enter a password. Provision the job user's required sudo
permissions beforehand. In that same execution environment, `sudo -n true`
checks basic non-interactive access; it does not prove permission for every
command the installer needs. Missing permission causes failure, not a prompt. Do
not run the whole installer as root to work around this.

Configure Git identity separately in `~/.gitconfig.local` when needed.

50/50 chance everything is gonna be OK.

---

Made with hate, coffee, and a little bit of love.
