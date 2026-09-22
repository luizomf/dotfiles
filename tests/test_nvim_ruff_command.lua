-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_ruff_command.lua
-- Inspect the real LSP configuration at its process-launch boundary; never run Ruff.
vim.opt.rtp:append(vim.fn.getcwd() .. "/nvim")
local lspconfig = vim.fn.stdpath("data") .. "/lazy/nvim-lspconfig"
assert(
  vim.fn.filereadable(lspconfig .. "/lsp/ruff.lua") == 1,
  "Installed nvim-lspconfig is required"
)
vim.opt.rtp:append(lspconfig)
vim.opt.rtp:append(vim.fn.stdpath("data") .. "/lazy/conform.nvim")
local enable = vim.lsp.enable
local start = vim.lsp.rpc.start
local mason = package.loaded["mason-lspconfig"]
local capabilities = package.loaded["cmp_nvim_lsp"]
package.loaded["mason-lspconfig"] = { setup = function() end }
package.loaded["cmp_nvim_lsp"] = {
  default_capabilities = function()
    return {}
  end,
}
vim.lsp.enable = function() end
local root = vim.fn.tempname()
local project = root .. "/project with spaces"
vim.fn.mkdir(project .. "/.venv/bin", "p", 448)
local command = project .. "/.venv/bin/ruff"
vim.fn.writefile({ "#!/bin/sh", "exit 99" }, command)
assert(vim.uv.fs_chmod(command, 448))

local ok, err = xpcall(function()
  require("plugins.lsp")[1].config()
  local selected, options, received_dispatchers
  vim.lsp.rpc.start = function(cmd, dispatchers, opts)
    selected, received_dispatchers, options = cmd, dispatchers, opts
    return {}
  end
  local cmd = vim.lsp.config.ruff.cmd
  local formatter_command =
    require("plugins.formatter")[1].opts.formatters.ruff_format.command
  local dispatchers = {}
  local function check(dir, expected)
    selected, options = nil, nil
    if type(cmd) == "function" then
      cmd(dispatchers, {
        root_dir = dir,
        cmd_cwd = root,
        cmd_env = { RUFF_TEST = "fixture" },
        detached = false,
      })
    else
      selected = cmd
    end
    assert(
      vim.deep_equal(selected, { expected, "server" }),
      "Wrong Ruff executable: " .. vim.inspect(selected)
    )
    if dir then
      assert(
        formatter_command({}, { dirname = dir }) == expected,
        "LSP and formatter executable policies disagree for the same directory"
      )
    end
    assert(
      received_dispatchers == dispatchers
        and options.cwd == root
        and options.env.RUFF_TEST == "fixture"
        and options.detached == false,
      "LSP launch options were not preserved"
    )
  end
  check(project, command)
  vim.fn.mkdir(project .. "/nested/.venv/bin", "p", 448)
  local closer = project .. "/nested/.venv/bin/ruff"
  vim.fn.writefile({ "#!/bin/sh", "exit 99" }, closer)
  assert(vim.uv.fs_chmod(closer, 384))
  check(project .. "/nested", command)
  assert(vim.uv.fs_chmod(closer, 448))
  check(project .. "/nested", closer)
  assert(vim.uv.fs_chmod(closer, 384))
  assert(vim.uv.fs_chmod(command, 384))
  check(project .. "/nested", "ruff")
  check(nil, "ruff")
  vim.fn.mkdir(root .. "/other-project", "p", 448)
  check(root .. "/other-project", "ruff")
  assert(vim.uv.fs_chmod(command, 448))
  check(project, command)
end, debug.traceback)
vim.lsp.enable = enable
vim.lsp.rpc.start = start
package.loaded["mason-lspconfig"] = mason
package.loaded["cmp_nvim_lsp"] = capabilities
vim.fn.delete(root, "rf")
assert(ok, err)
print(
  "PASS: Ruff LSP project/ancestor selection, executable checks, fallback and launch options"
)
