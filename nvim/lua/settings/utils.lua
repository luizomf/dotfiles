local U = {}

-- Notificações
function U.notify(msg, level, timeout)
  vim.notify(
    msg,
    level or vim.log.levels.INFO,
    { title = "nvim", timeout = timeout or 2000 }
  )
end

-- Atalho pra contar Notificações
vim.api.nvim_create_user_command("Notify", function(opts)
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
    ["「"] = "」",
    ["『"] = "』",
    ["【"] = "】",
    ["《"] = "》",
  }

  left = left and vim.trim(left) or ""
  right = right and vim.trim(right) or ""

  if left == "" then
    U.notify("Informe qual caractere será usado.", vim.log.levels.WARN)
    return
  end

  right = right ~= "" and right or pairs[left] or left

  local bufnr = vim.api.nvim_get_current_buf()
  local start_row, start_col = unpack(vim.api.nvim_buf_get_mark(bufnr, "<"))
  local end_row, end_col = unpack(vim.api.nvim_buf_get_mark(bufnr, ">"))

  if start_row == end_row and start_col == end_col then
    U.notify("Seleção vazia ou inválida", vim.log.levels.WARN)
    return
  end

  -- Corrige end_col se estiver fora da linha
  local end_line =
    vim.api.nvim_buf_get_lines(bufnr, end_row - 1, end_row, false)[1]
  if end_col > #end_line then
    end_col = #end_line
  end

  local lines = vim.api.nvim_buf_get_text(
    bufnr,
    start_row - 1,
    start_col,
    end_row - 1,
    end_col + 1, -- I want it to be precise with the selection
    {}
  )

  lines[1] = left .. lines[1]
  lines[#lines] = lines[#lines] .. right

  vim.api.nvim_buf_set_text(
    bufnr,
    start_row - 1,
    start_col,
    end_row - 1,
    end_col + 1, -- I want it to be precise with the selection
    lines
  )

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
