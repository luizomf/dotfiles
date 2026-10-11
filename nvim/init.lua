vim.g.mapleader = " "

require("settings.lazy_bootstrap")()

-- Apply core settings before plugins are imported or configured.
require("settings").setup()
require("keymaps")
require("settings.theme")
require("lazy").setup("plugins")
