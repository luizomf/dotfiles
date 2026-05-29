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

# Codex CLI
# printf "%s\n" "${PROMPT}" | codex exec --yolo --ephemeral

# Gemini CLI
# # Gemini will be discontinued (July 18)
# printf "%s\n" "${PROMPT}" | gemini -y -p -

# Antigravity CLI (any)
# printf "%s\n" "${PROMPT}" | agy --dangerously-skip-permissions --print -

# Claude Code
printf "%s\n" "${PROMPT}" | claude --model claude-opus-4-8 --effort xhigh \
  --no-session-persistence --dangerously-skip-permissions \
  -p -

cd "${CURDIR}" || exit 1

