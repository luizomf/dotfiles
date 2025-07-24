#!/bin/sh
# vim: set filetype=sh :

# Cores compatíveis com todos os terminais (ANSI 0–15)
# Foreground - padrão (0–7)
local FG_BLACK="%F{0}"        # black
local FG_RED="%F{1}"          # red
local FG_GREEN="%F{2}"        # green
local FG_YELLOW="%F{3}"       # yellow
local FG_BLUE="%F{4}"         # blue
local FG_MAGENTA="%F{5}"      # magenta
local FG_CYAN="%F{6}"         # cyan
local FG_WHITE="%F{7}"        # white

# Foreground - bright (8–15)
local FG_BRIGHT_BLACK="%F{8}"     # bright black (gray)
local FG_BRIGHT_RED="%F{9}"       # bright red
local FG_BRIGHT_GREEN="%F{10}"    # bright green
local FG_BRIGHT_YELLOW="%F{11}"   # bright yellow
local FG_BRIGHT_BLUE="%F{12}"     # bright blue
local FG_BRIGHT_MAGENTA="%F{13}"  # bright magenta
local FG_BRIGHT_CYAN="%F{14}"     # bright cyan
local FG_BRIGHT_WHITE="%F{15}"    # bright white

# Background - padrão (0–7)
local BG_BLACK="%K{0}"        # black
local BG_RED="%K{1}"          # red
local BG_GREEN="%K{2}"        # green
local BG_YELLOW="%K{3}"       # yellow
local BG_BLUE="%K{4}"         # blue
local BG_MAGENTA="%K{5}"      # magenta
local BG_CYAN="%K{6}"         # cyan
local BG_WHITE="%K{7}"        # white

# Background - bright (8–15)
local BG_BRIGHT_BLACK="%K{8}"     # bright black (gray)
local BG_BRIGHT_RED="%K{9}"       # bright red
local BG_BRIGHT_GREEN="%K{10}"    # bright green
local BG_BRIGHT_YELLOW="%K{11}"   # bright yellow
local BG_BRIGHT_BLUE="%K{12}"     # bright blue
local BG_BRIGHT_MAGENTA="%K{13}"  # bright magenta
local BG_BRIGHT_CYAN="%K{14}"     # bright cyan
local BG_BRIGHT_WHITE="%K{15}"    # bright white

# Reset
local RESET_FG="%f"
local RESET_BG="%k"
local RESET_ALL="%f%k"

# Git prompt config
ZSH_THEME_GIT_PROMPT_PREFIX=" ${FG_CYAN}("
ZSH_THEME_GIT_PROMPT_SUFFIX="${FG_CYAN})${RESET_ALL}"
ZSH_THEME_GIT_PROMPT_DIRTY="${FG_RED} ✘${RESET_ALL}"
ZSH_THEME_GIT_PROMPT_CLEAN="${FG_GREEN} ✔${RESET_ALL}"

# Prompt principal
PROMPT='${FG_YELLOW}%~${FG_RESET}$(git_prompt_info)'
PROMPT+=' %(?:${FG_GREEN} :${FG_RED}[✖ %?])'
PROMPT+=$'\n'
PROMPT+='${VIM_PROMPT_FG_COLOR}${VIM_PROMPT_BG_COLOR}${VIM_PROMPT_SYMBOL} ${RESET_ALL}'
