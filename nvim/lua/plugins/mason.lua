-- lua/plugins/mason.lua
return {
  "williamboman/mason.nvim",
  opts = {
    ensure_installed = {
      -- formatters
      "prettier",
      "stylua",
      "ruff",

      -- lsp
      "lua_ls",
      "ts_ls",
      "pyright",
      "ruff-lsp",
    },
  },
}
