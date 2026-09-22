-- Enable spelling even for temporary files without a detected filetype.
-- Syntax and Tree-sitter still decide which regions of code are checked.
vim.opt.spelllang = { "pt_br", "pt", "en_us", "en" }
vim.opt.spell = true

local is_editable = require("settings.editable-window")
local group = vim.api.nvim_create_augroup("EditingSpell", { clear = true })

local function update()
  if not is_editable() then
    if vim.w.spell_before_readonly == nil then
      vim.w.spell_before_readonly = vim.wo.spell
    end
    vim.wo.spell = false
  elseif vim.w.spell_before_readonly ~= nil then
    vim.wo.spell = vim.w.spell_before_readonly
    vim.w.spell_before_readonly = nil
  end
end

vim.api.nvim_create_autocmd(
  { "BufWinEnter", "WinEnter", "FileType", "VimEnter" },
  {
    group = group,
    callback = update,
  }
)

vim.api.nvim_create_autocmd("OptionSet", {
  group = group,
  pattern = { "buftype", "modifiable", "readonly", "previewwindow" },
  callback = function()
    for _, win in ipairs(vim.api.nvim_list_wins()) do
      vim.api.nvim_win_call(win, update)
    end
  end,
})

update()
