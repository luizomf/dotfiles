call plug#begin('~/.vim/plugged')

" Fuzzy finder para arquivos, buffers, etc.
Plug 'junegunn/fzf', { 'do': { -> fzf#install() } }
Plug 'junegunn/fzf.vim'
call plug#end()

packadd! hlyank
syntax on

set nocompatible
set number
set relativenumber
set nocursorline
"set colorcolumn=80
set backupcopy=yes
set expandtab
set tabstop=2
set shiftwidth=2
set expandtab
set autoindent
set smartindent
set mouse=a
set clipboard=unnamed
set nowrap
set backspace=indent,eol,start
set formatoptions-=t
set nostartofline
set ruler
set showmatch
set showmode
set showcmd
set textwidth=80
set title
set hlsearch
set incsearch

set notermguicolors
set t_Co=256
colorscheme sorbet
set background=dark

highlight Normal ctermbg=NONE guibg=NONE
highlight NonText ctermbg=NONE guibg=NONE
highlight EndOfBuffer ctermbg=NONE guibg=NONE
highlight LineNr ctermbg=NONE guibg=NONE
highlight SignColumn ctermbg=NONE guibg=NONE
highlight RedundantWhitespace ctermbg=blue guibg=blue
match RedundantWhitespace /\s\+$\| \+\ze\t/

" ### Opens the file in the same position where I left it
autocmd BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") | exe "normal! g`\"" | endif

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

" INSERT
inoremap jj <Esc>

" NORMAL (MISC)
nnoremap <leader>ff :Files<CR>
nnoremap <leader>w :w<CR>
nnoremap <leader>h :noh<CR>

" NORMAL (BUFFERS)
nnoremap <leader><Tab> <C-^><CR>
nnoremap <Tab> :bnext<CR>
nnoremap <S-Tab> :bprevious<CR>
nnoremap <leader>bd :bdelete<CR>
nnoremap <leader>bu <C-^><CR>


" ### CURSOR SHAPE
let &t_SI = "\<Esc>[6 q" " SI = Start Insert mode -> cursor em linha
let &t_EI = "\<Esc>[2 q" " EI = End Insert mode -> cursor em bloco (Normal mode)
set guicursor=n-v-c:block,i-ci-ve:ver25,r-cr:hor20,o:hor50

let g:home = $HOME
let g:sessions = g:home . "/.local/share/vim/sessions"
let g:current_dir = getcwd(-1)
let g:session_id = tolower(substitute(g:current_dir[1:], '[^a-zA-z0-9_\.\-]', '_', 'gi'))
let g:cur_session_path = g:sessions . '/' . g:session_id . '.vim'


call mkdir(g:sessions, "p")

if filereadable(g:cur_session_path)
  autocmd VimEnter * execute "source " . expand(g:cur_session_path) 
endif

autocmd VimLeavePre * execute "mksession! " . expand(g:cur_session_path) 

