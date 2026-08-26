#!/usr/bin/env zsh
# vim: set filetype=zsh :

# Git prompt config
ZSH_THEME_GIT_PROMPT_PREFIX="%F{12}❴"
ZSH_THEME_GIT_PROMPT_SUFFIX="%F{12}❵ "
ZSH_THEME_GIT_PROMPT_DIRTY="%F{1} ✱%f%k"
ZSH_THEME_GIT_PROMPT_CLEAN="%f%k"

# Desativa o prompt padrão do venv - (.venv)
# Sem isso, o tema duplicaria o nome do venv
typeset -g VIRTUAL_ENV_DISABLE_PROMPT=1

# Prompt principal
PROMPT=$([ -z $SSH_CONNECTION ] || echo "[SSH] ")
PROMPT+=$'%F{4}%n%f%k@%F{4}%m%f%k:'
PROMPT+=$'%F{13}%1~%f%k\\$ '
PROMPT+=$'$(git_prompt_info)'
PROMPT+=$'%F{14}${VIRTUAL_ENV:+❴${VIRTUAL_ENV:t}❵ }%f%k'
PROMPT+=$'%(?::%F{1}❴✖ %?❵%f%k )'
PROMPT+=$'\n%f%k'
PROMPT+='${VIM_PROMPT_FG_COLOR}${VIM_PROMPT_BG_COLOR}${VIM_PROMPT_SYMBOL}%f%k '
