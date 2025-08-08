-- Configurations for the default spell checker

local spell_types = {
  "text",
  "plaintex",
  "typst",
  "gitcommit",
  "markdown",
  "lua",
  "python",
  "html",
  "javascript",
  "javascriptreact",
  "typescript",
  "typescriptreact",
  "css",
  "scss",
}

vim.api.nvim_create_autocmd({ "FileType" }, {
  pattern = spell_types,
  callback = function()
    vim.opt_local.spell = true
    vim.opt_local.spelllang = "pt_br,pt,en_us"
  end,
  desc = "Enable spellcheck for defined filetypes",
})
