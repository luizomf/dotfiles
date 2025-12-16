#!/usr/bin/env bash

SESSION_NAME="${1:-float_popup}"
CURRENT_SESSION=$(tmux display-message -p "#{session_name}")

if [ "$CURRENT_SESSION" = "$SESSION_NAME" ]; then
  # We are inside the popup, so we detach
  tmux detach-client
else

  # We are not in a popup, then check if a session exist
  if ! tmux has-session -t "$SESSION_NAME" 2> /dev/null; then
      # If not, we create it
      tmux new-session -d -s "$SESSION_NAME"
  fi

  # Open the popup
  # -E: closes when command ends
  # attach: attach to the floating session
  tmux popup -d "#{pane_current_path}" -xC -yC -w80% -h75% \
      -E "tmux attach -t $SESSION_NAME"
fi
