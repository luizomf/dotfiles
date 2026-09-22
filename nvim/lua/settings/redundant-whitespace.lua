local M = {}
local is_editable = require("settings.editable-window")

local group =
  vim.api.nvim_create_augroup("RedundantWhitespaceHL", { clear = true })

local function set_hl()
  -- Let the colorscheme choose the style; provide a fallback for other themes.
  vim.api.nvim_set_hl(0, "RedundantWhitespace", {
    default = true,
    underline = true,
  })
end

local function add()
  if vim.w.redundant_whitespace_match then
    return
  end
  vim.w.redundant_whitespace_match =
    vim.fn.matchadd("RedundantWhitespace", [[\s\+$\| \+\ze\t]], 10)
end

local function remove()
  if vim.w.redundant_whitespace_match then
    pcall(vim.fn.matchdelete, vim.w.redundant_whitespace_match)
    vim.w.redundant_whitespace_match = nil
  end
end

local function update()
  if is_editable() then
    add()
  else
    remove()
  end
end

function M.setup()
  set_hl()
  update()

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

  vim.api.nvim_create_autocmd({ "BufWinLeave", "WinLeave" }, {
    group = group,
    callback = remove,
  })

  vim.api.nvim_create_autocmd("ColorScheme", {
    group = group,
    callback = function()
      vim.schedule(set_hl)
    end,
  })
end

return M
