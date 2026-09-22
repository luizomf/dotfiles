-- Enable spelling even for temporary files without a detected filetype.
-- Syntax and Tree-sitter still decide which regions of code are checked.
vim.opt.spelllang = { "pt_br", "pt", "en_us", "en" }
vim.opt.spell = true

local function set_spell_highlight()
  vim.api.nvim_set_hl(0, "SpellBad", {
    sp = "gray",
    underdashed = true,
  })
end

set_spell_highlight()
vim.api.nvim_create_autocmd("ColorScheme", {
  callback = set_spell_highlight,
  desc = "Preserve the spellcheck underline after colorscheme changes",
})
