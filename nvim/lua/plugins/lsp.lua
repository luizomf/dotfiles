return {
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      -- "mason-org/mason-lspconfig.nvim",
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
      local capabilities = require("cmp_nvim_lsp").default_capabilities()

      local on_attach = function(_, bufnr)
        local map = vim.keymap.set
        local opts = { buffer = bufnr, noremap = true, silent = true }

        map("n", "gd", vim.lsp.buf.definition, opts)
        map("n", "K", vim.lsp.buf.hover, opts)
        map("n", "<leader>rn", vim.lsp.buf.rename, opts)
        map("n", "<leader>ca", vim.lsp.buf.code_action, opts)
      end

      -- require("mason-lspconfig").setup({})

      local server_opts = {
        on_attach = on_attach,
        capabilities = capabilities,
      }

      -- if server_name == "pyright" then
      --   server_opts.settings = {
      --     pyright = {
      --       disableOrganizeImports = true,
      --     },
      --     python = {
      --       analysis = {
      --         ignore = { "*" },
      --       },
      --     },
      --   }
      -- end

      require("lspconfig").pyright.setup(server_opts)
      require("lspconfig").ruff.setup(server_opts)
      require("lspconfig").ts_ls.setup(server_opts)
      require("lspconfig").lua_ls.setup(server_opts)
    end,
  },
}
