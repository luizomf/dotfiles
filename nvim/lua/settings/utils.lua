local U = {}

function U.notify(msg, level, timeout)
  vim.notify(msg, level or vim.log.levels.INFO, { title = "nvim", timeout = timeout or 2000 })
end

return U
