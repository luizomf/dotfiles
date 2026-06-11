#!/usr/bin/env bash

export FZF_DEFAULT_COMMAND='fd --type f --strip-cwd-prefix --hidden --follow --exclude .git'
export FZF_DEFAULT_OPTS=${FZF_DEFAULT_OPTS:-}"
  --color=fg:#eae8ff,fg+:#56b8ff,bg:#000010,bg+:#151520
  --color=hl:#56b8ff,hl+:#ffffff,info:#56b8ff,marker:#56b8ff
  --color=prompt:#eeeeff,spinner:#56b8ff,pointer:#56b8ff,header:#56b8ff
  --color=gutter:#151520,border:#151520,separator:#151520,scrollbar:#56b8ff
  --color=label:#56b8ff,query:#ccccee
  --border=\"rounded\" --border-label=\"tmux\" --border-label-pos=\"0\" 
  --preview-window=\"border-rounded\"
  --padding=\"0\" --margin=\"0\" --prompt=\"> \" --marker=\">\"
  --pointer=\"◆\" --separator=\"─\" --scrollbar=\"│\" --layout=\"reverse\""

SELECTED="$(tmux list-window \
  -a -F "#S:#I #W #P #D" | \
  fzf --sync \
  --sort --algo=v2 --tiebreak=length \
  --tmux center,50%,50%
)"

[[ -z $SELECTED ]] && exit 0

tmux switch-client -t "$(echo "$SELECTED" | awk "{print \$1}")"
