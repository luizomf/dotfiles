local function config_fallback(formatter, flag, filename)
  return function(self, ctx)
    local builtin = require("conform.formatters." .. formatter)
    local editorconfig = vim.fs.find(".editorconfig", {
      path = ctx.dirname,
      upward = true,
    })[1]
    if builtin.cwd(self, ctx) or editorconfig then
      return {}
    end
    return { flag, vim.fn.stdpath("config") .. "/config_files/" .. filename }
  end
end

local function ruff_command(self, ctx)
  -- Use the project's locked formatter when available, without changing PATH.
  return require("conform.util").find_executable({ ".venv/bin/ruff" }, "ruff")(
    self,
    ctx
  )
end

return {
  {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    cmd = { "ConformInfo" },
    opts = {
      formatters = {
        taplo = {
          cwd = function(self, ctx)
            return require("conform.util").root_file({
              ".taplo.toml",
              "taplo.toml",
            })(self, ctx) or ctx.dirname
          end,
        },
        ruff_fix = { command = ruff_command },
        ruff_format = { command = ruff_command },
        ruff_organize_imports = { command = ruff_command },
        stylua = {
          prepend_args = config_fallback(
            "stylua",
            "--config-path",
            "stylua.toml"
          ),
        },
        prettier = {
          prepend_args = config_fallback(
            "prettier",
            "--config",
            "prettierrc.json"
          ),
          append_args = { "--log-level", "silent" },
        },
      },
      formatters_by_ft = {
        javascript = { "prettier" },
        typescript = { "prettier" },
        javascriptreact = { "prettier" },
        typescriptreact = { "prettier" },
        vue = { "prettier" },
        css = { "prettier" },
        scss = { "prettier" },
        less = { "prettier" },
        html = { "prettier" },
        json = { "prettier" },
        yaml = { "prettier" },
        markdown = { "prettier" },
        graphql = { "prettier" },
        astro = { "prettier" },

        lua = { "stylua" },
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
