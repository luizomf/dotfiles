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

# codex exec "$PROMPT" --yolo
# gemini -y -p "$PROMPT"
nohup gemini -p "$PROMPT" -y > /dev/null 2>&1 < /dev/null &
# claude --model claude-sonnet-4-6 -p "$PROMPT" --dangerously-skip-permissions

sleep 5
echo "Sleeping for 5 seconds..."
cd "${CURDIR}" || exit 1

