vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.cursorline = true

vim.opt.tabstop = 2
vim.opt.shiftwidth = 2
vim.opt.expandtab = true
vim.opt.autoindent = true
vim.opt.smartindent = true

vim.opt.mouse = "a"
vim.opt.clipboard = "unnamedplus"
vim.opt.wrap = false
vim.opt.hlsearch = true
vim.opt.incsearch = true

vim.cmd("syntax on")

-- restaura posição do cursor
vim.cmd([[
  autocmd BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") |
    \ exe "normal! g`\"" | endif
]])
