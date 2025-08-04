-- lua/plugins/mason.lua
return {
  "mason-org/mason.nvim",
  opts = {
    ensure_installed = {
      -- formatters
      -- "prettier", -- install manually with 'npm i -g prettier'
      -- "stylua", -- install manually with ':MasonInstall stylua'

      -- LSPs
      "ruff",
      "taplo",
      "lua_ls",
      "ts_ls",
      "pyright",
    },
  },
}
