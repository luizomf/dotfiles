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
  local platform ids manager
  if [[ "$kernel" == Darwin ]]; then
    printf 'darwin\n'
    return
  fi
  [[ "$kernel" == Linux && "$ostree" != 1 && -n "$distro" ]] || return 1
  while read -r platform ids manager || [[ -n "$platform" ]]; do
    [[ -n "$platform" && "$platform" != \#* && "$ids" != - ]] || continue
    case ",$ids," in
      *",$distro,"*) printf '%s\n' "$platform"; return ;;
    esac
  done < "$REPO_DIR/config/install-platforms.list"
  return 1
}

install_package_manager() {
  local target=$1 platform ids manager
  while read -r platform ids manager || [[ -n "$platform" ]]; do
    [[ "$platform" == "$target" ]] || continue
    printf '%s\n' "$manager"
    return
  done < "$REPO_DIR/config/install-platforms.list"
  printf 'Unsupported package platform: %s\n' "$target" >&2
  return 1
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
  local platform=$1 platforms provider package _option manager
  manager=$(install_package_manager "$platform") || return $?
  local native_packages=() brew_packages=() pacman_options=(-S --needed)

  case "$manager" in
    brew)
      install_homebrew
      brew update
      brew bundle --file="$REPO_DIR/homebrew/Brewfile"
      return
      ;;
    apt|dnf|pacman) ;;
    *) printf 'Unsupported package manager: %s\n' "$manager" >&2; return 1 ;;
  esac

  while read -r platforms provider package _option || [[ -n "$platforms" ]]; do
    [[ -n "$platforms" && "$platforms" != \#* ]] || continue
    case ",$platforms," in
      *",$platform,"*|*",$manager,"*)
        case "$provider" in
          native) native_packages+=("$package") ;;
          brew) brew_packages+=("$package") ;;
        esac
        ;;
    esac
  done < "$REPO_DIR/config/packages.list"

  loginfo "Installing $platform development and terminal packages..."
  case "$manager" in
    apt)
      sudo DEBIAN_FRONTEND=noninteractive apt-get update
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${native_packages[@]}"
      ;;
    dnf)
      # Preserve Asahi/host repositories, kernels, graphics and services.
      sudo dnf install -y "${native_packages[@]}"
      ;;
    pacman)
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
