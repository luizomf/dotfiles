-- lua/plugins/mason.lua
return {
  "mason-org/mason.nvim",
  opts = require("settings.tooling").is_alpine and { PATH = "append" } or {},
}
