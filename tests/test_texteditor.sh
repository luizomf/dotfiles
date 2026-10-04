#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/bin" "$tmp/home" "$tmp/work"
export CAPTURE="$tmp/arguments"
cat > "$tmp/bin/open" <<'SH'
#!/usr/bin/env bash
printf '%s\0' "$PWD" "$@" > "$CAPTURE"
SH
chmod +x "$tmp/bin/open"
export PATH="$tmp/bin:$PATH" HOME="$tmp/home" SHELL=/bin/sh
cd "$tmp/work"

check() {
  local actual=() argument i
  while IFS= read -r -d '' argument; do
    actual+=("$argument")
  done < "$CAPTURE"
  local expected=("$HOME" -na OMXterm --args -e /bin/sh -lc
    'exec nvim -n -- "$@"' texteditor "$@")
  [[ ${#actual[@]} -eq ${#expected[@]} ]]
  for ((i = 0; i < ${#expected[@]}; i++)); do
    [[ "${actual[i]}" == "${expected[i]}" ]]
  done
}

"$repo/scripts/texteditor"
check

# Shell syntax in filenames must remain literal data.
# shellcheck disable=SC2016
files=("file with spaces.txt" "it's a file.txt" '-R' '+quit' '$(touch INJECTED)' $'line\nbreak.txt' '/tmp/ação.txt')
"$repo/scripts/texteditor" "${files[@]}"
expected=()
for file in "${files[@]}"; do
  case "$file" in
    /*) expected+=("$file") ;;
    *) expected+=("$PWD/$file") ;;
  esac
done
check "${expected[@]}"

export SHELL=
"$repo/scripts/texteditor" "${files[@]}"
check "${expected[@]}"

# Exercise the shell boundary without opening a terminal or running real Neovim.
cat > "$tmp/bin/nvim" <<'SH'
#!/usr/bin/env bash
printf '%s\0' "$@" > "$CAPTURE"
SH
chmod +x "$tmp/bin/nvim"
for shell in /bin/sh /bin/bash /bin/zsh; do
  [[ -x "$shell" ]] || continue
  "$shell" -c 'exec nvim -n -- "$@"' texteditor "${expected[@]}"
  actual=()
  while IFS= read -r -d '' argument; do
    actual+=("$argument")
  done < "$CAPTURE"
  [[ "${actual[0]}" == -n && "${actual[1]}" == -- ]]
  [[ ${#actual[@]} -eq $((${#expected[@]} + 2)) ]]
  for ((i = 0; i < ${#expected[@]}; i++)); do
    [[ "${actual[i + 2]}" == "${expected[i]}" ]]
  done
done
[[ ! -e INJECTED ]]
printf 'texteditor tests passed\n'
