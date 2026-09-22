-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_indentation.lua
-- Requires installed nvim-treesitter; never installs parsers or runs formatters.
local repo = vim.fn.getcwd()
local data = vim.fn.stdpath("data")
local root = vim.fn.tempname()
vim.fn.mkdir(root .. "/indent", "p", 448)
vim.env.XDG_STATE_HOME = root .. "/state"
vim.env.XDG_CACHE_HOME = root .. "/cache"
vim.opt.rtp =
  { root, repo .. "/nvim", data .. "/lazy/nvim-treesitter", vim.env.VIMRUNTIME }
vim.o.swapfile = false
vim.cmd("filetype plugin indent on")

local function native_indent(filetype)
  vim.fn.writefile({
    "let b:did_indent = 1",
    "setlocal indentexpr=7",
    "let b:undo_indent = 'setlocal indentexpr<'",
  }, root .. "/indent/" .. filetype .. ".vim")
end

local ok, err = xpcall(function()
  native_indent("unavailable_fixture")
  require("plugins.treesitter")[1].config()
  local buf = vim.api.nvim_create_buf(false, false)
  vim.api.nvim_set_current_buf(buf)
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "first", "second" })
  vim.bo.filetype = "unavailable_fixture"
  vim.cmd("silent normal! gg=G")
  assert(vim.fn.indent(2) == 7, "Missing parser replaced native indentation")

  native_indent("queryless_fixture")
  vim.treesitter.language.add("lua", { path = data .. "/site/parser/lua.so" })
  vim.treesitter.language.register("lua", "queryless_fixture")
  assert(
    vim.treesitter.query.get("lua", "indents") == nil,
    "Fixture unexpectedly has an indentation query"
  )
  buf = vim.api.nvim_create_buf(false, false)
  vim.api.nvim_set_current_buf(buf)
  vim.api.nvim_buf_set_lines(
    buf,
    0,
    -1,
    false,
    { "if true then", "print('hello')", "end" }
  )
  vim.bo.filetype = "queryless_fixture"
  vim.cmd("silent normal! gg=G")
  assert(vim.fn.indent(2) == 7, "Missing query replaced native indentation")

  vim.opt.rtp:prepend(data .. "/site")
  assert(
    vim.treesitter.query.get("lua", "indents"),
    "Installed Lua indentation query is required"
  )
  vim.fn.writefile(
    { "root = true", "[*]", "indent_style = space", "indent_size = 4" },
    root .. "/.editorconfig"
  )
  native_indent("supported_fixture")
  vim.treesitter.language.register("lua", "supported_fixture")
  vim.filetype.add({ extension = { fixture_lua = "supported_fixture" } })
  vim.fn.writefile(
    { "if true then", "print('hello')", "end" },
    root .. "/example.fixture_lua"
  )
  vim.cmd("runtime plugin/editorconfig.lua")
  vim.cmd("edit! " .. vim.fn.fnameescape(root .. "/example.fixture_lua"))
  assert(
    vim.bo.shiftwidth == 4 and vim.bo.expandtab,
    "Project EditorConfig was not applied"
  )
  vim.cmd("silent normal! gg=G")
  assert(
    vim.deep_equal(
      vim.api.nvim_buf_get_lines(0, 0, -1, false),
      { "if true then", "    print('hello')", "end" }
    ),
    "Supported Tree-sitter indentation did not respect project spacing"
  )
end, debug.traceback)
vim.fn.delete(root, "rf")
assert(ok, err)
print(
  "PASS: native fallback for missing parsers/queries; supported indentation respects EditorConfig"
)
