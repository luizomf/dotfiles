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
  local pairs = {
    ["("] = ")",
    ["["] = "]",
    ["{"] = "}",
    ["<"] = ">",
    ["'"] = "'",
    ['"'] = '"',
    ["`"] = "`",
    ["«"] = "»",
    ["“"] = "”",
    ["‘"] = "’",
    ["‹"] = "›",
  }

  -- Esse é um teste
  -- ainda não sei
  -- escrever testes em LUA
  -- Testando testando testando...

  if not left or left == "" then
    U.notify("Informe qual caractere será usado.", vim.log.levels.WARN)
    return
  end

  right = right or pairs[left] or left

  local bufnr = vim.api.nvim_get_current_buf()
  local start_pos = vim.api.nvim_buf_get_mark(bufnr, "<")
  local end_pos = vim.api.nvim_buf_get_mark(bufnr, ">")

  if start_pos[1] == end_pos[1] and start_pos[2] == end_pos[2] then
    U.notify("Seleção vazia ou inválida", vim.log.levels.WARN)
    return
  end

  local text = vim.api.nvim_buf_get_text(bufnr, start_pos[1] - 1, start_pos[2], end_pos[1] - 1, end_pos[2], {})
  local joined = table.concat(text, "\n")
  local wrapped = left .. joined .. right

  vim.api.nvim_buf_set_text(bufnr, start_pos[1] - 1, start_pos[2], end_pos[1] - 1, end_pos[2], { wrapped })

  U.notify("Texto envolvido com: " .. left .. right)
end

vim.api.nvim_create_user_command("WrapIn", function(opts)
  local left = opts.fargs[1]
  local right = opts.fargs[2]
  U.wrap_in_chars(left, right)
end, {
  nargs = "*",
  range = true,
  desc = "Envolve a seleção visual com os caracteres informados",
})

return U
