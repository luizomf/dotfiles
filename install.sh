#!/bin/bash

# Funcao para printar logs
log() {
  echo -e "\n\033[1;34m$1\033[0m"
}

# --- Homebrew e Brewfile ---
log "🍺 Verificando e instalando dependências com Homebrew..."
if ! command -v brew &> /dev/null; then
  log "Homebrew não encontrado. Instalando..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> ~/.zprofile
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  log "Homebrew já está instalado. Atualizando..."
  brew update
fi

# Instala tudo do Brewfile
brew bundle --file=~/dotfiles/homebrew/Brewfile

# --- Zsh e Oh My Zsh ---
log "셸 Verificando e instalando Oh My Zsh e plugins..."
if [ ! -d "$HOME/.oh-my-zsh" ]; then
  log "Instalando Oh My Zsh..."
  /bin/sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# --- Neovim e LazyVim ---
log "🚀 Configurando Neovim e LazyVim..."
# Remove configuracao antiga do nvim se existir
rm -rf ~/.config/nvim
# Clona o LazyVim para a pasta de dotfiles
rm -rf ~/dotfiles/nvim/* # Limpa a pasta antes de clonar
git clone https://github.com/LazyVim/starter ~/dotfiles/nvim
# Cria o symlink para o local esperado pelo nvim
ln -sfn ~/dotfiles/nvim ~/.config/nvim
else
  log "Oh My Zsh já está instalado."
fi

# Plugins do Zsh
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
if [ ! -d "${ZSH_CUSTOM}/plugins/zsh-autosuggestions" ]; then
  git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM}/plugins/zsh-autosuggestions
fi
if [ ! -d "${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting" ]; then
  git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting
fi

# --- Gerenciadores de Plugins (Vim e Tmux) ---
log "🔌 Instalando gerenciadores de plugins..."

# vim-plug para Vim
if [ ! -f "$HOME/.vim/autoload/plug.vim" ]; then
  curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
fi

# tpm para Tmux
if [ ! -d "$HOME/.tmux/plugins/tpm" ]; then
  git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
fi

# --- Symlinks ---
log "🔗 Criando symlinks..."
ln -sf ~/dotfiles/zsh/.zshrc ~/.zshrc
ln -sf ~/dotfiles/zsh/.zprofile ~/.zprofile
ln -sf ~/dotfiles/vim/.vimrc ~/.vimrc
ln -sf ~/dotfiles/tmux/.tmux.conf ~/.tmux.conf
ln -sf ~/dotfiles/git/.gitconfig ~/.gitconfig

# --- Finalização ---
log "✅ Script de instalação concluído!"
echo -e "\n\033[1;33mATENÇÃO: Passos manuais necessários:\033[0m"
echo "1. Inicie o Vim e execute \`:PlugInstall\` para instalar os plugins."
echo "2. Inicie o Tmux e pressione \`prefix + I\` (Ctrl+b + I) para instalar os plugins."
echo "3. Reinicie seu terminal para que todas as alterações tenham efeito."
