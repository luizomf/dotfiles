export PATH="/usr/local/bin:/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"

# Keep non-interactive zsh sessions usable over SSH without loading the full
# interactive config.
export OLLAMA_HOST="${OLLAMA_HOST:-192.168.0.109:11434}"
export OLLAMA_TIMEOUT_MS="${OLLAMA_TIMEOUT_MS:-10000}"
export OLLAMA_LOAD_TIMEOUT="${OLLAMA_LOAD_TIMEOUT:-10m}"
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-10m}"
export LOCAL_MODEL="${LOCAL_MODEL:-qwen3.6:35b-a3b-mxfp8}"
export MODEL="${MODEL:-$LOCAL_MODEL}"
