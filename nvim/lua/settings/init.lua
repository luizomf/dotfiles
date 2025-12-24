local M = {}

M.setup = function()
  require("settings.utils")
  require("settings.file")
  require("settings.spell")
  require("settings.vim")
  require("settings.diagnostics")
  require("settings.redundant-whitespace").setup()
end

return M
