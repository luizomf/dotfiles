# Zsh environment ownership

Zsh reads the global file before the personal file at each stage:

1. `.zshenv`: every Zsh invocation, including non-interactive SSH commands.
2. `.zprofile`: login shells.
3. `.zshrc`: interactive shells.
4. `.zlogin`: login shells, after the other stages.

A value set in `.zshenv` is not necessarily final: Alpine's `/etc/profile`
resets PATH, macOS's `path_helper` reorders it, and interactive toolchain setup
changes it again.

## Where to edit

- **`zsh/config/path`**: the single PATH policy for scripts, local binaries,
  Cargo, Docker, and an active nvm Node. It is applied from `.zshenv`,
  `.zprofile`, and the end of toolchain setup in `config/exports`, without
  duplicates. Order: dotfiles scripts, nvm, local binaries, Cargo/Docker, then
  inherited paths, so app-bundled Node links in `~/.local/bin` cannot shadow
  nvm. The first call moves system fallback directories to the end. Homebrew
  (`/opt/homebrew`, or `/home/linuxbrew/.linuxbrew` on Linux) is a fallback too,
  so non-interactive SSH commands find brew tools such as `trash`; interactive
  shells move it ahead in `config/exports`.
- **`zsh/config/env`**: public defaults that non-interactive Zsh also needs,
  such as `OLLAMA_*` and `LOCAL_MODEL` (`MODEL` follows `LOCAL_MODEL`). No
  credential lookups or toolchain initialization here.
- **`zsh/config/exports`**: interactive preferences and toolchain setup
  (Homebrew, pyenv, nvm, Bun, pnpm, completions). Keep tool-specific paths
  beside the initialization that needs them.
- **`config/paths.sh`**: shared host directories such as `PROJECTS_DIR`, not the
  executable PATH.
- **`~/.env/.env.*`**: private service configuration, sourced by the interactive
  loader in `config/use_this_to_load` (a single legacy `~/.env` file also
  works). Do not move these files or their Keychain lookups into `.zshenv`.

The Docker Desktop block in `.zprofile` stays; the shared PATH is applied after
it. None of this reaches GUI applications, services, or containers, and running
shells keep their environment until reopened.

## History retention

`zsh/config/config` sets `HISTSIZE` and `SAVEHIST` to 1,000,000 in one place.
`scripts/zsh_history_sync.py` merges entries without a cap, and Zsh applies its
own retention afterward, so keep the limits the same on every synced machine: a
shell with a lower limit trims the merged history.

## Terminal-only startup

The interactive loader requests a window title through `scripts/title`, and
`config/exports` sources `~/.fzf.zsh`, only when both stdin and stdout are
terminals. Forced-interactive commands with pipes, such as
`ssh host 'zsh -l -i +m -c ...'`, still load the environment and config. Without
the guard, fzf's scripts print `(eval):1: can't change option: zle` there.

## Checks

```sh
python3 -m unittest tests.test_zsh_environment
```

Covers each startup mode in temporary homes, PATH priority and deduplication,
public defaults and overrides, and the terminal-only title and fzf guards. It
does not load private env files or real toolchains.
