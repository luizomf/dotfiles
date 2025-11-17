return {
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      "mason-org/mason-lspconfig.nvim",
      "hrsh7th/cmp-nvim-lsp",
      {
        "folke/lazydev.nvim",
        ft = "lua",
        opts = {
          library = {
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
          "tailwindcss",
          "rust_analyzer",
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

      vim.lsp.config("rust_analyzer", {
        on_attach = on_attach,
        capabilities = capabilities,
      })
      vim.lsp.enable("rust_analyzer")

      vim.lsp.config("pyright", {
        on_attach = on_attach,
        capabilities = capabilities,
      })
      vim.lsp.enable("pyright")

      vim.lsp.config("ruff", {
        on_attach = on_attach,
        capabilities = capabilities,
      })
      vim.lsp.enable("ruff")

      vim.lsp.config("ts_ls", {
        on_attach = on_attach,
        capabilities = capabilities,
      })
      vim.lsp.enable("ts_ls")

      vim.lsp.config("lua_ls", {
        on_attach = on_attach,
        capabilities = capabilities,
      })
      vim.lsp.enable("lua_ls")

      vim.lsp.config("tailwindcss", {
        on_attach = on_attach,
        capabilities = capabilities,
        settings = {
          tailwindCSS = {
            experimental = {
              classRegex = {
                { "cva\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]" },
                { "cn\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]" },
                { "clsx\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]" },
                { "twMerge\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]" },
              },
            },
          },
        },
      })
      vim.lsp.enable("tailwindcss")
    end,
  },
}
