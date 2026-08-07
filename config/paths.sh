#!/usr/bin/env bash

# Shared host paths for interactive shells and unattended scripts.
# Use OM_PATHS_FILE at supported call sites to select a machine-specific file.
: "${HOME:?HOME must be set}"

export PROJECTS_DIR="${HOME}/Desktop/tutoriais_e_cursos"
