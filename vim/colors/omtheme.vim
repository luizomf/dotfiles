" omtheme.vim: a custom color scheme
" maintainer: Luiz Otávio Miranda
" license: MIT
" last change: 2025 Dec 13

" Clear any existing highlights
highlight clear

" Check if syntax highlighting is on
if exists("syntax_on")
  syntax reset
endif

" Set the name of the color scheme
let g:colors_name="omtheme"

" Set the background to dark or light, as appropriate for your design
set background=dark

" Yeap!! That is it... Nothing. I'm relying on the terminal
" Maybe I'll change this later. We'll see.

