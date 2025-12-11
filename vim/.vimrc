call plug#begin('~/.vim/plugged')

" Fuzzy finder para arquivos, buffers, etc.
Plug 'junegunn/fzf', { 'do': { -> fzf#install() } }
Plug 'junegunn/fzf.vim'

call plug#end()

set number
set relativenumber
set nocursorline
"set colorcolumn=80 
set backupcopy=yes 
set expandtab
syntax on
set tabstop=2
set shiftwidth=2
set expandtab
set autoindent
set smartindent
set mouse=a
" Cursor Shape
let &t_SI = "\<Esc>[6 q" " SI = Start Insert mode -> cursor em linha
let &t_EI = "\<Esc>[2 q" " EI = End Insert mode -> cursor em bloco (Normal mode)

set guicursor=n-v-c:block,i-ci-ve:ver25,r-cr:hor20,o:hor50

