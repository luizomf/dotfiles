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

function U.wrap_in_chars(left, right)
  left = left or "("
  right = right or ")"

  -- Pega início e fim da seleção visual
  local start_pos = vim.fn.getpos("'<")
  local end_pos = vim.fn.getpos("'>")

  local start_line = start_pos[2]
  local start_col = start_pos[3]
  local end_line = end_pos[2]
  local end_col = end_pos[3]

  -- Corrige ordem se o usuário selecionou ao contrário
  if start_line > end_line or (start_line == end_line and start_col > end_col) then
    start_line, end_line = end_line, start_line
    start_col, end_col = end_col, start_col
  end

  -- Pegamos a linha original
  local line = vim.api.nvim_buf_get_lines(0, start_line - 1, start_line, false)[1]

  -- Pega o trecho selecionado
  local selected = string.sub(line, start_col, end_col)

  -- Monta novo conteúdo com o wrap
  local wrapped = string.sub(line, 1, start_col - 1) .. left .. selected .. right .. string.sub(line, end_col + 1)

  -- Substitui linha no buffer
  vim.api.nvim_buf_set_lines(0, start_line - 1, start_line, false, { wrapped })

  -- Move o cursor pro final da seleção
  vim.api.nvim_win_set_cursor(0, { start_line, start_col + #selected + 1 })

  U.notify("Texto envolvido com: " .. left .. " " .. right)
end

vim.api.nvim_create_user_command("WrapIn", function(opts)
  local left = opts.fargs[1] or "("
  local right = opts.fargs[2] or ")"
  U.wrap_in_chars(left, right)
end, {
  nargs = "*",
  range = true,
  desc = "Envolve a seleção visual com os caracteres informados",
})

return U
