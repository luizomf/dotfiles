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
set clipboard=unnamed
set nowrap
packadd! hlyank
colorscheme omtheme
set background=dark

" ### Opens the file in the same position where I left it
autocmd BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") | exe "normal! g`\"" | endif

" ### SEARCH
set hlsearch
set incsearch

" ### KEYMAPS
let mapleader = " "

" map: Maps in Normal, Visual, Select, and Operator-pending modes.
" nmap: Normal mode only.
" imap: Insert mode only.
" vmap: Visual mode only.
" noremap: Non-recursive (safer, prevents loops).
" <CR>: Carriage Return (Enter key).
" <Esc>: Escape key.
" <C-s>: Control + s.
" <leader>: Your defined leader key (e.g., space or \).

nnoremap <leader>ff :Files<CR>
nnoremap <leader>w :w<CR>
inoremap jj <Esc> 
nnoremap <leader>h :noh<CR>
nnoremap <Tab> :bn<CR>

" ### CURSOR SHAPE
let &t_SI = "\<Esc>[6 q" " SI = Start Insert mode -> cursor em linha
let &t_EI = "\<Esc>[2 q" " EI = End Insert mode -> cursor em bloco (Normal mode)
set guicursor=n-v-c:block,i-ci-ve:ver25,r-cr:hor20,o:hor50

