#!/usr/bin/env bash
# Source-only installer policy. No commands run until a function is called.

configure_install_interaction() {
  [[ "${OM_INSTALL_ASSUME_YES:-0}" == "1" ]] || return 0

  # Homebrew honors NONINTERACTIVE; Git must not ask for HTTPS credentials.
  export NONINTERACTIVE=1 GIT_TERMINAL_PROMPT=0
  unset INTERACTIVE
  # Also prevent stdin prompts in third-party installers and Git identity setup.
  exec < /dev/null
  # Keep privilege checks non-interactive even when a controlling TTY exists.
  # This function only affects this installer, not the user's shell.
  # shellcheck disable=SC2329 # Installed for subsequent sudo calls in install.sh.
  sudo() { command sudo -n "$@"; }
}

detect_install_platform() {
  local kernel=$1 distro=${2:-} ostree=${3:-0}
  case "$kernel:$distro" in
    Darwin:*) printf 'darwin\n' ;;
    Linux:ubuntu) printf 'ubuntu\n' ;;
    Linux:arch|Linux:omarchy)
      [[ "$ostree" != 1 ]] || return 1
      printf 'arch\n'
      ;;
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

install_platform_packages() {
  local platform=$1 platforms provider package _option
  local native_packages=() brew_packages=() pacman_options=(-S --needed)

  case "$platform" in
    darwin)
      install_homebrew
      brew update
      brew bundle --file="$REPO_DIR/homebrew/Brewfile"
      return
      ;;
    ubuntu|fedora|arch) ;;
    *) printf 'Unsupported package platform: %s\n' "$platform" >&2; return 1 ;;
  esac

  while read -r platforms provider package _option || [[ -n "$platforms" ]]; do
    [[ -n "$platforms" && "$platforms" != \#* ]] || continue
    case ",$platforms," in
      *",$platform,"*)
        case "$provider" in
          native) native_packages+=("$package") ;;
          brew) brew_packages+=("$package") ;;
        esac
        ;;
    esac
  done < "$REPO_DIR/config/packages.list"

  loginfo "Installing $platform development and terminal packages..."
  case "$platform" in
    ubuntu)
      sudo DEBIAN_FRONTEND=noninteractive apt-get update
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${native_packages[@]}"
      ;;
    fedora)
      # Preserve Asahi/host repositories, kernels, graphics and services.
      sudo dnf install -y "${native_packages[@]}"
      ;;
    arch)
      # Use the host's existing sync database. Never perform a partial upgrade
      # (-Sy) or take over Omarchy's system-update/repository policy.
      if [[ "${OM_INSTALL_ASSUME_YES:-0}" == 1 ]]; then
        pacman_options+=(--noconfirm)
      fi
      sudo pacman "${pacman_options[@]}" "${native_packages[@]}"
      ;;
  esac

  install_homebrew
  brew install "${brew_packages[@]}"
}
