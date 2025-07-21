-- lua/settings/diagnostics.lua

vim.diagnostic.config({
  virtual_text = {
    prefix = "●", -- ou "■", "▎", "● ", etc
    spacing = 2,
    source = "if_many", -- mostra o nome do LSP se tiver mais de um
  },
  signs = true,
  underline = true,
  update_in_insert = false,
  severity_sort = true,
  float = {
    border = "rounded",
    source = true,
  },
})
