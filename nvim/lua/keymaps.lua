vim.g.mapleader = " "

local map = vim.keymap.set
local opts = { noremap = true, silent = true }

-- Insert mode: jj = ESC
map("i", "jj", "<Esc>", opts)

-- Delete no insert
map("i", "<C-h>", "<BS>", opts)
map("i", "<C-l>", "<Del>", opts)

-- Navegação entre splits
map("n", "<C-h>", "<C-w>h", opts)
map("n", "<C-j>", "<C-w>j", opts)
map("n", "<C-k>", "<C-w>k", opts)
map("n", "<C-l>", "<C-w>l", opts)

-- Leader shortcuts
map("n", "<leader>w", ":w<CR>", opts)
map("n", "<leader>q", ":q<CR>", opts)
-- map("n", "<leader>x", ":x<CR>", opts)
map("n", "<leader>h", ":noh<CR>", opts)

-- Diagnósticos (LSP)
map("n", "gl", vim.diagnostic.open_float, opts)

-- Telescope
local builtin = require("telescope.builtin")
map("n", "<leader>ff", builtin.find_files, { desc = "Find files" })
map("n", "<leader>fg", builtin.live_grep, { desc = "Live grep" })
map("n", "<leader>fb", builtin.buffers, { desc = "List open buffers" })
map("n", "<leader>fh", builtin.help_tags, { desc = "Search help tags" })
map("n", "<leader>fo", builtin.oldfiles, { desc = "Recently opened files" })
map("n", "<leader>fc", builtin.current_buffer_fuzzy_find, { desc = "Fuzzy search in current buffer" })
map("n", "<leader>fr", builtin.resume, { desc = "Resume last Telescope picker" })
map("n", "<leader>fs", builtin.lsp_document_symbols, { desc = "Document symbols (LSP)" })

-- Buffers
map("n", "<leader><tab>", "<C-^>", { desc = "Toggle last buffer" })
map("n", "<Tab>", ":bnext<CR>", opts)
map("n", "<S-Tab>", ":bprevious<CR>", opts)
map("n", "<leader>bd", ":bdelete<CR>", { desc = "Fechar buffer" })
map("n", "<leader>bu", "<cmd>edit #<CR>", { desc = "Reabrir último buffer" })
