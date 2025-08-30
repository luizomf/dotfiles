vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.cursorline = true
vim.opt.colorcolumn = { 80 }

vim.opt.backupcopy = "yes" -- It fixed the bun error on --watch --hot

vim.opt.encoding = "utf-8"
vim.opt.fileencoding = "utf-8"

vim.opt.tabstop = 2
vim.opt.shiftwidth = 2
vim.opt.expandtab = true
vim.opt.autoindent = true
vim.opt.smartindent = true

vim.opt.mouse = ""
vim.opt.clipboard = "unnamedplus"
vim.opt.wrap = false
vim.opt.hlsearch = true
vim.opt.incsearch = true

-- Tenta manter o cursor mais ao centro no scroll
vim.opt.scrolloff = math.floor(vim.o.lines * 0.145)
vim.opt.sidescrolloff = math.floor(vim.o.columns * 0.08)

vim.opt.sessionoptions =
  "blank,buffers,curdir,folds,help,tabpages,winsize,winpos,terminal,localoptions"

vim.cmd("syntax on")

-- Render tabs and white spaces
vim.opt.list = true
vim.opt.listchars = "tab:>-,trail:-,lead:·,eol:¬"

-- restaura posição do cursor
vim.cmd([[
  autocmd BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") |
    \ exe "normal! g`\"" | endif
]])

-- highlight on yank
vim.api.nvim_create_autocmd("TextYankPost", {
  callback = function()
    vim.highlight.on_yank({ higroup = "IncSearch", timeout = 1000 })
  end,
})
