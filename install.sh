#!/usr/bin/env bash

set -Eeuo pipefail

REPO_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
BACKUP_DIR="$HOME/.dotfiles-backups/$(date '+%Y%m%d-%H%M%S')"
readonly REPO_DIR BACKUP_DIR

# shellcheck source=scripts/lib/install-platform.sh
source "$REPO_DIR/scripts/lib/install-platform.sh"
# shellcheck source=scripts/lib/install-python.sh
source "$REPO_DIR/scripts/lib/install-python.sh"
python_failure=""

# Make user-managed tools visible during reruns before shell config is linked.
export PATH="$HOME/.local/bin:$HOME/.pyenv/bin:$PATH"

loginfo() {
  local blue='\033[1;34m'
  local reset='\033[0m'
  printf "🔵 ${blue}%s${reset}\n" "$1"
}

logsuccess() {
  local green='\033[1;32m'
  local reset='\033[0m'
  printf "🟢 ${green}%s${reset}\n" "$1"
}

logerror() {
  local red='\033[1;31m'
  local reset='\033[0m'
  printf "🔴 ${red}%s${reset}\n" "$1" >&2
}

# Report only an actual failed installer exit. macOS Bash 3.2 can fire ERR for
# expected probes inside guarded substitutions, while omitting a parent ERR for
# some failed subshells. EXIT handles both without claiming a successful run failed.
# shellcheck disable=SC2154 # exit_status is assigned inside this EXIT trap.
trap 'exit_status=$?; if (( BASH_SUBSHELL == 0 && exit_status != 0 )); then logerror "Installation incomplete (exit $exit_status)."; if [[ -n "${python_failure:-}" ]]; then logerror "$python_failure"; fi; fi' EXIT

run_remote_script() (
  local shell_path=$1
  local url=$2
  shift 2

  local script_path
  script_path=$(mktemp) || return $?
  trap 'rm -f "$script_path"' EXIT
  curl -fsSL "$url" -o "$script_path" || return $?
  "$shell_path" "$script_path" "$@"
)

load_brew() {
  local brew_path

  if command -v brew > /dev/null 2>&1; then
    brew_path=$(command -v brew)
  elif [[ -x /opt/homebrew/bin/brew ]]; then
    brew_path=/opt/homebrew/bin/brew
  elif [[ -x /home/linuxbrew/.linuxbrew/bin/brew ]]; then
    brew_path=/home/linuxbrew/.linuxbrew/bin/brew
  else
    return 1
  fi

  eval "$("$brew_path" shellenv)"
  if [[ "${OP_SYSTEM:-}" == lfs ]]; then
    # Brew dependencies may provide their own Python and other native tools.
    export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"
  fi
}

install_homebrew() {
  if load_brew; then
    return
  fi

  loginfo "Homebrew não encontrado. Instalando..."
  run_remote_script /bin/bash \
    https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh
  load_brew
}

backup_and_link() {
  local source=$1
  local target=$2

  mkdir -p "$(dirname "$target")"
  if [[ -L "$target" && "$(readlink "$target")" == "$source" ]]; then
    return
  fi
  if [[ -e "$target" || -L "$target" ]]; then
    local relative_target=${target#"$HOME"/}
    local backup_target="$BACKUP_DIR/$relative_target"
    mkdir -p "$(dirname "$backup_target")"
    mv "$target" "$backup_target"
    loginfo "Backup criado: $backup_target"
  fi

  ln -s "$source" "$target"
}

confirm_installation() {
  if [[ "${OM_INSTALL_ASSUME_YES:-0}" == "1" ]]; then
    return
  fi

  printf '%s\n' \
    "Este instalador altera pacotes do sistema e substitui configurações." \
    "Configurações existentes serão salvas em ~/.dotfiles-backups/."
  read -r -p "Digite INSTALL para continuar: " confirmation
  if [[ "$confirmation" != "INSTALL" ]]; then
    loginfo "Instalação cancelada."
    exit 0
  fi
}

if [[ "$REPO_DIR" != "$HOME/dotfiles" ]]; then
  logerror "O repositório deve estar em $HOME/dotfiles (encontrado: $REPO_DIR)."
  exit 1
fi

confirm_installation
configure_install_interaction
if [[ "${OM_INSTALL_ASSUME_YES:-0}" == "1" ]]; then
  loginfo "Unattended mode: prompts disabled; sudo (or Alpine doas) must already be authorized. Logs and errors remain visible."
fi

OP_SYSTEM=""
case "$(uname -s)" in
  Linux)
    if [[ ! -r /etc/os-release ]]; then
      logerror "Não foi possível identificar a distribuição Linux."
      exit 1
    fi
    # shellcheck disable=SC1091
    . /etc/os-release
    ostree=0
    [[ ! -e /run/ostree-booted ]] || ostree=1
    if ! OP_SYSTEM=$(detect_install_platform Linux "${ID:-}" "$ostree"); then
      logerror "Distribuição Linux não suportada (incluindo variantes OSTree): ${PRETTY_NAME:-desconhecida}"
      exit 1
    fi
    loginfo "Sistema detectado: ${PRETTY_NAME}."
    ;;
  Darwin)
    OP_SYSTEM=$(detect_install_platform Darwin)
    loginfo "Sistema detectado: macOS $(sw_vers -productVersion)."
    ;;
  *)
    logerror "Sistema não suportado; consulte config/install-platforms.list."
    exit 1
    ;;
