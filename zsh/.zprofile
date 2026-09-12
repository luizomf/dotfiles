# Docker Desktop's macOS path must not leak into Linux login shells.
if [[ "$OSTYPE" == darwin* ]]; then
  export PATH="$PATH:$HOME/.docker/bin"
fi
# End of Docker Desktop section.

# Set PATH, MANPATH, etc., for Homebrew.
# eval "$(/opt/homebrew/bin/brew shellenv)"
