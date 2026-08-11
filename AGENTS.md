# Repository Guidelines

## Purpose and scope

This public repository contains Otávio Miranda's personal dotfiles and bootstrap
automation for macOS and Ubuntu. Other people also use it, so preserve personal
preferences while keeping shared setup behavior safe and understandable.

- These instructions apply repository-wide. `pi/agent/AGENTS.md` adds stricter
  rules for `pi/agent/`; follow the closest applicable `AGENTS.md`.
- `README.md` is the user-facing source for supported setup and safety warnings.
  It documents clean-install testing only on ARM Ubuntu 24.04 and macOS Sequoia;
  do not claim broader support without evidence.
- `config/paths.sh` is the documented source of truth for shared host paths.
  Preserve `OM_PATHS_FILE` overrides at callers that support them.
- When documentation, tests, comments, and implementation disagree, trace the
  intended behavior and report the conflict instead of silently choosing one.

## Repository map and boundaries

- `install.sh` installs dependencies and replaces user configuration with links
  into this checkout. `homebrew/Brewfile` is the macOS package manifest.
- `zsh/`, `tmux/`, `nvim/`, `vim/`, `ghostty/`, `fastfetch/`, and `git/` contain
  deployed application and shell configuration.
- `scripts/` contains user commands, including utilities that contact remote
  machines, cloud services, and queues. Inspect dependencies and side effects
  before changing or running one.
- `pi/agent/` contains only static Pi configuration. Credentials, sessions,
  trust decisions, generated model state, and machine-specific model settings
  must remain local, as described in `README.md`.
- `prompts/` contains reusable prompt text. `tests/` currently covers only
  `scripts/bq`.

## Safety and public data

Treat every tracked file and Git commit as public.

- Never add secrets, credentials, tokens, private keys, `.env` files, session
  data, personal logs, or other sensitive information. Do not rely on
  `.gitignore` as the only protection.
- Do not add caches, generated output, runtime artifacts, or machine-local state
  unless explicitly requested and safe for publication.
- Never run `install.sh` as a check: it is interactive and intentionally
  destructive. Do not run synchronization, upload, SSH, queue, or remote-host
  helpers without explicit authorization for their side effects.
- Installation and setup changes require extra care because they can overwrite
  files, install software, and affect users beyond the repository owner.
- Preserve unrelated personal configuration. Do not generalize, reformat, or
  "clean up" preferences outside the requested scope.

## Engineering and verification

- Prefer simple, explicit changes in the existing language and style. Preserve
  Bash, Zsh, POSIX shell, Python, and Lua boundaries, including whether a shell
  file is executed or sourced.
- Quote paths and arguments, validate untrusted input at boundaries, preserve
  useful error context, and explain non-obvious intent rather than narrating
  syntax.
- Keep behavior changes small and reviewable. Add regression coverage when a
  practical test boundary exists, and update affected user documentation in the
  same change.
- There is no repository-wide build, lint, type-check, format, or CI workflow.
  The empty `package.json` is not an npm toolchain. Do not invent or claim gates
  that are not configured.
- For changes to `scripts/bq`, run from the repository root:
  `python3 -m unittest tests/test_bq.py`.
- For other changes, use focused interpreter-specific syntax or behavior checks
  that do not alter the host. Review the final diff and report exactly what ran,
  what was skipped, and any remaining risk.
