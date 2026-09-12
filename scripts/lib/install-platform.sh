#!/usr/bin/env bash
# Source-only installer policy. No commands run until a function is called.

detect_install_platform() {
  local kernel=$1 distro=${2:-} ostree=${3:-0}
  case "$kernel:$distro" in
    Darwin:*) printf 'darwin\n' ;;
    Linux:ubuntu) printf 'ubuntu\n' ;;
    Linux:fedora|Linux:fedora-asahi-remix)
      # DNF mutation is not the deployment model for Atomic/OSTree hosts.
      [[ "$ostree" != 1 ]] || return 1
      printf 'fedora\n'
      ;;
    *) return 1 ;;
  esac
}

require_new_toolchain_dir() {
  local target=$1
  if [[ -e "$target" || -L "$target" ]]; then
    printf 'Refusing to replace existing toolchain directory: %s\n' "$target" >&2
    printf 'Repair its installation or PATH, then rerun the installer.\n' >&2
    return 1
  fi
}

install_fedora_packages() {
  loginfo "Installing Fedora development and terminal packages..."
  # Based on the working Fedora Asahi environment. Use virtual capabilities
  # for zlib/wget so Fedora can select zlib-ng and wget2 implementations.
  # Do not change Asahi kernels, graphics drivers, boot, SSH or repositories.
  sudo dnf install -y \
    aria2 autoconf automake bzip2-devel cmake curl fd-find ffmpeg-free \
    gcc gcc-c++ gdbm-devel gettext git glibc-langpack-en htop libffi-devel \
    libtool llvm lua lua-devel luarocks make nano ncurses-devel ninja-build \
    openssl openssl-devel pkgconf python3-devel readline-devel ripgrep \
    sqlite sqlite-devel tcl tcl-devel tk tk-devel tree unzip util-linux \
    vim-enhanced wget xz-devel zlib-devel zsh fastfetch tmux just

  install_homebrew
  # Keep the distro tmux fallback for explicit/non-interactive callers, while
  # also installing the preferred interactive Homebrew version.
  # Keep the same providers used by the interactive environment on fedoraair.
  # Personal services/projects (Ollama, EdgeTTS, etc.) are not provisioned here.
  brew install bash-completion@2 bat fzf gh glow hf lazygit neovim rtk \
    trash-cli tree-sitter-cli tmux pi-coding-agent
}
