-- Editing hints belong to normal, writable buffers, not plugin UI or previews.
return function(win)
  win = win or vim.api.nvim_get_current_win()
  local buf = vim.api.nvim_win_get_buf(win)
  local options = vim.bo[buf]
  return options.buftype == ""
    and options.modifiable
    and not options.readonly
    and not vim.wo[win].previewwindow
end
