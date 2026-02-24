-- lua/plugins/formatter.lua
return {
  {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    cmd = { "ConformInfo" },
    opts = {
      formatters = {
        custom_stylua = {
          command = "stylua",
          args = {
            "--respect-ignores",
            "--stdin-filepath",
            "$FILENAME",
            "--config-path",
            os.getenv("HOME") .. "/dotfiles/nvim/config_files/stylua.toml",
            "-",
          },
        },
        global_prettier = {
          command = "prettier",
          args = {
            "--stdin-filepath",
            "$FILENAME",
            "--config",
            os.getenv("HOME") .. "/dotfiles/nvim/config_files/prettierrc.json",
            "--log-level",
            "silent",
          },
        },
        local_prettier = {
          command = "prettier",
          args = {
            "--stdin-filepath",
            "$FILENAME",
            "--config",
            ".prettierrc.json",
            "--log-level",
            "silent",
          },
        },
      },
      formatters_by_ft = {
        javascript = {
          "global_prettier",
        },
        typescript = {
          "global_prettier",
        },
        javascriptreact = {
          "global_prettier",
        },
        typescriptreact = {
          "global_prettier",
        },
        vue = { "global_prettier" },
        css = { "global_prettier" },
        scss = {
          "global_prettier",
        },
        less = {
          "global_prettier",
        },
        html = {
          "global_prettier",
        },
        json = {
          "global_prettier",
        },
        yaml = {
          "global_prettier",
        },
        markdown = {
          "global_prettier",
        },
        graphql = {
          "global_prettier",
        },
        astro = { "local_prettier" },

        lua = {
          "custom_stylua",
        },
        python = {
          -- To fix auto-fixable lint errors.
          "ruff_fix",
          -- To run the Ruff formatter.
          "ruff_format",
          -- To organize the imports.
          "ruff_organize_imports",
        },
        toml = { "taplo" },
      },
      format_on_save = {
        timeout_ms = 500,
        lsp_fallback = "fallback",
      },
      log_level = vim.log.levels.ERROR,
      notify_on_error = true,
      notify_no_formatters = true,
      inherit = false,
    },
  },
}
