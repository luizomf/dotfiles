-- lua/plugins/mason.lua
return {
  "mason-org/mason.nvim",
  opts = {
    ensure_installed = {
      -- formatters
      "prettier",
      "stylua",
      "ruff",
      "taplo",

      -- lsp
      "lua_ls",
      "ts_ls",
      "pyright",
      "ruff-lsp",
    },
  },
}
