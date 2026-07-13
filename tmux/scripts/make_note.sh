#!/usr/bin/env bash
#
# Quick-note capture for the LLM Wiki at $PROJECTS_DIR/notes.
#
# Flow (see notes/CLAUDE.md for the schema):
#   1. capture  — open nvim, dump raw text into sources/inbox/ (Layer 1). This is
#                 frictionless and is committed immediately so nothing is lost.
#   2. ingest   — a *cheaper* model reads AGENTS.md + index.md and decides whether
#                 the dump is a new note / an update / a merge, writes the curated
#                 note (Layer 2), wires links, updates index.md + log.md, and
#                 commits+pushes. The expensive model is kept for manual curation.
#
# Bound in tmux to C-b C-n (popup).

# --- config -----------------------------------------------------------------
# Cheap model on the capture->ingest path. Override in the environment to escalate
# (e.g. NOTES_INGEST_MODEL=claude-opus-4-8 NOTES_INGEST_EFFORT=high).
: "${NOTES_INGEST_MODEL:=sonnet}"
: "${NOTES_INGEST_EFFORT:=medium}"

NOTES_DIR="${PROJECTS_DIR}/notes"
CURDIR="$(pwd)"
TMP="/tmp/quicknote.md"

# --- 1. capture (Layer 1) ---------------------------------------------------
: > "$TMP"
nvim -c 'startinsert' "$TMP"
RAW_NOTE="${1:-$(cat "$TMP")}"
rm -f "$TMP"

# nothing meaningful typed -> touch nothing, exit clean
if [[ -z "${RAW_NOTE//[[:space:]]/}" ]]; then
  echo "empty note, nothing captured."
  exit 0
fi

cd "$NOTES_DIR" || { echo "notes dir not found: $NOTES_DIR"; exit 1; }

TS="$(date '+%Y-%m-%dT%H-%M-%S')"
SLUG="$(printf '%s' "$RAW_NOTE" | head -c 60 | tr '[:upper:]' '[:lower:]' \
        | tr -cs 'a-z0-9' '-' | sed 's/^-*//; s/-*$//')"
[[ -z "$SLUG" ]] && SLUG="note"
RAW_FILE="sources/inbox/${TS}-${SLUG}.md"

mkdir -p sources/inbox
{
  printf -- '---\n'
  printf 'date: %s\n' "$(date '+%Y-%m-%dT%H:%M:%S')"
  printf 'source: tmux-quicknote\n'
  printf 'status: raw\n'
  printf -- '---\n\n'
  printf '%s\n' "$RAW_NOTE"
} > "$RAW_FILE"

# commit the raw capture right away so a failed ingest never loses the idea
git add "$RAW_FILE"
git commit -q -m "chore(inbox): capture raw note ${TS}" || true

# --- 2. ingest (Layer 1 -> Layer 2) -----------------------------------------
PROMPT="Read AGENTS.md in the current directory before doing anything else.
Then perform the *ingest* operation defined there on the raw source file below.

Raw source file: ${RAW_FILE}

Decide whether this is a NEW note, an UPDATE to an existing note, or a MERGE into
one — prefer updating/merging over creating a near-duplicate. Read index.md to
decide placement and links. Write or update the curated note under files/<topic>/,
wire wikilinks and reciprocal backlinks, register it in index.md, and append a
line to log.md.

Current date: $(date '+%Y-%m-%dT%H:%M:%S')

Execute completely: make the edits, then commit and push. Include every file you
touched (the curated note, index.md, log.md, and any backlinked notes)."

printf '%s\n' "$PROMPT" | claude --model "$NOTES_INGEST_MODEL" --effort "$NOTES_INGEST_EFFORT" \
  --no-session-persistence --dangerously-skip-permissions -p -

# --- alternative CLIs (pipe the same $PROMPT) -------------------------------
# printf '%s\n' "$PROMPT" | codex exec --yolo --ephemeral
# printf '%s\n' "$PROMPT" | gemini -y -p -
# printf '%s\n' "$PROMPT" | agy --dangerously-skip-permissions --print -

cd "$CURDIR" || exit 1
