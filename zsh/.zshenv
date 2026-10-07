# Minimal setup for every Zsh. Later login/interactive files can overwrite it.
# Global profiles reset/reorder PATH on Alpine/macOS, so reapply the shared PATH
# in .zprofile and after interactive toolchain initialization as well.
source "$HOME/dotfiles/zsh/config/env"
source "$HOME/dotfiles/zsh/config/path" --initial
