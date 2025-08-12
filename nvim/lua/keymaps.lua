vim.g.mapleader = " "

local map = vim.keymap.set
local opts = { noremap = true, silent = true }
local utils = require("settings.utils")

-- Insert mode: jj = ESC
map("i", "jj", "<Esc>", opts)

-- Delete no insert
-- map("i", "<C-h>", "<BS>", opts)
-- map("i", "<C-l>", "<Del>", opts)

-- Navegação entre splits
map("n", "<C-h>", "<C-w>h", opts)
map("n", "<C-j>", "<C-w>j", opts)
map("n", "<C-k>", "<C-w>k", opts)
map("n", "<C-l>", "<C-w>l", opts)

-- Leader shortcuts
map("n", "<leader>w", ":w<CR>", opts)
map("n", "<leader>h", ":noh<CR>", opts)

-- diagnostics (LSP)
map("n", "gl", vim.diagnostic.open_float, opts)

-- Toggle diagnostics on/off
map("n", "<leader>dt", function()
  if vim.diagnostic.is_enabled() then
    utils.notify("Diagnostic disabled")
    vim.diagnostic.enable(false)
  else
    utils.notify("Diagnostic enabled")
    vim.diagnostic.enable()
  end
end)

-- Conform format
map({ "n", "v" }, "<leader>f", function()
  utils.notify("Manually formatting with <leader>f...", vim.log.levels.INFO)
  require("conform").format({ async = false, lsp_fallback = true })
end, { desc = "Format file or range (conform)" })

-- Telescope
local builtin = require("telescope.builtin")
map("n", "<leader>ff", builtin.find_files, { desc = "Find files" })
map("n", "<leader>fg", builtin.live_grep, { desc = "Live grep" })
map("n", "<leader>fb", builtin.buffers, { desc = "List open buffers" })
map("n", "<leader>fh", builtin.help_tags, { desc = "Search help tags" })
map("n", "<leader>fo", builtin.oldfiles, { desc = "Recently opened files" })
map(
  "n",
  "<leader>fc",
  builtin.current_buffer_fuzzy_find,
  { desc = "Fuzzy search in current buffer" }
)
map(
  "n",
  "<leader>fr",
  builtin.resume,
  { desc = "Resume last Telescope picker" }
)
map(
  "n",
  "<leader>fs",
  builtin.lsp_document_symbols,
  { desc = "Document symbols (LSP)" }
)

-- Buffers
map("n", "<leader><tab>", "<C-^>", { desc = "Toggle last buffer" })
map("n", "<Tab>", ":bnext<CR>", opts)
map("n", "<S-Tab>", ":bprevious<CR>", opts)
map("n", "<leader>bd", ":bdelete<CR>", { desc = "Fechar buffer" })
map("n", "<leader>bu", "<C-^>", { desc = "Reabrir último buffer" })

-- WrapIn
-- Wrap com parênteses
map(
  "v",
  "<leader>wp",
  "<Esc><Cmd>lua require('settings.utils').wrap_in_chars('(')<CR>",
  { desc = "Wrap parentheses - ( and )" }
)
map(
  "v",
  "<leader>wq",
  "<Esc><Cmd>lua require('settings.utils').wrap_in_chars('\\'')<CR>",
  { desc = "Wrap single quotes - ' and '" }
)
map(
  "v",
  "<leader>wQ",
  "<Esc><Cmd>lua require('settings.utils').wrap_in_chars('\"')<CR>",
  { desc = 'Wrap double quotes - " and "' }
)
map(
  "v",
  "<leader>ws",
  "<Esc><Cmd>lua require('settings.utils').wrap_in_chars('[')<CR>",
  { desc = "Wrap square brackets - [ and ]" }
)
map(
  "v",
  "<leader>wc",
  "<Esc><Cmd>lua require('settings.utils').wrap_in_chars('{')<CR>",
  { desc = "Wrap curly braces - { and }" }
)
map(
  "v",
  "<leader>wb",
  "<Esc><Cmd>lua require('settings.utils').wrap_in_chars('`')<CR>",
  { desc = "Wrap backtick - ` and `" }
)
map(
  "v",
  "<leader>wh",
  "<Esc><Cmd>lua require('settings.utils').wrap_in_chars('<')<CR>",
  { desc = "Wrap HTML - < and >" }
)

-- Word Wrap
vim.keymap.set("n", "<leader>ww", function()
  if vim.wo.wrap then
    vim.opt.wrap = false
    vim.opt.linebreak = false
    vim.opt.breakindent = false
    utils.notify("Softwrap desativado", vim.log.levels.INFO)
  else
    vim.opt.wrap = true
    vim.opt.linebreak = true
    vim.opt.breakindent = true
    utils.notify("Softwrap ativado", vim.log.levels.INFO)
  end
end, { desc = "Toggle Softwrap" })

-- Toggle Spell -- Toggle Spell Checker
vim.keymap.set("n", "<leader>ss", function()
  if vim.wo.spell then
    vim.opt.spell = false
    utils.notify("Spell checker desativado", vim.log.levels.INFO)
  else
    vim.opt.spell = true
    vim.opt.spelllang = { "pt_br", "en_us", "en", "pt" }
    utils.notify("Spell checker ativado", vim.log.levels.INFO)
  end
end, { desc = "Toggle Spell Checker" })
