# Repository Guidelines

This is Otávio Miranda's personal dotfiles repository. It describes and
automates his working environment across macOS and Linux, including shell
configuration, editor settings, installation steps, and utility scripts.

## Public repository

This repository is public and used by other people. Treat every tracked file and
Git commit as publicly visible.

- Never add secrets, credentials, tokens, private keys, `.env` files, session
  data, personal logs, or other sensitive information.
- Avoid committing machine-specific state, generated files, caches, runtime
  artifacts, or private filesystem details unless explicitly requested.
- Keep changes focused, readable, and compatible with the existing repository
  conventions.
- Be especially careful when changing installation or setup scripts: they may
  overwrite files, install software, and be run by people other than the owner.
- Preserve unrelated personal configuration. Do not "clean up" preferences or
  scripts outside the requested scope.