esac

install_platform_packages "$OP_SYSTEM"

if [[ "$OP_SYSTEM" == "ubuntu" ]]; then
  if ! locale -a | grep -Eqi '^en_US\.utf-?8$'; then
    sudo locale-gen en_US.UTF-8
  fi
  sudo update-locale LANG=en_US.UTF-8
fi

if [[ "$(install_package_manager "$OP_SYSTEM")" == apt ]]; then
  mkdir -p "$HOME/.local/bin"
  if ! command -v fd > /dev/null 2>&1 && command -v fdfind > /dev/null 2>&1; then
    ln -sf "$(command -v fdfind)" "$HOME/.local/bin/fd"
  fi
  if ! command -v bat > /dev/null 2>&1 && command -v batcat > /dev/null 2>&1; then
    ln -sf "$(command -v batcat)" "$HOME/.local/bin/bat"
  fi
fi

if [[ "$OP_SYSTEM" != "darwin" ]]; then
  zsh_path=$(command -v zsh)
  if [[ "$OP_SYSTEM" == lfs ]] && ! grep -Fxq "$zsh_path" /etc/shells; then
    printf '%s\n' "$zsh_path" | run_install_privileged "$OP_SYSTEM" tee -a /etc/shells > /dev/null
  fi
  if [[ "$(getent passwd "$(id -un)" | cut -d: -f7)" != "$zsh_path" ]]; then
    run_install_privileged "$OP_SYSTEM" chsh -s "$zsh_path" "$(id -un)"
  fi
  # Linux hosts keep their installed terminal; only Ubuntu adjusts the locale.
fi

loginfo "Configurando Oh My Zsh..."
if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
  run_remote_script /bin/sh \
    https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh \
    "" --unattended
else
  loginfo "Oh My Zsh já está instalado."
fi

ZSH_CUSTOM=${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}
loginfo "Instalando plugins do Zsh..."
if [[ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]]; then
  git clone https://github.com/zsh-users/zsh-autosuggestions \
    "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi
if [[ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]]; then
  git clone https://github.com/zsh-users/zsh-syntax-highlighting.git \
    "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
fi

# Ask Neovim rather than duplicate its XDG data/app-name resolution.
LAZY_PATH="$(nvim --clean --headless -i NONE \
  -c 'lua io.write(vim.fn.stdpath("data"))' -c 'qa')/lazy/lazy.nvim"
loginfo "Instalando Lazy.nvim..."
if [[ ! -d "$LAZY_PATH" ]]; then
  git clone https://github.com/folke/lazy.nvim.git \
    --filter=blob:none --branch=stable "$LAZY_PATH"
fi

if [[ "${OP_SYSTEM:-}" == lfs ]]; then
  loginfo "LFS: keeping native tools and using Homebrew for missing tools; no nvm or pyenv."
elif [[ "${OP_SYSTEM:-}" == alpine ]]; then
  loginfo "Alpine: using apk Node/Python and native musl tools; no Homebrew or nvm."
  if [[ "${OM_INSTALL_SKIP_TOOLCHAINS:-0}" != "1" ]]; then
    npm install --global --prefix "$HOME/.local" \
      prettier pyright @earendil-works/pi-coding-agent
  fi
