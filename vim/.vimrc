call plug#begin('~/.vim/plugged')

" Fuzzy finder para arquivos, buffers, etc.
Plug 'junegunn/fzf', { 'do': { -> fzf#install() } }
Plug 'junegunn/fzf.vim'

call plug#end()

" --- Atalhos para FZF ---
" Ctrl+P para buscar arquivos (similar ao VSCode/Sublime)
nnoremap <C-p> :Files<CR>

set number
set relativenumber
set nocursorline
set colorcolumn=80 
set backupcopy=yes 
set expandtab
syntax on
set tabstop=2
set shiftwidth=2
set expandtab
set autoindent
set smartindent
set mouse=a

set encoding=utf-8
set fileencoding=utf-8

set autoindent
set smartindent

set clipboard=unnamed
set wrap
set hlsearch
set incsearch
set nowrap

set sessionoptions=blank,buffers,curdir,folds,help,tabpages,winsize,winpos,terminal,localoptions
set list
set listchars=tab:>-,trail:-,lead:·,eol:¬

set viminfo=
autocmd BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") | exe "normal! g`\"" | endif

inoremap jj <Esc>

let mapleader=" "
nnoremap <leader>w :w<CR>        " salvar com <space>w
nnoremap <leader>q :q<CR>        " sair com <space>q
nnoremap <leader>x :x<CR>        " salvar e sair com <space>x
nnoremap <leader>h :noh<CR>      " limpar highlight de busca com <space>h

" Cursor Shape
let &t_SI = "\<Esc>[6 q" " SI = Start Insert mode -> cursor em linha
let &t_EI = "\<Esc>[2 q" " EI = End Insert mode -> cursor em bloco (Normal mode)

set guicursor=n-v-c:block,i-ci-ve:ver25,r-cr:hor20,o:hor50

