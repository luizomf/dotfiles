-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_editing_highlights.lua
vim.opt.rtp:append(vim.fn.getcwd() .. "/nvim")
require("settings.spell")
require("settings.redundant-whitespace").setup()

local function has_whitespace_match(win)
  for _, match in ipairs(vim.fn.getmatches(win)) do
    if match.group == "RedundantWhitespace" then
      return true
    end
  end
  return false
end

local ns = vim.api.nvim_create_namespace("editing-highlight-check")
vim.api.nvim_buf_set_lines(0, 0, -1, false, { "zzzxqvvv  " })
vim.diagnostic.set(ns, 0, {
  { lnum = 0, col = 0, message = "zzzxqvvv\n  \nMore details" },
})
local _, float = vim.diagnostic.open_float({ scope = "line" })
assert(float, "Expected a diagnostic popup")
assert(
  not has_whitespace_match(float),
  "Diagnostic popup has whitespace markers"
)
assert(not vim.wo[float].spell, "Diagnostic popup has spelling enabled")
vim.api.nvim_win_close(float, true)

local text_buf = vim.api.nvim_get_current_buf()
local readonly_buf = vim.api.nvim_create_buf(true, false)
vim.bo[readonly_buf].readonly = true
vim.api.nvim_set_current_buf(readonly_buf)
assert(not vim.wo.spell, "Read-only buffer has spelling enabled")
assert(not has_whitespace_match(0), "Read-only buffer has whitespace markers")
vim.api.nvim_set_current_buf(text_buf)
assert(vim.wo.spell, "Spelling was not restored in editable text")
assert(has_whitespace_match(0), "Editable text lost whitespace markers")

vim.bo.readonly = true
assert(not vim.wo.spell, "Changing readonly did not suppress spelling")
assert(not has_whitespace_match(0), "Changing readonly left whitespace markers")
vim.bo.readonly = false
assert(vim.wo.spell, "Making the buffer writable did not restore spelling")
assert(
  has_whitespace_match(0),
  "Making the buffer writable did not restore markers"
)

for _, option in ipairs({ "modifiable", "buftype", "previewwindow" }) do
  if option == "modifiable" then
    vim.bo.modifiable = false
  elseif option == "buftype" then
    vim.bo.buftype = "nofile"
  else
    vim.wo.previewwindow = true
  end
  assert(not vim.wo.spell, option .. " left spelling enabled")
  assert(not has_whitespace_match(0), option .. " left whitespace markers")
  if option == "modifiable" then
    vim.bo.modifiable = true
  elseif option == "buftype" then
    vim.bo.buftype = ""
  else
    vim.wo.previewwindow = false
  end
  assert(
    vim.wo.spell and has_whitespace_match(0),
    option .. " did not restore hints"
  )
end

-- A buffer option affects every window showing that buffer.
local original_win = vim.api.nvim_get_current_win()
vim.cmd("vsplit")
local split_win = vim.api.nvim_get_current_win()
vim.bo.readonly = true
for _, win in ipairs({ original_win, split_win }) do
  assert(not vim.wo[win].spell and not has_whitespace_match(win))
end
vim.bo.readonly = false
for _, win in ipairs({ original_win, split_win }) do
  assert(vim.wo[win].spell and has_whitespace_match(win))
end
vim.api.nvim_win_close(split_win, true)

-- Do not turn spelling back on if the user disabled it before visiting a UI buffer.
vim.wo.spell = false
vim.api.nvim_set_current_buf(readonly_buf)
vim.api.nvim_set_current_buf(text_buf)
assert(not vim.wo.spell, "Manual nospell was lost after a buffer switch")
assert(has_whitespace_match(0), "Editable text lost whitespace markers")

print(
  "PASS: diagnostic popup, readonly/nonmodifiable/special/preview buffers, split windows and manual nospell"
)
