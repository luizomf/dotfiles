#!/usr/bin/env bash

export FZF_DEFAULT_COMMAND='fd --type f --strip-cwd-prefix --hidden --follow --exclude .git'
export FZF_DEFAULT_OPTS=${FZF_DEFAULT_OPTS:-}"
  --color=fg:#eae8ff,fg+:#6bccff,bg:#0f0f14,bg+:#202026
  --color=hl:#f0f0ff,hl+:#ffffff,info:#6bccff,marker:#6bccff
  --color=prompt:#f0f0ff,spinner:#6bccff,pointer:#6bccff,header:#6bccff
  --color=gutter:#202026,border:#202026,separator:#202026,scrollbar:#6bccff
  --color=label:#6bccff,query:#ffffff
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
