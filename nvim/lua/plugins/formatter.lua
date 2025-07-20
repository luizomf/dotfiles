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
      },
      formatters_by_ft = {
        javascript = {
          "prettier",
        },
        typescript = {
          "prettier",
        },
        javascriptreact = {
          "prettier",
        },
        typescriptreact = {
          "prettier",
        },
        vue = { "prettier" },
        css = { "prettier" },
        scss = {
          "prettier",
        },
        less = {
          "prettier",
        },
        html = {
          "prettier",
        },
        json = {
          "prettier",
        },
        yaml = {
          "prettier",
        },
        markdown = {
          "prettier",
        },
        graphql = {
          "prettier",
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
