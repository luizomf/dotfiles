#!/usr/bin/env bash

set -Eeuo pipefail

REPO_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
BACKUP_DIR="$HOME/.dotfiles-backups/$(date '+%Y%m%d-%H%M%S')"
readonly REPO_DIR BACKUP_DIR

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

trap 'logerror "Installation failed at line $LINENO."' ERR

run_remote_script() (
  local shell_path=$1
  local url=$2
  shift 2

  local script_path
  script_path=$(mktemp)
  trap 'rm -f "$script_path"' EXIT
  curl -fsSL "$url" -o "$script_path"
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

OP_SYSTEM=""
case "$(uname -s)" in
  Linux)
    if [[ ! -r /etc/os-release ]]; then
      logerror "Não foi possível identificar a distribuição Linux."
      exit 1
    fi
    # shellcheck disable=SC1091
    . /etc/os-release
    if [[ "${ID:-}" != "ubuntu" ]]; then
      logerror "Distribuição Linux não suportada: ${PRETTY_NAME:-desconhecida}"
      exit 1
    fi
    OP_SYSTEM="ubuntu"
    loginfo "Sistema detectado: ${PRETTY_NAME}."
    ;;
  Darwin)
    OP_SYSTEM="darwin"
    loginfo "Sistema detectado: macOS $(sw_vers -productVersion)."
    ;;
  *)
    logerror "Apenas macOS e Ubuntu são suportados."
    exit 1
    ;;
esac

if [[ "$OP_SYSTEM" == "darwin" ]]; then
  install_homebrew
  loginfo "Atualizando o Homebrew..."
  brew update
  loginfo "Instalando o Brewfile..."
  brew bundle --file="$REPO_DIR/homebrew/Brewfile"
fi

if [[ "$OP_SYSTEM" == "ubuntu" ]]; then
  loginfo "Atualizando o índice de pacotes do Ubuntu..."
  sudo DEBIAN_FRONTEND=noninteractive apt-get update

  loginfo "Instalando dependências do Ubuntu..."
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    aria2 autoconf automake blt-dev build-essential cmake curl ffmpeg \
    fd-find fonts-firacode fonts-jetbrains-mono gettext git htop libbz2-dev \
    libgdbm-dev liblua5.4-dev liblzma-dev libreadline-dev libsqlite3-dev locales \
    libssl-dev libtool libtool-bin llvm lua5.4 luarocks make nano ninja-build \
    openssl pkgconf python3-dev ripgrep sqlite3 tcl tcl-dev tk tk-dev \
    tree unzip vim watch wget zlib1g-dev

  if ! locale -a | grep -Eqi '^en_US\.utf-?8$'; then
    sudo locale-gen en_US.UTF-8
  fi
  sudo update-locale LANG=en_US.UTF-8

  install_homebrew
  brew install fastfetch font-fira-code-nerd-font gcc neovim tree-sitter-cli rtk glow \
    bat chafa fzf tmux btop gh imagemagick just lazygit p7zip pandoc vhs trash-cli hf

  mkdir -p "$HOME/.local/bin"
  if ! command -v fd > /dev/null 2>&1 && command -v fdfind > /dev/null 2>&1; then
    ln -sf "$(command -v fdfind)" "$HOME/.local/bin/fd"
  fi
  if ! command -v bat > /dev/null 2>&1 && command -v batcat > /dev/null 2>&1; then
    ln -sf "$(command -v batcat)" "$HOME/.local/bin/bat"
  fi

  if ! command -v zsh > /dev/null 2>&1; then
    loginfo "Instalando Zsh..."
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y zsh
  else
    loginfo "Zsh já está instalado."
  fi

  zsh_path=$(command -v zsh)
  if [[ "$(getent passwd "$(id -un)" | cut -d: -f7)" != "$zsh_path" ]]; then
    sudo chsh -s "$zsh_path" "$(id -un)"
  fi

  if ! command -v ghostty > /dev/null 2>&1; then
    loginfo "Instalando Ghostty..."
    run_remote_script /bin/bash \
      https://raw.githubusercontent.com/mkasberg/ghostty-ubuntu/HEAD/install.sh
  else
    loginfo "Ghostty já está instalado."
  fi
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

