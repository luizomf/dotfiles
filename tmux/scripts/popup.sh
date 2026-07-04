#!/usr/bin/env bash

SESSION_NAME="${1:-float}"
WINDOW_NAME="${2:-term}"
CURDIR="${3:-$(tmux display-message -p '#{pane_current_path}')}"

CURRENT_SESSION=$(tmux display-message -p "#{session_name}")

if [ "${CURRENT_SESSION}" = "${SESSION_NAME}" ]; then
  # We are inside the popup, so we detach
  tmux detach-client
else
  # I dont't remember why I put this line here, but it was causing problems
  # tmux send-keys "$(tmux display-message -p '#{pane_name}')" C-m

  # We are not in a popup, then check if a session exist
  if ! tmux has-session -t "${SESSION_NAME}" 2> /dev/null; then
      # If not, we create it
      tmux new-session -d -s "${SESSION_NAME}" -n "${WINDOW_NAME}1" -c "${CURDIR}"
      tmux set status
      # tmux new-window  -d -t "${SESSION_NAME}" -n "${WINDOW_NAME}2" -c "${CURDIR}"
  fi

  # Open the popup
  # -E: closes when command ends
  # attach: attach to the floating session
  tmux popup -d "#{pane_current_path}" -xC -yC -w90% -h90% \
      -E "tmux attach -t ${SESSION_NAME}"
fi
