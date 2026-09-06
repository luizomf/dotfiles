require("settings")
require("keymaps")

-- Personal Theme
require("omtheme.groups").set_groups()
vim.opt.termguicolors = true

-- DARK THEME
-- Use omtheme for dark background only
vim.cmd("colorscheme omtheme")

-- -- LIGHT THEMES
-- -- For light backgrounds, use the colorscheme you like
-- vim.cmd("colorscheme peachpuff")

-- -- Remove background to use the terminal background color
-- local bg_groups = {
--   "Normal",
--   "NormalNC",
--   "SignColumn",
--   "LineNr",
--   "CursorLineNr",
--   "CursorColumn",
--   "ColorColumn",
--   "CursorLine",
--   "StatusLine",
--   "StatusLineNC",
--   "StatusLineTerm",
--   "StatusLineTermNC",
-- }
-- for _, group in ipairs(bg_groups) do
--   vim.api.nvim_set_hl(0, group, { bg = "NONE", ctermbg = "NONE" })
-- end

return {}
