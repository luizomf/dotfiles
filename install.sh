#!/bin/bash

# função para printar logs de forma legível
log() {
  echo -e "
[1;34m$1[0m"
}

# garante que o script pare em caso de erro
set -e

# --- Homebrew e Brewfile ---
log "🍺 Verificando e instalando dependências com Homebrew..."
if ! command -v brew &> /dev/null; then
  log "Homebrew não encontrado. Instalando..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> "$HOME/.zprofile"
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  log "Homebrew já está instalado. Atualizando..."
  brew update
fi

# Para gerar o Brewfile
# brew bundle dump --file=~/dotfiles/homebrew/Brewfile --describe --force
log "📦 Instalando pacotes e aplicações do Brewfile..."
brew bundle --file="$HOME/dotfiles/homebrew/Brewfile"

# --- Zsh e Oh My Zsh ---
log "Configurando Zsh e Oh My Zsh..."
if [ ! -d "$HOME/.oh-my-zsh" ]; then
  log "Instalando Oh My Zsh..."
  /bin/sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
else
  log "Oh My Zsh já está instalado."
fi

# Instala plugins do Zsh
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
log "🔌 Instalando plugins do Zsh..."
if [ ! -d "${ZSH_CUSTOM}/plugins/zsh-autosuggestions" ]; then
  git clone https://github.com/zsh-users/zsh-autosuggestions "${ZSH_CUSTOM}/plugins/zsh-autosuggestions"
fi
if [ ! -d "${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting" ]; then
  git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting"
fi

# --- Configuração do Neovim com Lazy.nvim ---
log "🐘 Configurando Neovim e Lazy.nvim..."
LAZY_PATH="$HOME/.local/share/nvim/lazy/lazy.nvim"
if [ ! -d "$LAZY_PATH" ]; then
  log "Instalando o gerenciador de plugins Lazy.nvim..."
  git clone https://github.com/folke/lazy.nvim.git --filter=blob:none "$LAZY_PATH"
fi

# --- Gerenciador de Plugins do Tmux (TPM) ---
log "🔄 Instalando TPM para Tmux..."
if [ ! -d "$HOME/.tmux/plugins/tpm" ]; then
  git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
fi

# --- Criação de Symlinks ---
log "🔗 Criando symlinks para os arquivos de configuração..."

# Cria o diretório ~/.config se não existir
mkdir -p "$HOME/.config"

# Zsh
ln -sfn "$HOME/dotfiles/zsh/.zshrc" "$HOME/.zshrc"
ln -sfn "$HOME/dotfiles/zsh/.zprofile" "$HOME/.zprofile"

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
log "✅ Script de instalação concluído!"
echo -e "
[1;33mATENÇÃO: Passos manuais necessários:[0m"
echo "1. Abra o Neovim ('nvim') para que o Lazy.nvim possa instalar todos os plugins."
echo "2. Inicie o Tmux e pressione 'prefix + I' (Ctrl+b + I) para instalar os plugins do TPM."
echo "3. Reinicie seu terminal para que todas as alterações tenham efeito."
