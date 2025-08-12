-- nvim/lua/plugins/lsp.lua
return {
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      "mason-org/mason-lspconfig.nvim",
      "hrsh7th/cmp-nvim-lsp",
      {
        "folke/lazydev.nvim",
        ft = "lua", -- only load on lua files
        opts = {
          library = {
            -- See the configuration section for more details
            -- Load luvit types when the `vim.uv` word is found
            { path = "${3rd}/luv/library", words = { "vim%.uv" } },
          },
        },
      },
    },
    config = function()
      require("mason-lspconfig").setup({
        automatic_enable = false,
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
      })

      local capabilities = require("cmp_nvim_lsp").default_capabilities()

      local on_attach = function(_, bufnr)
        local map = vim.keymap.set
        local opts = { buffer = bufnr, noremap = true, silent = true }

        map("n", "gd", vim.lsp.buf.definition, opts)
        map("n", "K", vim.lsp.buf.hover, opts)
        map("n", "<leader>rn", vim.lsp.buf.rename, opts)
        map("n", "<leader>ca", vim.lsp.buf.code_action, opts)
      end

      require("lspconfig").pyright.setup({
        on_attach = on_attach,
        capabilities = capabilities,
      })

      require("lspconfig").ruff.setup({
        on_attach = on_attach,
        capabilities = capabilities,
      })

      require("lspconfig").ts_ls.setup({
        on_attach = on_attach,
        capabilities = capabilities,
      })

      require("lspconfig").lua_ls.setup({
        on_attach = on_attach,
        capabilities = capabilities,
      })
    end,
  },
}
