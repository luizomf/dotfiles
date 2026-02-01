#!/usr/bin/env bash

CURDIR=$(pwd)
nvim -c 'startinsert' /tmp/quicknote.tmp
RAW_NOTE="${1:-$(cat /tmp/quicknote.tmp)}"
rm /tmp/quicknote.tmp

[[ -z "$RAW_NOTE" ]] && exit 1
cd "${PROJECTS_DIR}/notes" || exit 1

PROMPT=""
PROMPT+="Act as a Technical Documentation Librarian assistant.\n"
PROMPT+="This prompt is used in an automated script. Do NOT add conversational text, opinions, or explanations.\n"
PROMPT+="Only produce the requested artifacts.\n"
PROMPT+="\n"
PROMPT+="The user will provide a raw note containing technical information.\n"
PROMPT+="This note is meant to be stored and searched in the future.\n"
PROMPT+="\n"
PROMPT+="Your responsibility is to transform this note into a well-organized Markdown document\n"
PROMPT+="and prepare it to be committed to a GitHub repository.\n"
PROMPT+="\n"
PROMPT+="Your tasks:\n"
PROMPT+="1. Convert the note into a valid, well-structured Markdown file.\n"
PROMPT+="2. Include the provided date and time in the document metadata or header.\n"
PROMPT+="3. Choose the most appropriate category and create a subdirectory under 'files/'.\n"
PROMPT+="   Example: files/python/, files/linux/, files/docker/.\n"
PROMPT+="4. Generate a clear, descriptive filename in UPPER_SNAKE_CASE.\n"
PROMPT+="   Example: SAMBA_DIRECTORY_SHARE.md.\n"
PROMPT+="5. Place the file inside the chosen category directory.\n"
PROMPT+="   Example: files/linux/SAMBA_DIRECTORY_SHARE.md.\n"
PROMPT+="6. Generate a Conventional Commits–compatible commit message describing the addition.\n"
PROMPT+="7. Whatever you create, always push it to GitHub (create, commit and push).\n"
PROMPT+="\n"
PROMPT+="You MAY rewrite, expand, or clarify the original note if it improves technical clarity,\n"
PROMPT+="but you must preserve the original meaning and intent.\n"
PROMPT+="\n"
PROMPT+="Do NOT invent facts, commands, or configurations that are not implied by the note.\n"
PROMPT+="\n"
PROMPT+="Raw user note:\n"
PROMPT+="${RAW_NOTE}\n"
PROMPT+="\n"
PROMPT+="Current date:\n"
PROMPT+="$(date "+%Y-%m-%dT%H:%M:%S")\n"

gemini -y -p "$PROMPT"

cd "${CURDIR}" || exit 1

