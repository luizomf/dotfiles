-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_wrap.lua
vim.opt.rtp:append(vim.fn.getcwd() .. "/nvim")
vim.g.mapleader = " "
require("keymaps")

local function check_wrap(name, lines, keys, expected)
  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_set_current_buf(buf)
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
  vim.api.nvim_feedkeys(
    vim.api.nvim_replace_termcodes(keys, true, false, true),
    "xt",
    false
  )
  local actual = vim.api.nvim_buf_get_lines(buf, 0, -1, false)
  assert(
    vim.deep_equal(actual, expected),
    name
      .. ": expected "
      .. vim.inspect(expected)
      .. ", got "
      .. vim.inspect(actual)
  )
  vim.api.nvim_buf_delete(buf, { force = true })
end

check_wrap("single character", { "abc" }, "gg0v<Space>wp", { "(a)bc" })
check_wrap(
  "selection through end of line",
  { "abc" },
  "gg0v$<Space>wp",
  { "(abc)" }
)
check_wrap(
  "single accented character",
  { "ábc" },
  "gg0v<Space>wp",
  { "(á)bc" }
)
check_wrap("empty line", { "" }, "gg0v<Space>wp", { "()" })
check_wrap(
  "linewise selection",
  { "one", "two" },
  "ggVj<Space>wp",
  { "(one", "two)" }
)
check_wrap(
  "multiline selection",
  { "one", "two" },
  "gg0vj$<Space>wq",
  { "'one", "two'" }
)
check_wrap(
  "command with custom delimiters",
  { "abc" },
  "gg0v$:<C-u>WrapIn << >><CR>",
  { "<<abc>>" }
)
check_wrap("no previous selection", { "abc" }, ":WrapIn (<CR>", { "abc" })

print("PASS: 8 wrapping cases through visual mappings and WrapIn")
