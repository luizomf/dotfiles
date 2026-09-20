#!/usr/bin/env bash
# Source-only Python setup for install.sh. On failure, return the original status
# and leave PYTHON_SETUP_STEP describing the failed operation for the final report.
# The caller supplies logging, run_remote_script and require_new_toolchain_dir.
# shellcheck disable=SC2034 # PYTHON_SETUP_STEP is consumed by install.sh.

configure_install_python() {
  local python_version pyenv_init tool installed_tools python_path
  # This function is called in an if: Bash disables errexit throughout its body.
  # Every required operation must therefore propagate failure explicitly.
  PYTHON_SETUP_STEP="Install pyenv"
  if ! command -v pyenv > /dev/null 2>&1; then
    loginfo "Instalando pyenv..."
    require_new_toolchain_dir "$HOME/.pyenv" || return $?
    run_remote_script /bin/bash https://pyenv.run || return $?
  fi

  PYTHON_SETUP_STEP="Install uv"
  if ! command -v uv > /dev/null 2>&1; then
    loginfo "Instalando uv..."
    run_remote_script /bin/sh https://astral.sh/uv/install.sh || return $?
  fi

  if [[ "${OM_INSTALL_SKIP_TOOLCHAINS:-0}" == "1" ]]; then
    return 0
  fi

  loginfo "Configurando Python..."
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$HOME/.local/bin:$PATH"
  PYTHON_SETUP_STEP="Initialize pyenv"
  pyenv_init=$(pyenv init -) || return $?
  eval "$pyenv_init" || return $?
  python_version=${OM_PYTHON_VERSION:-}
  PYTHON_SETUP_STEP="Find a stable Python 3.14 release"
  if [[ -z "$python_version" ]]; then
    python_version=$(pyenv install --list | awk '
      $1 ~ /^3\.14\.[0-9]+$/ { version = $1 }
      END { print version }
    ') || return $?
  fi
  if [[ -z "$python_version" ]]; then
    logerror "Nenhuma versão estável do Python 3.14 foi encontrada pelo pyenv."
    return 1
  fi
  PYTHON_SETUP_STEP="Install Python $python_version"
  pyenv install --skip-existing "$python_version" || return $?
  PYTHON_SETUP_STEP="Select global Python $python_version"
  pyenv global "$python_version" || return $?

  PYTHON_SETUP_STEP="List uv tools"
  installed_tools=$(uv tool list) || return $?
  for tool in pyright ruff; do
    if ! grep -q "^$tool " <<< "$installed_tools"; then
      PYTHON_SETUP_STEP="Install $tool with uv"
      uv tool install "$tool" || return $?
    fi
  done

  PYTHON_SETUP_STEP="Resolve the pyenv interpreter"
  python_path=$(pyenv which python) || return $?
  PYTHON_SETUP_STEP="Sync the dotfiles development environment"
  loginfo "Syncing the dotfiles development environment from uv.lock..."
  # Always target this checkout, not the caller's cwd or another active venv.
  UV_PROJECT_ENVIRONMENT="$REPO_DIR/.venv" uv sync \
    --project "$REPO_DIR" --locked --python "$python_path" || return $?
}
