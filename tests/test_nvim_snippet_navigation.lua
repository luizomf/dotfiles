-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_snippet_navigation.lua
-- Real LuaSnip state and configured cmp callbacks; no LSP or external completion sources.
vim.opt.rtp:append(vim.fn.getcwd() .. "/nvim")
local data = vim.fn.stdpath("data")
vim.opt.rtp:append(data .. "/lazy/nvim-cmp")
vim.opt.rtp:append(data .. "/lazy/LuaSnip")
require("plugins.cmp")[1].config()
local cmp = require("cmp")
local luasnip = require("luasnip")
cmp.setup({ completion = { autocomplete = false }, sources = {} })

local buf = vim.api.nvim_create_buf(false, true)
vim.api.nvim_set_current_buf(buf)
vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "", "", "outside" })
luasnip.lsp_expand("call(${1:first}, ${2:second})$0")
vim.api.nvim_feedkeys("", "x", false)
vim.api.nvim_win_set_cursor(0, { 3, 0 })
local fell_back = false
cmp.get_config().mapping["<Tab>"].i(function()
  fell_back = true
end)
assert(fell_back, "Tab jumped back to an old snippet instead of falling back")
assert(
  vim.api.nvim_win_get_cursor(0)[1] == 3,
  "Tab moved the cursor back into the snippet"
)
fell_back = false
cmp.get_config().mapping["<S-Tab>"].i(function()
  fell_back = true
end)
assert(
  fell_back,
  "Shift-Tab jumped back to an old snippet instead of falling back"
)
assert(
  vim.api.nvim_win_get_cursor(0)[1] == 3,
  "Shift-Tab moved the cursor back into the snippet"
)
vim.api.nvim_win_set_cursor(0, { 1, 5 })
cmp.get_config().mapping["<Tab>"].i(function()
  error("Tab fell back inside a snippet")
end)
vim.api.nvim_feedkeys("", "x", false)
assert(
  vim.fn.expand("<cword>") == "second",
  "Tab did not reach the next placeholder"
)
cmp.get_config().mapping["<S-Tab>"].i(function()
  error("Shift-Tab fell back inside a snippet")
end)
vim.api.nvim_feedkeys("", "x", false)
assert(
  vim.fn.expand("<cword>") == "first",
  "Shift-Tab did not return to the previous placeholder"
)

luasnip.add_snippets(
  "all",
  { luasnip.parser.parse_snippet("omfixture", "new(${1:value})$0") }
)
vim.wo.virtualedit = "onemore"
vim.api.nvim_buf_set_lines(buf, 2, 3, false, { "omfixture" })
vim.api.nvim_win_set_cursor(0, { 3, #"omfixture" })
cmp.get_config().mapping["<Tab>"].i(function()
  error("New snippet expansion fell back")
end)
vim.api.nvim_feedkeys("", "x", false)
assert(
  vim.api.nvim_buf_get_lines(buf, 2, 3, false)[1] == "new(value)",
  "Tab stopped expanding new snippets outside an old one"
)
print(
  "PASS: local snippet navigation, outside fallback and new snippet expansion"
)