LAZY_PATH="$HOME/.local/share/nvim/lazy/lazy.nvim"
loginfo "Instalando Lazy.nvim..."
if [[ ! -d "$LAZY_PATH" ]]; then
  git clone https://github.com/folke/lazy.nvim.git --filter=blob:none "$LAZY_PATH"
fi

loginfo "Instalando TPM..."
if [[ ! -d "$HOME/.tmux/plugins/tpm" ]]; then
  git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
fi

if ! command -v pyenv > /dev/null 2>&1; then
  loginfo "Instalando pyenv..."
  rm -rf "$HOME/.pyenv"
  run_remote_script /bin/bash https://pyenv.run
fi

if ! command -v uv > /dev/null 2>&1; then
  loginfo "Instalando uv..."
  run_remote_script /bin/sh https://astral.sh/uv/install.sh
fi

if ! command -v nvm > /dev/null 2>&1 && [[ ! -s "$HOME/.nvm/nvm.sh" ]]; then
  loginfo "Instalando nvm..."
  rm -rf "$HOME/.nvm"
  run_remote_script /bin/bash \
    https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh
fi

if [[ "${OM_INSTALL_SKIP_TOOLCHAINS:-0}" != "1" ]]; then
  loginfo "Configurando Node.js e ferramentas npm..."
  export NVM_DIR="$HOME/.nvm"
  # shellcheck disable=SC1091
  . "$NVM_DIR/nvm.sh"
  nvm install --lts
  nvm install-latest-npm
  npm install --global prettier

  loginfo "Configurando Python..."
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$HOME/.local/bin:$PATH"
  eval "$(pyenv init -)"
  PYTHON_VERSION=${OM_PYTHON_VERSION:-}
  if [[ -z "$PYTHON_VERSION" ]]; then
    PYTHON_VERSION=$(pyenv install --list | awk '
      $1 ~ /^3\.14\.[0-9]+$/ { version = $1 }
      END { print version }
    ')
  fi
  if [[ -z "$PYTHON_VERSION" ]]; then
    logerror "Nenhuma versão estável do Python 3.14 foi encontrada pelo pyenv."
    exit 1
  fi
  pyenv install --skip-existing "$PYTHON_VERSION"
  pyenv global "$PYTHON_VERSION"

  if ! uv tool list | grep -q '^pyright '; then
    uv tool install pyright
  fi
  if ! uv tool list | grep -q '^ruff '; then
    uv tool install ruff
  fi
fi

loginfo "Criando links de configuração..."
mkdir -p "$HOME/.config" "$HOME/.pi/agent/themes"

backup_and_link "../../dotfiles/pi/agent/AGENTS.md" "$HOME/.pi/agent/AGENTS.md"
backup_and_link "../../dotfiles/pi/agent/RTK.md" "$HOME/.pi/agent/RTK.md"
backup_and_link "../../dotfiles/pi/agent/settings.json" "$HOME/.pi/agent/settings.json"
backup_and_link "../../../dotfiles/pi/agent/themes/omtheme.json" \
  "$HOME/.pi/agent/themes/omtheme.json"

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

  loginfo "Instalando plugins do Tmux..."
  "$HOME/.tmux/plugins/tpm/bin/install_plugins"
fi

loginfo "Verificando a instalação..."
required_commands=(git nvim vim zsh tmux brew fastfetch fd fzf bat)
if [[ "$OP_SYSTEM" == "ubuntu" ]]; then
  required_commands+=(ghostty)
fi
if [[ "${OM_INSTALL_SKIP_TOOLCHAINS:-0}" != "1" ]]; then
  required_commands+=(node npm prettier pyenv python uv pyright ruff)
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
  "$HOME/.pi/agent/settings.json"
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

printf '\n%s\n' \
  "Instalação automática concluída." \
  "Abra um novo terminal para carregar o Zsh e os novos caminhos."

if [[ -d "$BACKUP_DIR" ]]; then
  loginfo "Backups salvos em $BACKUP_DIR"
fi
logsuccess "Instalação concluída."
