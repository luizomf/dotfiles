#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
if [[ $(uname -s) != Darwin ]]; then
  printf 'texteditor defaults tests skipped: macOS required\n'
  exit 0
fi

# Preview and invalid arguments must never apply associations.
preview=$(/usr/bin/swift "$repo/scripts/lib/texteditor-defaults.swift" --list)
[[ "$preview" == *'Preview only.'* ]]
for identifier in public.source-code public.script public.utf16-plain-text; do
  grep -q "^TYPE $identifier$" <<< "$preview"
done
for extension in txt md js ts py json yaml sh; do
  grep -q "^$extension: " <<< "$preview"
done
if grep -qE '^(TYPE |[^ ]+: )(public\.(data|content|item|jpeg|png|movie|zip-archive|executable|unix-executable)|com\.adobe\.pdf)$' <<< "$preview"; then
  printf 'Preview includes a protected file type\n' >&2
  exit 1
fi

if /usr/bin/swift "$repo/scripts/lib/texteditor-defaults.swift" --invalid >/dev/null 2>&1; then
  printf 'Invalid arguments unexpectedly accepted\n' >&2
  exit 1
fi
printf 'texteditor defaults preview tests passed\n'
