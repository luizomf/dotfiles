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

Before running anything, open `install.sh` and check what it does.
It installs packages and replaces shell, editor, terminal, Git, tmux, and Pi
configuration. Existing targets are moved to a timestamped directory under
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

The `scripts/` directory contains personal commands and automation used
across my machines. Some of them contact remote hosts, stop processes, synchronize
files, submit background work, or change system configuration. Read a script
before running it and do not assume it is safe for your setup.

The test suite is intentionally limited to behavior where a regression could
delete data, corrupt shared state, break installation, or leave background work
in a bad state. Tests use isolated fixtures; they do not make these scripts a
supported public API.

### Send a screenshot to an SSH host

Run `sshot <ssh-alias>` on the local Mac, outside SSH. It returns immediately
and waits in the background for **one new clipboard image**, for up to 120 seconds.
Close the tmux popup, arrange your screen, then use **Ctrl+Shift+Cmd+4** to capture
an area to the clipboard (or copy an image with another tool). Existing clipboard
images and changes containing only text are ignored. The previous immediate
screen-selection mode is retired.

The PNG is uploaded with `scp`; only after success does the remote path replace
the Mac clipboard. Paste that path into the remote shell or agent. SSH config and
host-key checks are preserved, but background SSH/SCP use `BatchMode=yes`: keys or
an agent must work without password/passphrase or new-host confirmation prompts.
The script does not discover the active SSH tab. Arm only one instance at a time;
concurrent instances could send the same image to multiple destinations.

```bash
sshot my-server
# Or, if scripts/ is not on PATH:
~/dotfiles/scripts/sshot my-server
```

Uses built-in macOS `osascript` (AppKit via JavaScript for Automation), `pbcopy`,
SSH/SCP, and a Unix-like remote with `mktemp` and writable `/tmp`. No extra runtime
or persistent service is installed. The helper is `scripts/lib/sshot-clipboard.js`.

The arming message prints a private local status-log path and a `touch` command
to cancel while waiting; Ctrl-C after the prompt returns does not cancel it.
Expiration or cancellation sends nothing. Esc cancels the screenshot tool, not
the armed watcher. A new clipboard image from any application can trigger it:
review the destination and cancel before copying sensitive images.

Local image bytes are removed when the worker exits. Private temporary logs and
cancellation files remain for troubleshooting; remove their reported directory
once the worker is finished. Remote images remain in fresh private
`/tmp/sshot.XXXXXXXXXX/` directories until removed or cleaned by the OS. Failed
uploads can leave partial remote files; check the local log for the destination
and failure. The 120-second limit covers waiting for an image, not upload time.

## Shared host paths

`config/paths.sh` defines the shared `PROJECTS_DIR` used by shells and unattended
scripts. Supported callers can load machine-specific values with `OM_PATHS_FILE`;
`omnivoice_m4128_half` also accepts `OMNIVOICE_REMOTE_APP`.

## Pi Coding Agent

The installer links the static configuration under `pi/agent/` into
`~/.pi/agent/`. Credentials, sessions, trust decisions, generated resources, and
machine-specific model settings stay local and must not be committed.

Skills and extensions are maintained separately in
[omskills](https://github.com/luizomf/omskills) and
[ompi](https://github.com/luizomf/ompi).

---

Made with hate, coffee, and a little bit of love.
