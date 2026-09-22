vim.diagnostic.config({
  virtual_lines = false,
  virtual_text = false,
  underline = true,
  signs = true,
  severity_sort = true,
  float = {
    border = "single",
    -- The formatter includes the code, including the legacy LSP fallback.
    suffix = "",
    format = function(diagnostic)
      local code = diagnostic.code
        or vim.tbl_get(diagnostic, "user_data", "lsp", "code")
      local message = diagnostic.message

      if diagnostic.source then
        message = string.format("%s (%s)", message, diagnostic.source)
      end
      if code ~= nil then
        message = string.format("%s [%s]", message, code)
      end

      return message
    end,
    -- max_width = math.floor(vim.o.columns * 0.95),
    -- max_height = math.floor(vim.o.lines * 0.3),
  },
})
