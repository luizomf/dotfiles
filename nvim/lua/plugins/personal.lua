require("settings")
require("keymaps")

-- Personal Theme
require("omtheme.groups").set_groups()
vim.opt.termguicolors = true
vim.cmd("colorscheme omtheme")

return {}
