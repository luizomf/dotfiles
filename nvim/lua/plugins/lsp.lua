local tooling = require("settings.tooling")

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
        ensure_installed = #vim.api.nvim_list_uis() > 0 and tooling.lsp_servers
          or {},
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

      local function enable_server(name, options)
        vim.lsp.config(
          name,
          vim.tbl_extend("force", {
            on_attach = on_attach,
            capabilities = capabilities,
          }, options or {})
        )
        vim.lsp.enable(name)
      end

      enable_server("eslint")
      enable_server("astro")
      enable_server("html")
      enable_server("cssls")

      enable_server("emmet_ls", {
        filetypes = {
          "html",
          "css",
          "scss",
          "javascriptreact",
          "typescriptreact",
        },
      })

      enable_server("bashls")
      enable_server("rust_analyzer")
      enable_server("pyright")
      enable_server("ruff", {
        cmd = function(dispatchers, config)
          local command = "ruff"
          if config.root_dir then
            for _, venv in
              ipairs(vim.fs.find(".venv", {
                path = config.root_dir,
                upward = true,
                limit = math.huge,
              }))
            do
              local candidate = venv .. "/bin/ruff"
              if vim.fn.executable(candidate) == 1 then
                command = candidate
                break
              end
            end
          end
          return vim.lsp.rpc.start({ command, "server" }, dispatchers, {
            cwd = config.cmd_cwd,
            env = config.cmd_env,
            detached = config.detached,
          })
        end,
      })
      enable_server("ts_ls")
      enable_server("lua_ls")

      enable_server("tailwindcss", {
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
    end,
  },
}
