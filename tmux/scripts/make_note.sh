#!/usr/bin/env bash

CURDIR=$(pwd)
nvim -c 'startinsert' /tmp/quicknote.tmp
RAW_NOTE="${1:-$(cat /tmp/quicknote.tmp)}"
rm /tmp/quicknote.tmp

[[ -z "$RAW_NOTE" ]] && exit 1
cd "${PROJECTS_DIR}/notes" || exit 1

PROMPT=""

PROMPT+="Read AGENTS.md in the current directory before doing anything else.\n"
PROMPT+="It contains all instructions for how to handle the note below.\n"
PROMPT+="\n"
PROMPT+="Raw note:\n"
PROMPT+="${RAW_NOTE}\n"
PROMPT+="\n"
PROMPT+="Current date: $(date "+%Y-%m-%dT%H:%M:%S")\n"
PROMPT+="\n"
PROMPT+="Execute completely: write the file, commit, and push.\n"

gemini -y -p "$PROMPT"
# claude --model claude-sonnet-4-6 -p "$PROMPT" --dangerously-skip-permissions

cd "${CURDIR}" || exit 1