else
  # Match zsh/config/exports even when the desktop sets XDG_CONFIG_HOME.
  export NVM_DIR="$HOME/.nvm"
  if [[ ! -s "$NVM_DIR/nvm.sh" ]]; then
    loginfo "Instalando nvm..."
    require_new_toolchain_dir "$NVM_DIR"
    # nvm requires an explicit non-default install directory to exist first.
    mkdir -p "$NVM_DIR"
    run_remote_script /bin/bash \
      https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh
  fi

  if [[ "${OM_INSTALL_SKIP_TOOLCHAINS:-0}" != "1" ]]; then
    loginfo "Configurando Node.js e ferramentas npm..."
    # shellcheck disable=SC1091
    . "$NVM_DIR/nvm.sh"
    nvm install --lts
    nvm install-latest-npm
    npm install --global prettier
  else
    loginfo "Toolchain setup skipped; run 'uv sync --locked' in $REPO_DIR to prepare development tools."
  fi
fi

if configure_install_python; then
  loginfo "Python setup completed (or toolchain configuration explicitly skipped)."
else
  python_status=$?
  python_failure="Python: $PYTHON_SETUP_STEP (exit $python_status). Remaining Python setup and its checks were skipped; see the original error above."
  logerror "$python_failure"
  loginfo "Continuing independent installation steps..."
fi

loginfo "Criando links de configuração..."
mkdir -p "$HOME/.config"

backup_and_link "$REPO_DIR/zsh/.zshrc" "$HOME/.zshrc"
backup_and_link "$REPO_DIR/zsh/.zprofile" "$HOME/.zprofile"
backup_and_link "$REPO_DIR/zsh/.zshenv" "$HOME/.zshenv"
backup_and_link "$REPO_DIR/zsh/config/omtheme.zsh-theme" \
  "$ZSH_CUSTOM/themes/omtheme.zsh-theme"

backup_and_link "$REPO_DIR/git/.gitconfig" "$HOME/.gitconfig"

GIT_LOCAL="$HOME/.gitconfig.local"
if git config -f "$GIT_LOCAL" user.name > /dev/null 2>&1; then
  loginfo "Identidade local do Git já configurada."
elif [[ -t 0 ]]; then
  loginfo "Configure a identidade usada nos seus commits:"
  read -r -p "  Nome   (git user.name): " GIT_USER_NAME
  read -r -p "  E-mail (git user.email): " GIT_USER_EMAIL
  if [[ -n "$GIT_USER_NAME" && -n "$GIT_USER_EMAIL" ]]; then
    git config -f "$GIT_LOCAL" user.name "$GIT_USER_NAME"
    git config -f "$GIT_LOCAL" user.email "$GIT_USER_EMAIL"
    logsuccess "Identidade salva em ~/.gitconfig.local."
  else
    loginfo "Identidade vazia; configure ~/.gitconfig.local posteriormente."
  fi
else
  loginfo "Sessão não interativa; configure ~/.gitconfig.local posteriormente."
fi

backup_and_link "$REPO_DIR/tmux/.tmux.conf" "$HOME/.tmux.conf"
backup_and_link "$REPO_DIR/vim/.vimrc" "$HOME/.vimrc"
backup_and_link "$REPO_DIR/nvim" "$HOME/.config/nvim"
backup_and_link "$REPO_DIR/ghostty" "$HOME/.config/ghostty"
backup_and_link "../../dotfiles/omxterm/config.json" \
  "$HOME/.config/omxterm/config.json"
backup_and_link "../../dotfiles/omxterm/snippets.json" \
  "$HOME/.config/omxterm/snippets.json"
backup_and_link "../../dotfiles/omxterm/themes" \
  "$HOME/.config/omxterm/themes"
backup_and_link "$REPO_DIR/fastfetch" "$HOME/.config/fastfetch"

VIM_PLUG_PATH="$HOME/.vim/autoload/plug.vim"
if [[ ! -f "$VIM_PLUG_PATH" ]]; then
  loginfo "Instalando vim-plug..."
  mkdir -p "$(dirname "$VIM_PLUG_PATH")"
  curl -fsSL \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim \
    -o "$VIM_PLUG_PATH"
fi

