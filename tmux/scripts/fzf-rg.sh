#!/usr/bin/env bash
# shellcheck disable=SC2016

set -euo pipefail

PREFERRED_ROOT="${1:-}"
TARGET_PANE="${2:-${TMUX_PANE:-}}"

LIMIT="${FZF_RG_LIMIT:-1000}"
MAX_DEPTH="${FZF_RG_DEPTH:-8}"
MAX_FILESIZE="${FZF_RG_MAX_FILESIZE:-1M}"
EDITOR_CMD="${FZF_TMUX_EDITOR:-${EDITOR:-nvim}}"
FIELD_SEPARATOR=$'\t'

ROOTS=()

add_root() {
  local root="$1"
  local existing

  [[ -d "$root" ]] || return 0

  if (( ${#ROOTS[@]} > 0 )); then
    for existing in "${ROOTS[@]}"; do
      [[ "$existing" == "$root" ]] && return 0
    done
  fi

  ROOTS+=("$root")
}

vim_string() {
  local value

  value="$(printf '%s' "$1" | sed "s/'/''/g")"
  printf "'%s'" "$value"
}

short_path() {
  local file="$1"
  local root
  local best_root=""
  local best_rel=""

  if (( ${#ROOTS[@]} > 0 )); then
    for root in "${ROOTS[@]}"; do
      root="${root%/}"

      if [[ "$file" == "$root"/* && ${#root} -gt ${#best_root} ]]; then
        best_root="$root"
        best_rel="${file#"$root"/}"
      fi
    done
  fi

  if [[ -n "$best_root" ]]; then
    printf '%s/%s' "$(basename "$best_root")" "$best_rel"
  else
    printf '%s' "${file/#$HOME/~}"
  fi
}

open_in_target_pane() {
  local file="$1"
  local line="$2"
  local pane_command=""
  local shell_command
  local vim_command

  if [[ -n "$TARGET_PANE" ]]; then
    pane_command="$(tmux display-message -p -t "$TARGET_PANE" '#{pane_current_command}' 2>/dev/null || true)"
  fi

  case "$pane_command" in
    nvim|vim|vi|view)
      vim_command=":execute 'edit +$line ' . fnameescape($(vim_string "$file"))"
      tmux send-keys -t "$TARGET_PANE" C-\\ C-n Escape
      tmux send-keys -t "$TARGET_PANE" -l "$vim_command"
      tmux send-keys -t "$TARGET_PANE" C-m
      ;;
    *)
      shell_command="$EDITOR_CMD +$line $(printf '%q' "$file")"
      tmux send-keys -t "$TARGET_PANE" -l "$shell_command"
      tmux send-keys -t "$TARGET_PANE" C-m
      ;;
  esac
}

if [[ -z "$PREFERRED_ROOT" && -n "$TARGET_PANE" ]]; then
  PREFERRED_ROOT="$(tmux display-message -p -t "$TARGET_PANE" '#{pane_current_path}' 2>/dev/null || true)"
fi

add_root "${PREFERRED_ROOT:-$PWD}"

while IFS= read -r root; do
  add_root "$root"
done < <(tmux list-panes -a -F '#{pane_current_path}' 2>/dev/null || true)

[[ "${#ROOTS[@]}" -eq 0 ]] && ROOTS=("$PWD")

ROOTS_TEXT="$(printf '%s\n' "${ROOTS[@]}")"

export ROOTS_TEXT LIMIT MAX_DEPTH MAX_FILESIZE FIELD_SEPARATOR

SELECTED="$(
  fzf \
    --sync \
    --tmux center,90%,85% \
    --ansi \
    --disabled \
    --prompt="> " \
    --sort --algo=v2 --tiebreak=length \
    --delimiter="$FIELD_SEPARATOR" \
    --with-nth='{4}:{2}    {5}    {6..}' \
    --preview='
      file={1}
      line={2}
      start=$(( line > 10 ? line - 10 : 1 ))
      end=$(( line + 20 ))

      bat \
        --style=numbers \
        --color=always \
        --highlight-line "$line" \
        --line-range "$start:$end" \
        "$file" 2>/dev/null || sed -n "${start},${end}p" "$file"
    ' \
    --preview-window='right,60%,border-left,+0' \
    --bind 'change:reload:bash -c '"'"'
      query="${1:-}"
      roots=()

      short_path() {
        local file="$1"
        local root
        local best_root=""
        local best_rel=""

        if (( ${#roots[@]} > 0 )); then
          for root in "${roots[@]}"; do
            root="${root%/}"

            if [[ "$file" == "$root"/* && ${#root} -gt ${#best_root} ]]; then
              best_root="$root"
              best_rel="${file#"$root"/}"
            fi
          done
        fi

        if [[ -n "$best_root" ]]; then
          printf "%s/%s" "$(basename "$best_root")" "$best_rel"
        else
          printf "%s" "${file/#$HOME/~}"
        fi
      }

      [[ -z "$query" ]] && exit 0

      while IFS= read -r root; do
        [[ -n "$root" ]] && roots+=("$root")
      done <<< "$ROOTS_TEXT"

      [[ "${#roots[@]}" -eq 0 ]] && exit 0

      rg \
        --column \
        --line-number \
        --no-heading \
        --color=never \
        --smart-case \
        --hidden \
        --field-match-separator "$FIELD_SEPARATOR" \
        --max-depth "$MAX_DEPTH" \
        --max-filesize "$MAX_FILESIZE" \
        --glob "!.git" \
        --glob "!node_modules" \
        --glob "!.next" \
        --glob "!dist" \
        --glob "!build" \
        --glob "!venv" \
        --glob "!.venv" \
        -- "$query" "${roots[@]}" \
        | while IFS="$FIELD_SEPARATOR" read -r file line column text; do
          short="$(short_path "$file")"
          name="$(basename "$short")"
          dir="${short%/*}"
          [[ "$dir" == "$short" ]] && dir=""

          printf "%s%s%s%s%s%s%s%s%s%s%s\n" \
            "$file" "$FIELD_SEPARATOR" \
            "$line" "$FIELD_SEPARATOR" \
            "$column" "$FIELD_SEPARATOR" \
            "$name" "$FIELD_SEPARATOR" \
            "$dir" "$FIELD_SEPARATOR" \
            "$text"
        done \
        | awk "!seen[\$0]++" \
        | head -n "$LIMIT"
    '"'"' bash {q} || true' || exit 0
)"

[[ -z "${SELECTED:-}" ]] && exit 0

# Remove ANSI colors before parsing the tab-separated rg fields.
CLEAN_SELECTED="$(
  printf '%s' "$SELECTED" | perl -pe 's/\e\[[0-9;]*m//g'
)"

IFS=$'\t' read -r FILE LINE _ <<< "$CLEAN_SELECTED"

[[ -z "${FILE:-}" || -z "${LINE:-}" ]] && exit 0
[[ "$LINE" =~ ^[0-9]+$ ]] || exit 0

open_in_target_pane "$FILE" "$LINE"
