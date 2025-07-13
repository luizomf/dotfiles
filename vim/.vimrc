" --- Básico ---
set number              " mostra número das linhas
syntax on               " highlight de sintaxe
set tabstop=2           " tabulação com 2 espaços
set shiftwidth=2
set expandtab
set autoindent
set smartindent
set mouse=a             " permite uso do mouse (opcional)
set clipboard=unnamed   " usa clipboard do sistema (pode mudar pra unnamedplus se der problema)
set nowrap              " não quebra linhas automaticamente

" --- Histórico e posição ---
set viminfo=            " desativa histórico persistente (registers, marks etc.)
" Caso queira manter histórico mínimo, substitua por:
" set viminfo='20,\"50
autocmd BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") | exe "normal! g`\"" | endif

" --- Busca ---
set hlsearch            " destaca resultado da busca
set incsearch           " busca incremental enquanto digita

" --- Mapeamentos estilo Zed / qualidade de vida ---
inoremap jj <Esc>       " jj pra sair do modo insert

" Backspace no insert com Ctrl+h
inoremap <C-h> <BS>
nnoremap <C-h> X        " Deleta caractere à esquerda no normal mode

" Delete no insert com Ctrl+l
inoremap <C-l> <Del>
nnoremap <C-l> x        " Deleta caractere sob o cursor

" --- Navegação entre splits com Ctrl + hjkl ---
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-h> <C-w>h
nnoremap <C-l> <C-w>l

" --- Leader Key ---
let mapleader=" "
nnoremap <leader>w :w<CR>        " salvar com <space>w
nnoremap <leader>q :q<CR>        " sair com <space>q
nnoremap <leader>x :x<CR>        " salvar e sair com <space>x
nnoremap <leader>h :noh<CR>      " limpar highlight de busca com <space>h

" Cursor shapes por modo
" normal / visual / command  = bloco
" insert / cmd-insert / visual-ex = vertical
" replace / cmd-replace      = horizontal
" operator-pending           = horizontal maior
set guicursor=n-v-c:block,i-ci-ve:ver25,r-cr:hor20,o:hor50
