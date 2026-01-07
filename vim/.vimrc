" Download plug.vim to ~/.vim/autoload
"
" curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
"   https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
"
call plug#begin('~/.vim/plugged')
" fzf
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
"set autoindent
"set smartindent
set noautoindent
set nosmartindent
set mouse=""
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
" set title
set hlsearch
set incsearch

set notermguicolors
set t_Co=256
" colorscheme habamax " Nice
colorscheme sorbet " Nice
" colorscheme lunaperche " Nice
" colorscheme pablo " Nice
" colorscheme slate " Nice
" colorscheme wildcharm " Nice
" colorscheme zaibatsu " Nice
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

" CURSOR SHAPE
let &t_SI = "\<Esc>[6 q" " SI = Start Insert mode -> cursor em linha
let &t_EI = "\<Esc>[2 q" " EI = End Insert mode -> cursor em bloco (Normal mode)
set guicursor=n-v-c:block,i-ci-ve:ver25,r-cr:hor20,o:hor50

" Really Simple Auto Session (KISS)
let s:sessions_dir = split(&runtimepath, ',')[0] . '/sessions'

function! s:session_id() abort
  " usa cwd e sanitiza para nome de arquivo
  let l:cwd = getcwd()
  return tolower(substitute(l:cwd, '[^A-Za-z0-9_.-]', '_', 'g'))
endfunction

function! s:session_path() abort
  return s:sessions_dir . '/' . s:session_id() . '.vim'
endfunction

if !isdirectory(s:sessions_dir)
  call mkdir(s:sessions_dir, 'p')
endif

augroup SimpleAutoSession
  autocmd!
  autocmd VimEnter * call s:maybe_load()
  autocmd VimLeavePre * call s:maybe_save()
augroup END

function! s:maybe_load() abort
  if argc() > 0
    return
  endif

  let l:path = s:session_path()
  if filereadable(l:path)
    execute 'source' fnameescape(l:path)
  endif
endfunction

function! s:maybe_save() abort
  if argc() > 0
    return
  endif

  let l:path = s:session_path()
  execute 'mksession!' fnameescape(l:path)
endfunction
