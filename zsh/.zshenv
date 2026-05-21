# Keep user-managed toolchains ahead of Homebrew in non-interactive zsh
# sessions. This prevents Homebrew's node/npm from shadowing nvm when a parent
# process already exported NVM_BIN.
path=("${(@)path:#${HOME:-/Users/luizotavio}/.local/bin}")
path=("${HOME:-/Users/luizotavio}/.local/bin" "${path[@]}")

path=("${(@)path:#/usr/local/bin}")
path=("${(@)path:#/opt/homebrew/bin}")
path=("${(@)path:#/opt/homebrew/sbin}")
path=("${path[@]}" /usr/local/bin /opt/homebrew/bin /opt/homebrew/sbin)
typeset -gU path

export PATH

# Keep non-interactive zsh sessions usable over SSH without loading the full
# interactive config.
export OLLAMA_HOST="${OLLAMA_HOST:-192.168.0.109:11434}"
export PROJECTS_DIR="${HOME:-/Users/luizotavio}/Desktop/tutoriais_e_cursos"
export OLLAMA_TIMEOUT_MS="${OLLAMA_TIMEOUT_MS:-10000}"
export OLLAMA_LOAD_TIMEOUT="${OLLAMA_LOAD_TIMEOUT:-10m}"
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-10m}"
export LOCAL_MODEL="${LOCAL_MODEL:-qwen3.6:35b-a3b-mxfp8}"
export MODEL="${MODEL:-$LOCAL_MODEL}"
