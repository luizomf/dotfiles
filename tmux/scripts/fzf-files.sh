#!/usr/bin/env bash
# shellcheck disable=SC2016

set -euo pipefail

PREFERRED_ROOT="${1:-}"
TARGET_PANE="${2:-${TMUX_PANE:-}}"

LIMIT="${FZF_FILE_LIMIT:-5000}"
MAX_DEPTH="${FZF_FILE_DEPTH:-8}"
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

emit_candidate() {
  local file="$1"
  local short
  local name
  local dir

  short="$(short_path "$file")"
  name="$(basename "$short")"
  dir="${short%/*}"
  [[ "$dir" == "$short" ]] && dir=""

  printf '%s%s%s%s%s\n' "$file" "$FIELD_SEPARATOR" "$name" "$FIELD_SEPARATOR" "$dir"
}

open_in_target_pane() {
  local file="$1"
  local pane_command=""
  local shell_command
  local vim_command

  if [[ -n "$TARGET_PANE" ]]; then
    pane_command="$(tmux display-message -p -t "$TARGET_PANE" '#{pane_current_command}' 2>/dev/null || true)"
  fi

  case "$pane_command" in
    nvim|vim|vi|view)
      vim_command=":execute 'edit ' . fnameescape($(vim_string "$file"))"
      tmux send-keys -t "$TARGET_PANE" C-\\ C-n Escape
      tmux send-keys -t "$TARGET_PANE" -l "$vim_command"
      tmux send-keys -t "$TARGET_PANE" C-m
      ;;
    *)
      shell_command="$EDITOR_CMD $(printf '%q' "$file")"
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

export FIELD_SEPARATOR

SELECTED_LINE="$(
  fd . "${ROOTS[@]}" \
    --type f \
    --max-depth "$MAX_DEPTH" \
    --exclude .git \
    --exclude .claude \
    --exclude node_modules \
    --exclude .next \
    --exclude dist \
    --exclude build \
    --exclude venv \
    --exclude .venv \
    | awk '!seen[$0]++' \
    | head -n "$LIMIT" \
    | while IFS= read -r file; do
      emit_candidate "$file"
    done \
    | fzf \
      --tmux center,90%,85% \
      --prompt="> " \
      --delimiter="$FIELD_SEPARATOR" \
      --with-nth='{2}    {3}' \
      --preview='
        file={1}
        mime="$(file -b --mime-type "$file" 2>/dev/null || true)"

        case "$mime" in
          image/*)
            printf "%s\n\n" "$file"
            if command -v chafa >/dev/null 2>&1; then
              rows=$(( ${FZF_PREVIEW_LINES:-24} - 6 ))
              [[ "$rows" -lt 8 ]] && rows=8
              chafa \
                --format=symbols \
                --animate=off \
                --size="${FZF_PREVIEW_COLUMNS:-80}x${rows}" \
                "$file" 2>/dev/null || true
              printf "\n"
            fi

            file "$file" 2>/dev/null || true
            printf "Size: %s bytes\n" "$(wc -c < "$file" | tr -d "[:space:]")"
            command -v identify >/dev/null 2>&1 && identify "$file" 2>/dev/null
            ;;
          text/*|application/json|application/xml|application/x-sh|application/x-shellscript)
            bat --style=numbers --color=always --line-range :200 "$file" 2>/dev/null ||
              sed -n "1,200p" "$file"
            ;;
          *)
            printf "%s\n\n" "$file"
            file "$file" 2>/dev/null || true
            printf "Size: %s bytes\n" "$(wc -c < "$file" | tr -d "[:space:]")"
            ;;
        esac

      ' \
      --preview-window='right,60%,border-left,+0' || exit 0
)"

[[ -z "${SELECTED_LINE:-}" ]] && exit 0

IFS=$'\t' read -r SELECTED _ <<< "$SELECTED_LINE"

[[ -z "${SELECTED:-}" ]] && exit 0

open_in_target_pane "$SELECTED"
