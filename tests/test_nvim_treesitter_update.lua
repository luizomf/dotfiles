-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_treesitter_update.lua
-- Real Tree-sitter async tasks/commands; synthetic backend, no downloads or compilation.
vim.opt.rtp:append(vim.fn.getcwd() .. "/nvim")
local plugin = vim.fn.stdpath("data") .. "/lazy/nvim-treesitter"
vim.opt.rtp:append(plugin)
local async = require("nvim-treesitter.async")
local finished, installed = false, false
local update_result, install_result = true, true
local update_error
package.loaded["nvim-treesitter.install"] = {
  install = async.async(function()
    async.schedule()
    installed = true
    return install_result
  end),
  update = async.async(function()
    async.schedule()
    if update_error then
      error(update_error)
    end
    finished = true
    return update_result
  end),
}
package.loaded["lazy"] = { load = function() end }
vim.treesitter.language.add = function()
  return true
end
dofile(plugin .. "/plugin/nvim-treesitter.lua")
local spec = require("plugins.treesitter")[1]
local function build()
  if type(spec.build) == "string" then
    vim.cmd(spec.build:sub(2))
  else
    spec.build({ name = "nvim-treesitter" })
  end
end
build()
assert(finished, "Lazy build returned before the parser update finished")
assert(installed, "Lazy build did not wait for configured missing parsers")
update_result = false
local ok, err = pcall(build)
assert(
  not ok and tostring(err):find("update failed", 1, true),
  "Failed updates were reported as successful builds"
)
update_result = true
update_error = "synthetic async failure"
ok, err = pcall(build)
assert(
  not ok and tostring(err):find(update_error, 1, true),
  "Async task errors were swallowed"
)
update_error = nil
install_result = false
finished = false
ok, err = pcall(build)
assert(
  not ok and not finished and tostring(err):find("installation failed", 1, true),
  "Failed installation did not stop the build"
)
install_result = true

-- The installer must use the same synchronization, not just install missing files.
local tooling = require("settings.tooling")
package.loaded["mason-registry"] = {
  refresh = function()
    return true
  end,
  is_installed = function()
    return true
  end,
}
package.loaded["mason-lspconfig.mappings"] = {
  get_mason_map = function()
    local packages = {}
    for _, server in ipairs(tooling.lsp_servers) do
      packages[server] = server
    end
    return { lspconfig_to_package = packages }
  end,
}
finished, installed = false, false
tooling.bootstrap()
assert(
  finished and installed,
  "Bootstrap returned before installation and update completed"
)
local exit_requested = false
vim.cmd = function(command)
  assert(command == "cquit 1")
  exit_requested = true
end
vim.api.nvim_err_writeln = function() end
update_result = false
tooling.bootstrap()
assert(
  exit_requested,
  "Bootstrap did not request a failing exit after update failure"
)
print(
  "PASS: Lazy/bootstrap await parser installation and update, propagate failures and preserve failing installer exits"
)
