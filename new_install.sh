#!/bin/bash

# função para printar loginfos de forma legível
loginfo() {
  echo -e "
🔵 [1;34m$1[0m"
}

logsuccess() {
  echo -e "
🟢 [1;32m$1[0m"
}

logerror() {
  echo -e "
🔴 [1;31m$1[0m"
}

# garante que o script pare em caso de erro
set -e

OP_SYSTEM=""

if [ "$(uname -s)" == "Linux" ]; then
    echo "This system is Linux."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" == "ubuntu" ]; then
            OP_SYSTEM="ubuntu"
        else
            logerror "This is another Linux distribution: $PRETTY_NAME"
        fi
    elif command -v lsb_release &> /dev/null; then
        if lsb_release -d | grep -q "Ubuntu"; then
            OP_SYSTEM="ubuntu"
        fi
    fi
elif [ "$(uname -s)" == "Darwin" ]; then 
  OP_SYSTEM="darwin"
else
  logerror "It is not safe to run this script on your system."
  exit 1
fi

if [[ "$OP_SYSTEM" == "darwin" ]]; then

  # Homebrew e Brewfile
  loginfo "Verificando e instalando dependências com Homebrew..."
  if ! command -v brew &> /dev/null; then
    loginfo "Homebrew não encontrado. Instalando..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> "$HOME/.zprofile"
    eval "$(/opt/homebrew/bin/brew shellenv)"
  else
    loginfo "Homebrew já está instalado. Atualizando..."
    brew update
  fi

  # Para gerar o Brewfile
  # brew bundle dump --file=~/dotfiles/homebrew/Brewfile --describe --force
  loginfo "Instalando pacotes e aplicações do Brewfile..."
  brew bundle --file="$HOME/dotfiles/homebrew/Brewfile"
  
elif [[ "$OP_SYSTEM" == "ubuntu" ]]; then

  loginfo "Your system is Ubuntu, updating packages..."
  sudo apt update -y
  sudo apt upgrade -y

  loginfo "Installing apps..."
  sudo apt install \
    openssl bat cmake ffmpeg fzf htop nano \
    neovim p7zip pkgconf sqlite3 tcl tk tcl-dev tk-dev tmux \
    tree watch wget fonts-firacode fonts-jetbrains-mono \
    -y

  sudo chsh -s /usr/bin/zsh
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/mkasberg/ghostty-ubuntu/HEAD/install.sh)"

else
  logerror "Wrong system, sorry!"
  exit 1
fi

# --- Zsh e Oh My Zsh ---
loginfo "Configurando Zsh e Oh My Zsh..."
if [ ! -d "$HOME/.oh-my-zsh" ]; then
  loginfo "Instalando Oh My Zsh..."
  /bin/sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
else
  loginfo "Oh My Zsh já está instalado."
fi

# Instala plugins do Zsh
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
loginfo "🔌 Instalando plugins do Zsh..."
if [ ! -d "${ZSH_CUSTOM}/plugins/zsh-autosuggestions" ]; then
  git clone https://github.com/zsh-users/zsh-autosuggestions "${ZSH_CUSTOM}/plugins/zsh-autosuggestions"
fi
if [ ! -d "${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting" ]; then
  git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting"
fi

# --- Configuração do Neovim com Lazy.nvim ---
loginfo "🐘 Configurando Neovim e Lazy.nvim..."
LAZY_PATH="$HOME/.local/share/nvim/lazy/lazy.nvim"
if [ ! -d "$LAZY_PATH" ]; then
  loginfo "Instalando o gerenciador de plugins Lazy.nvim..."
  git clone https://github.com/folke/lazy.nvim.git --filter=blob:none "$LAZY_PATH"
fi

# --- Gerenciador de Plugins do Tmux (TPM) ---
loginfo "🔄 Instalando TPM para Tmux..."
if [ ! -d "$HOME/.tmux/plugins/tpm" ]; then
  git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
fi

# --- Criação de Symlinks ---
loginfo "🔗 Criando symlinks para os arquivos de configuração..."

# Cria o diretório ~/.config se não existir
mkdir -p "$HOME/.config"

# Zsh
ln -sfn "$HOME/dotfiles/zsh/.zshrc" "$HOME/.zshrc"
ln -sfn "$HOME/dotfiles/zsh/.zprofile" "$HOME/.zprofile"
ln -sfn "$HOME/dotfiles/zsh/config/omtheme.zsh-theme" "$ZSH_CUSTOM/themes/omtheme.zsh-theme"

# Git
ln -sfn "$HOME/dotfiles/git/.gitconfig" "$HOME/.gitconfig"

# Tmux
ln -sfn "$HOME/dotfiles/tmux/.tmux.conf" "$HOME/.tmux.conf"

# Vim (para compatibilidade)
ln -sfn "$HOME/dotfiles/vim/.vimrc" "$HOME/.vimrc"

# Neovim
ln -sfn "$HOME/dotfiles/nvim" "$HOME/.config/nvim"

# Ghostty
ln -sfn "$HOME/dotfiles/ghostty" "$HOME/.config/ghostty"

# --- Finalização ---
loginfo "✅ Script de instalação concluído!"
echo -e "
[1;33mATENÇÃO: Passos manuais necessários:[0m"
echo "1. Abra o Neovim ('nvim') para que o Lazy.nvim possa instalar todos os plugins."
echo "2. Inicie o Tmux e pressione 'prefix + I' (Ctrl+b + I) para instalar os plugins do TPM."
echo "3. Reinicie seu terminal para que todas as alterações tenham efeito."
