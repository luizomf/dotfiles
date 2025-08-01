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
        custom_prettier = {
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
      },
      formatters_by_ft = {
        javascript = {
          "custom_prettier",
        },
        typescript = {
          "custom_prettier",
        },
        javascriptreact = {
          "custom_prettier",
        },
        typescriptreact = {
          "custom_prettier",
        },
        vue = { "custom_prettier" },
        css = { "custom_prettier" },
        scss = {
          "custom_prettier",
        },
        less = {
          "custom_prettier",
        },
        html = {
          "custom_prettier",
        },
        json = {
          "custom_prettier",
        },
        yaml = {
          "custom_prettier",
        },
        markdown = {
          "custom_prettier",
        },
        graphql = {
          "custom_prettier",
        },
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
