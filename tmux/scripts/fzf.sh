#!/usr/bin/env bash

SELECTED="$(tmux list-window \
  -a -F "#S:#I #W #P #D" | \
  fzf --sync \
  --sort --algo=v2 --tiebreak=length \
  --tmux center,90%,85%
)"

[[ -z $SELECTED ]] && exit 0

tmux switch-client -t "$(echo "$SELECTED" | awk "{print \$1}")"
