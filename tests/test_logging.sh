#!/usr/bin/env bash

set -euo pipefail

# Exercise the public commands without requiring the dotfiles shell setup.
ROOT=$(cd "${BASH_SOURCE[0]%/*}/.." && pwd)
BASH_BIN=${BASH_BIN:-/bin/bash}
export PATH="$ROOT/scripts:$PATH"
export NO_COLOR=1
TEMP=$(mktemp -d)
trap 'rm -rf "$TEMP"' EXIT

check_output() {
  local expected=$1
  shift
  "$BASH_BIN" "$ROOT/scripts/logbase" "$@" >"$TEMP/out"
  printf '%s\n' "$expected" >"$TEMP/expected"
  cmp "$TEMP/expected" "$TEMP/out"
}

check_output '[info] hello world' -t info hello world
# Level commands accept literal arguments, including options and empty strings.
for level in info success warn error debug; do
  case "$level" in
    info) label=INFO; stream=out; other=err ;;
    success) label=SUCCESS; stream=out; other=err ;;
    warn) label=WARN; stream=err; other=out ;;
    error) label=ERROR; stream=err; other=out ;;
    debug) label=DEBUG; stream=err; other=out ;;
  esac
  "$BASH_BIN" "$ROOT/scripts/log$level" --help '' '%s' -t x >"$TEMP/out" 2>"$TEMP/err"
  printf '[%s] --help  %%s -t x\n' "$label" >"$TEMP/expected"
  cmp "$TEMP/expected" "$TEMP/$stream"
  test ! -s "$TEMP/$other"
  "$BASH_BIN" "$ROOT/scripts/log$level" >"$TEMP/out" 2>"$TEMP/err"
  printf '[%s] \n' "$label" >"$TEMP/expected"
  cmp "$TEMP/expected" "$TEMP/$stream"
done
# Invalid palette values must fail even when output is redirected.
for color in '' -1 256 08x 18446744073709551616; do
  if "$BASH_BIN" "$ROOT/scripts/logbase" -f "$color" text >"$TEMP/out" 2>"$TEMP/err"; then
    printf 'Unexpectedly accepted color: %s\n' "$color" >&2
    exit 1
  fi
  test ! -s "$TEMP/out"
  test -s "$TEMP/err"
done
check_output 'text' -f 008 -b 255 text
check_output '<tag> text --help' -t tag --open-tag '<' --close-tag '>' text --help
check_output ''
for option in -t -f -b --open-tag --close-tag --unknown; do
  if "$BASH_BIN" "$ROOT/scripts/logbase" "$option" >"$TEMP/out" 2>"$TEMP/err"; then
    printf 'Unexpectedly accepted incomplete/unknown option: %s\n' "$option" >&2
    exit 1
  fi
  test ! -s "$TEMP/out"
  test -s "$TEMP/err"
done
printf 'Logging checks passed\n'
