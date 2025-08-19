vim.diagnostic.config({
  virtual_lines = false,
  virtual_text = false,
  underline = true,
  signs = true,
  severity_sort = true,
  float = {
    border = "single",
    format = function(diagnostic)
      return string.format(
        "%s (%s) [%s]",
        diagnostic.message,
        diagnostic.source,
        diagnostic.code or diagnostic.user_data.lsp.code
      )
    end,
    -- max_width = math.floor(vim.o.columns * 0.95),
    -- max_height = math.floor(vim.o.lines * 0.3),
  },
})