if [[ "$OP_SYSTEM" == "darwin" ]]; then
  GDRIVE_PATH=""
  if [[ -d "$HOME/Library/CloudStorage" ]]; then
    GDRIVE_PATH=$(find "$HOME/Library/CloudStorage" -maxdepth 1 \
      -name 'GoogleDrive-*' -type d -print -quit)
  fi
  if [[ -z "$GDRIVE_PATH" && -d "$HOME/Google Drive" ]]; then
    GDRIVE_PATH="$HOME/Google Drive"
  fi
  if [[ -n "$GDRIVE_PATH" ]]; then
    backup_and_link "$GDRIVE_PATH" "$HOME/gdrive"
  else
    loginfo "Google Drive não encontrado; link ~/gdrive não foi criado."
  fi
fi

if [[ "${OM_INSTALL_SKIP_PLUGINS:-0}" != "1" ]]; then
  loginfo "Instalando plugins do Vim..."
  vim -Nu "$HOME/.vimrc" -n -es -i NONE \
    -c 'PlugInstall --sync' -c 'qa'

  loginfo "Instalando plugins do Neovim..."
  nvim --headless '+Lazy! restore' +qa

  loginfo "Instalando ferramentas do Mason e parsers do Treesitter..."
  nvim --headless \
    -c "lua require('settings.tooling').bootstrap()" \
    -c 'qall'

fi

loginfo "Verificando a instalação..."
required_commands=(git nvim vim zsh tmux python3 fastfetch fd fzf bat shellcheck)
if [[ "$OP_SYSTEM" != alpine ]]; then
  required_commands+=(brew)
fi
if [[ "${OM_INSTALL_SKIP_TOOLCHAINS:-0}" != "1" ]]; then
  required_commands+=(node npm prettier)
  if [[ "$OP_SYSTEM" == alpine ]]; then
    required_commands+=(pi pyright)
  fi
fi
if [[ "${OM_INSTALL_SKIP_TOOLCHAINS:-0}" != "1" && -z "$python_failure" ]]; then
  required_commands+=(uv pyright ruff)
  if [[ "$OP_SYSTEM" != alpine && "$OP_SYSTEM" != lfs ]]; then
    required_commands+=(pyenv python)
  fi
  for development_tool in python pyright ruff; do
    if [[ ! -x "$REPO_DIR/.venv/bin/$development_tool" ]]; then
      logerror "Development tool not found: $REPO_DIR/.venv/bin/$development_tool"
      exit 1
    fi
  done
fi
for required_command in "${required_commands[@]}"; do
  if ! command -v "$required_command" > /dev/null 2>&1; then
    logerror "Comando obrigatório não encontrado: $required_command"
    exit 1
  fi
done

required_links=(
  "$HOME/.zshrc"
  "$HOME/.zprofile"
  "$HOME/.zshenv"
  "$HOME/.gitconfig"
  "$HOME/.tmux.conf"
  "$HOME/.vimrc"
  "$HOME/.config/nvim"
  "$HOME/.config/ghostty"
  "$HOME/.config/omxterm/config.json"
  "$HOME/.config/omxterm/snippets.json"
  "$HOME/.config/omxterm/themes"
  "$HOME/.config/fastfetch"
)
for required_link in "${required_links[@]}"; do
  if [[ ! -L "$required_link" ]]; then
    logerror "Link obrigatório não encontrado: $required_link"
    exit 1
  fi
done

if [[ ! -f "$VIM_PLUG_PATH" ]]; then
  logerror "vim-plug não foi instalado."
  exit 1
fi
if [[ "${OM_INSTALL_SKIP_PLUGINS:-0}" != "1" ]]; then
  for vim_plugin in fzf fzf.vim; do
    if [[ ! -d "$HOME/.vim/plugged/$vim_plugin" ]]; then
      logerror "Plugin do Vim não encontrado: $vim_plugin"
      exit 1
    fi
  done
fi

loginfo "Configuring repository-local Git hooks (preserving existing setups)..."
"$REPO_DIR/scripts/setup_git_hooks"

if [[ -n "$python_failure" ]]; then
  loginfo "Independent installation steps completed. Open a new terminal to load the configuration."
  exit 1
fi

printf '\n%s\n' \
  "Instalação automática concluída." \
  "Abra um novo terminal para carregar o Zsh e os novos caminhos."

if [[ -d "$BACKUP_DIR" ]]; then
  loginfo "Backups salvos em $BACKUP_DIR"
fi
logsuccess "Instalação concluída."
