#!/usr/bin/env bash

# The target remains searchable, but only the fixed-width row is displayed.
LIST_FORMAT=$'#S:#I\t#{?window_active,✚, }  #{=16;p16:#{session_name}:#{window_index}}  #{=36;p36:#{?#{@pi_status},#{@pi_status},#{pane_title}}}  #{=16;p16:window_name}'
# Strip the hidden rank after sorting; unvisited windows fall back to session/index.
LIST="$(tmux list-windows -a -F "#{?@window_mru,#{@window_mru},0}"$'\t'"$LIST_FORMAT" |
  LC_ALL=C sort -t $'\t' -k1,1nr -k2,2V |
  cut -f2-)"
# Add ANSI colors after tmux pads the columns so escape sequences do not affect alignment.
LIST="${LIST//󰓅/$'\033[32m󰓅\033[39m'}"
LIST="${LIST///$'\033[31m\033[39m'}"
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
  '--prompt=❱ '
  '--marker=❯'
  --pointer='❭'
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
