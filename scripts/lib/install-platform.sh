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

# Alpine normally supplies doas, not sudo. Other platforms keep their existing
# sudo path, including configure_install_interaction's unattended wrapper.
run_install_privileged() {
  local platform=$1
  shift
  if [[ "$platform" == alpine ]] && command -v doas > /dev/null 2>&1; then
    if [[ "${OM_INSTALL_ASSUME_YES:-0}" == 1 ]]; then
      doas -n "$@"
    else
      doas "$@"
    fi
  else
    sudo "$@"
  fi
}

validate_install_compiler() {
  local name=$1 value=$2 resolved
  resolved=$(command -v "$value") || resolved=""
  if [[ -z "$resolved" || ! -x "$resolved" ]] || ! "$value" --version > /dev/null 2>&1; then
    printf '%s=%s is unusable. Set %s to one executable compiler name/path (no flags), or unset it for automatic selection.\n' \
      "$name" "$value" "$name" >&2
    return 1
  fi
}

# Call inside the plugin subprocess, never the user's shell or Brew setup.
configure_install_compilers() {
  [[ "$1" == lfs ]] || return 0
  local prefix driver version best=0 selected_cc="" selected_cxx=""
  if [[ ${CC+x} ]]; then validate_install_compiler CC "$CC" || return $?; fi
  if [[ ${CXX+x} ]]; then validate_install_compiler CXX "$CXX" || return $?; fi
  if [[ ! ${CC+x} || ! ${CXX+x} ]]; then
    if [[ ! ${CC+x} ]]; then
      selected_cc=$(PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        type -P cc || PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        type -P gcc) || selected_cc=""
    fi
    if [[ ! ${CXX+x} ]]; then
      selected_cxx=$(PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        type -P c++ || PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        type -P g++) || selected_cxx=""
    fi
    if [[ ( ! ${CC+x} && -z "$selected_cc" ) || ( ! ${CXX+x} && -z "$selected_cxx" ) ]]; then
      prefix=$(brew --prefix gcc) || return $?
      for driver in "$prefix"/bin/gcc-*; do
        version=${driver##*/gcc-}
        case "$version" in ''|*[!0-9]*) continue ;; esac
        [[ -x "$driver" && -x "$prefix/bin/g++-$version" ]] || continue
        if (( 10#$version > best )); then
          best=$((10#$version))
        fi
      done
      if (( best == 0 )); then
        printf 'No complete Brew GCC driver pair in %s/bin. Install/repair Brew gcc or set CC and CXX to executable drivers.\n' "$prefix" >&2
        return 1
      fi
      [[ -n "$selected_cc" ]] || selected_cc="$prefix/bin/gcc-$best"
      [[ -n "$selected_cxx" ]] || selected_cxx="$prefix/bin/g++-$best"
    fi
    if [[ ! ${CC+x} ]]; then CC=$selected_cc; fi
    if [[ ! ${CXX+x} ]]; then CXX=$selected_cxx; fi
  fi
  validate_install_compiler CC "$CC" || return $?
  validate_install_compiler CXX "$CXX" || return $?
  export CC CXX
}

install_platform_packages() {
  local platform=$1 platforms provider package _option manager
  manager=$(install_package_manager "$platform") || return $?
  local native_packages=() brew_packages=() pacman_options=(-S --needed)
  local runtime_only=0

  case "$manager" in
    brew)
      install_homebrew
      brew update
      brew bundle --file="$REPO_DIR/homebrew/Brewfile"
      return
      ;;
    linuxbrew)
      # Fedora-derived minimal roots need this for downloaded Node binaries.
      # Real LFS without DNF continues to supply its own native runtime libraries.
      if command -v dnf > /dev/null 2>&1; then
        sudo dnf install -y libatomic || return $?
      fi
      # Inspect only host-managed paths, never an inherited Homebrew/toolchain PATH.
      # Formula dependencies remain Homebrew's responsibility.
      while read -r platforms provider package _option || [[ -n "$platforms" ]]; do
        [[ -n "$platforms" && "$platforms" != \#* && "$provider" == brew ]] || continue
        case ",$platforms," in
          *",$platform,"*)
            if PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
              type -P "${_option:-$package}" > /dev/null; then
              loginfo "Keeping native ${_option:-$package} (skipping $package)."
            else
              brew_packages+=("$package")
            fi
            ;;
        esac
      done < "$REPO_DIR/config/packages.list"
      install_homebrew || return $?
      if ! PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        type -P cc > /dev/null; then
        runtime_only=1
        # GCC needs startup objects from Brew glibc on compiler-free bases.
        brew install glibc || return $?
      fi
      if (( ${#brew_packages[@]} )); then
        brew install "${brew_packages[@]}" || return $?
      fi
      if (( runtime_only )); then
        # Also repair an installed GCC whose earlier post-install failed.
        brew postinstall gcc || return $?
      fi
      return 0
      ;;
    apt|dnf|pacman|apk) ;;
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
    apk)
      # Use the host's configured repositories; no distro upgrade or glibc layer.
      run_install_privileged "$platform" apk add "${native_packages[@]}"
      return $?
      ;;
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
