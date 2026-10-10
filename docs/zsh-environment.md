# Zsh environment ownership

Zsh reads the global file before the personal file at each applicable stage:

1. `.zshenv`: every normal Zsh invocation, including non-interactive SSH
   commands.
2. `.zprofile`: login shells.
3. `.zshrc`: interactive shells.
4. `.zlogin`: login shells, after the other stages.

A variable set in `.zshenv` is not necessarily the final value. Alpine's global
login profile resets PATH through `/etc/profile`; macOS runs `path_helper`,
which reorders it. Later interactive toolchain initialization can modify PATH
again. Startup-disabling flags such as `zsh -f` can bypass personal startup
files.

## Where to edit

- **`zsh/config/path`**: the single basic PATH policy for scripts, local
  binaries, Cargo, Docker, and an active/inherited nvm Node. It is sourced from
  `.zshenv`, `.zprofile`, and the end of interactive toolchain setup in
  `config/exports`. Reapplication restores priority without duplicate entries.
  Dotfiles scripts precede an active/inherited nvm; nvm precedes local binaries,
  Cargo/Docker and inherited paths. This keeps application-bundled Node links in
  `~/.local/bin` from shadowing the selected nvm runtime while preserving
  wrappers. The initial `.zshenv` call moves system fallback directories to the
  end, preserving its previous behavior for inherited virtualenv/custom paths.
  Later calls preserve toolchain ordering and append missing fallbacks.
- **`zsh/config/env`**: public defaults needed by non-interactive Zsh too, such
  as `OLLAMA_*` and `LOCAL_MODEL`. Loaded by `.zshenv`; no credential lookup or
  toolchain initialization belongs here. Existing overrides remain supported;
  `MODEL` deliberately continues to follow `LOCAL_MODEL`, as before.
- **`zsh/config/exports`**: interactive preferences and toolchain initialization
  (Homebrew, pyenv, nvm, Bun, pnpm, completions). Tool-specific paths remain
  beside the initialization that needs them rather than being enabled in every
  script.
- **`config/paths.sh`**: shared host directory variables used by shell and other
  scripts, such as `PROJECTS_DIR`. This is not the executable PATH list.
- **`~/.env/.env.*`**: private/local service configuration. The existing
  interactive loader in `config/use_this_to_load` sources all these files; it
  also supports a legacy single `~/.env` file. This behavior is unchanged. Do
  not move these files or their Keychain lookups into `.zshenv`.

The existing Docker Desktop block in `.zprofile` remains intact. Our shared PATH
is applied after it, but this does not prevent Docker Desktop from editing the
file. Managing Docker Desktop's own installation preferences is separate.

This config applies to Zsh processes, not automatically to GUI applications,
services or containers. Existing shells keep their environment until reloaded;
open a new shell to exercise the complete startup order. No login or credential
reset is required by this reorganization.

## Checks

`python3 -m unittest tests.test_zsh_environment` exercises non-interactive,
interactive, login-only and login-interactive startup in temporary homes. It
checks a simulated login PATH reset and native system startup files, shared path
priority, an inherited nvm Node, no duplicate entries, public
defaults/overrides, and repeated PATH application. Private env files and real
user toolchain startup files are not loaded. Interactive tool initialization
uses a neutral `OSTYPE` and stub `uname`/`pyenv` functions, avoiding installed
Homebrew/pyenv initialization. These tests do not validate installed toolchain
behavior. A separate ordering regression covers fallback-first inherited PATHs
on simulated macOS/Linux, both at initial startup and after toolchain setup.
