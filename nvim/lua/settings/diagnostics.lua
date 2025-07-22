-- lua/settings/diagnostics.lua

-- vim.diagnostic.config({
--   virtual_text = {
--     prefix = "●", -- ou "■", "▎", "● ", etc
--     spacing = 2,
--     source = "if_many", -- mostra o nome do LSP se tiver mais de um
--   },
--   signs = true,
--   underline = true,
--   update_in_insert = false,
--   severity_sort = true,
--   float = {
--     border = "rounded",
--     source = true,
--   },
-- })

-- Disable virtual text, enable signs and underline
vim.diagnostic.config({
  virtual_lines = false,
  virtual_text = false,
  underline = true,
  signs = true,
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
  },
})
