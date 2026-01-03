#!/usr/bin/env bash

SELECTED="$(tmux list-window -a -F "#S:#I #W #P #D" | fzf --sync --tmux center)"

[[ -z $SELECTED ]] && exit 0

tmux switch-client -t "$(echo "$SELECTED" | awk "{print \$1}")"
