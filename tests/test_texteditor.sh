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
  # Execute this exact captured command below, rather than a hand-copied version.
  editor_command=${actual[7]}
  local expected=("$HOME" -na OMXterm --args -e /bin/sh -lc
    "$editor_command" texteditor "$@")
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
#!/bin/bash
printf '%s\0' "$@" > "$CAPTURE"
if [[ ${REQUIRE_NODE:-} == 1 ]]; then
  command -v node > "$CAPTURE.node"
fi
SH
chmod +x "$tmp/bin/nvim"
for shell in /bin/sh /bin/bash /bin/zsh; do
  [[ -x "$shell" ]] || continue
  "$shell" -c "$editor_command" texteditor "${expected[@]}"
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
# Finder's environment lacks NVM's Node. Use a PATH with only our test stubs.
mkdir -p "$tmp/nvm/bin"
cat > "$tmp/nvm/nvm.sh" <<'SH'
export PATH="$NVM_DIR/bin:$PATH"
printf loaded > "$CAPTURE.nvm"
SH
printf '#!/bin/sh\nexit 0\n' > "$tmp/nvm/bin/node"
chmod +x "$tmp/nvm/bin/node"
for shell in /bin/sh /bin/bash /bin/zsh; do
  [[ -x "$shell" ]] || continue
  rm -f "$CAPTURE.nvm"
  PATH="$tmp/bin" NVM_DIR="$tmp/nvm" REQUIRE_NODE=1 \
    "$shell" -c "$editor_command" texteditor "${expected[@]}"
  [[ $(< "$CAPTURE.node") == "$tmp/nvm/bin/node" ]]
  [[ $(< "$CAPTURE.nvm") == loaded ]]

  # An already available Node must not be replaced by NVM initialization.
  rm "$CAPTURE.nvm"
  PATH="$tmp/nvm/bin:$tmp/bin" NVM_DIR="$tmp/nvm" REQUIRE_NODE=1 \
    "$shell" -c "$editor_command" texteditor
  [[ ! -e "$CAPTURE.nvm" ]]

  # NVM is optional: without it, opening the editor still works.
  PATH="$tmp/bin" NVM_DIR="$tmp/missing-nvm" \
    "$shell" -c "$editor_command" texteditor
done
[[ ! -e INJECTED ]]
printf 'texteditor tests passed\n'
