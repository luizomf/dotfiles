local U = {}

-- Notificações
function U.notify(msg, level, timeout)
  vim.notify(msg, level or vim.log.levels.INFO, { title = "nvim", timeout = timeout or 2000 })
end

-- Atalho pra contar Notificações
vim.api.nvim_create_user_command("Notify", function(opts)
  -- print(vim.inspect(opts.fargs))

  local msg = opts.fargs[1] or "NO MESSAGE"
  local level = opts.fargs[2] or vim.log.levels.INFO
  local timeout = tonumber(opts.fargs[3]) or 2000

  U.notify(msg, level, timeout)
end, {
  nargs = "*",
})

-- Conta palavras no buffer atual
function U.count_words()
  local buf = vim.api.nvim_get_current_buf()
  local lines = vim.api.nvim_buf_get_lines(buf, 0, -1, false)
  local content = table.concat(lines, " ")
  local _, count = content:gsub("%S+", "")
  U.notify("Palavras: " .. count)
end

-- Atalho pra contar palavras
vim.api.nvim_create_user_command("CountWords", function()
  U.count_words()
end, {})

return U
