-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_startup_indentation.lua
-- Requires installed Lazy, nvim-treesitter and its Lua parser/indent query.
local repo = vim.fn.getcwd()
local data = vim.fn.stdpath("data")
local root = vim.fn.tempname()
vim.fn.mkdir(root, "p", 448)

local ok, err = xpcall(function()
  assert(
    vim.fn.isdirectory(data .. "/lazy/lazy.nvim") == 1,
    "Lazy must already be installed; this test must not bootstrap it"
  )
  vim.fn.writefile(
    { "root = true", "[*]", "indent_style = space", "indent_size = 4" },
    root .. "/.editorconfig"
  )
  vim.fn.writefile(
    { "if true then", "print('hello')", "end" },
    root .. "/example.lua"
  )
  -- Keep the real init sequence and Lazy loader, but exclude plugins that
  -- launch language servers, save sessions or perform unrelated work.
  local init = string.format(
    [[
vim.opt.rtp:prepend(%q .. "/lazy/lazy.nvim")
local lazy = require("lazy")
local setup = lazy.setup
lazy.setup = function()
  setup({ require("plugins.treesitter")[1] }, {
    root = %q .. "/lazy",
    lockfile = %q .. "/lazy-lock.json",
    install = { missing = false },
    checker = { enabled = false },
    change_detection = { enabled = false },
  })
end
vim.opt.rtp:prepend(%q .. "/nvim")
dofile(%q .. "/nvim/init.lua")
vim.o.swapfile = false
vim.o.updatecount = 0
]],
    data,
    data,
    root,
    repo,
    repo
  )
  vim.fn.writefile(vim.split(init, "\n"), root .. "/init.lua")
  vim.fn.writefile({
    "assert(vim.bo.shiftwidth == 4 and vim.bo.expandtab, 'CLI-opened file missed project EditorConfig')",
    "assert(vim.b.editorconfig and vim.b.editorconfig.indent_size == '4', 'EditorConfig did not run on startup')",
    "assert(vim.bo.indentexpr ~= 'GetLuaIndent()' and vim.bo.indentexpr ~= '', 'CLI-opened file missed Tree-sitter indentation')",
    "vim.cmd('silent normal! gg=G')",
    "assert(vim.fn.indent(2) == 4, 'CLI-opened file did not indent with four spaces')",
    "vim.cmd('qa!')",
  }, root .. "/check.lua")
  local command = {
    vim.v.progpath,
    "--headless",
    "-i",
    "NONE",
    "-u",
    root .. "/init.lua",
    root .. "/example.lua",
    "-c",
    "lua local ok, err = pcall(dofile, "
      .. string.format("%q", root .. "/check.lua")
      .. "); if not ok then print(err); vim.cmd('cquit 1') end",
  }
  local result = vim
    .system(command, {
      env = {
        XDG_STATE_HOME = root .. "/state",
        XDG_CACHE_HOME = root .. "/cache",
      },
      text = true,
      timeout = 10000,
    })
    :wait()
  assert(
    result.code == 0,
    "Startup indentation check failed:\n"
      .. (result.stderr or "")
      .. (result.stdout or "")
  )
end, debug.traceback)
vim.fn.delete(root, "rf")
assert(ok, err)
print(
  "PASS: CLI-opened Lua file receives EditorConfig and Tree-sitter indentation"
)
