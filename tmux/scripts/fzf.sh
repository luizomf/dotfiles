#!/usr/bin/env bash

# The target and path remain searchable, but only the fixed-width row is displayed.
# LIST="$(tmux list-window -a -F $'#S:#I\t#{?window_active,◆, }  #{=14;p14:#{session_name}:#{window_index}}  #{=22;p22:#{?#{@pi_status},#{@pi_status},#{pane_title}}}  #{=10;p10:window_name}  #{window_panes} #{?#{==:#{window_panes},1},pane,panes}\t#{pane_current_path}')"
LIST="$(tmux list-window -a -F $'#S:#I\t#{?window_active,◆, }  #{=24;p24:#{session_name}:#{window_index}}  #{=24;p24:#{?#{@pi_status},#{@pi_status},#{pane_title}}}  #{=24;p24:window_name}')"
# Pi publishes tmux styles; fzf needs their ANSI equivalents.
LIST="${LIST//#\[fg=green\]/$'\033[32m'}"
LIST="${LIST//#\[fg=red\]/$'\033[31m'}"
LIST="${LIST//#\[fg=default\]/$'\033[39m'}"
WINDOW_COUNT="$(printf '%s\n' "$LIST" | wc -l | tr -d ' ')"
POPUP_HEIGHT=$((WINDOW_COUNT + 5))
((POPUP_HEIGHT > 20)) && POPUP_HEIGHT=20

LIST_FILE="$(mktemp "${TMPDIR:-/tmp}/tmux-windows.XXXXXX")"
trap 'rm -f "$LIST_FILE"' EXIT
printf '%s\n' "$LIST" >"$LIST_FILE"

FZF_TMUX_CMD=(
  fzf
  --ansi
  '--color=fg:#eae8ff,fg+:#6bccff,bg:#141418,bg+:#242428,hl:#f0f0ff,hl+:#ffffff,info:#6bccff,marker:#6bccff,prompt:#f0f0ff,spinner:#6bccff,pointer:#6bccff,header:#6bccff,gutter:#1c1c1f,border:#2c2c2f,separator:#2c2c2f,scrollbar:#6bccff,label:#6bccff,query:#ffffff'
  --border=rounded
  '--border-label= windows '
  --border-label-pos=0
  --padding=0
  --margin=0
  '--prompt=> '
  '--marker=>'
  --pointer=◆
  --separator=─
  --scrollbar=│
  --layout=reverse
  --disabled
  --no-sort
  --delimiter=$'\t'
  --with-nth=2
  --bind="change:reload(fzf --filter={q} --algo=v2 --tiebreak=length < '$LIST_FILE' || true)"
  --header='Enter: switch · Esc: close'
  --tmux="center,80%,${POPUP_HEIGHT}"
)

SELECTED="$(printf '%s\n' "$LIST" | "${FZF_TMUX_CMD[@]}")"
[[ -z $SELECTED ]] && exit 0

TARGET="${SELECTED%%$'\t'*}"
tmux switch-client -t "$TARGET"
