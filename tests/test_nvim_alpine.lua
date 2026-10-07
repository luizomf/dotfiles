-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_alpine.lua
-- Mock platform/filesystem and plugin boundaries; no downloads or tool execution.
vim.opt.rtp:append(vim.fn.getcwd() .. "/nvim")
local uname = vim.uv.os_uname
local readable = vim.fn.filereadable
local function platform(system, alpine)
  vim.uv.os_uname = function()
    return { sysname = system }
  end
  vim.fn.filereadable = function(path)
    if path == "/etc/alpine-release" then
      return alpine and 1 or 0
    end
    return readable(path)
  end
  package.loaded["settings.tooling"] = nil
  package.loaded["plugins.mason"] = nil
  package.loaded["plugins.lsp"] = nil
end

platform("Linux", true)
assert(
  require("plugins.mason").opts.PATH == "append",
  "Alpine must prefer native PATH tools over Mason binaries"
)
for _, system in ipairs({ "Darwin", "Linux" }) do
  platform(system, false)
  assert(
    vim.deep_equal(require("plugins.mason").opts, {}),
    "Existing platforms must retain Mason defaults"
  )
end
platform("Darwin", true)
assert(vim.deep_equal(require("plugins.mason").opts, {}))
-- Reuse installed LSP defaults without starting servers (same boundary as the LSP tests).
vim.opt.rtp:append(vim.fn.stdpath("data") .. "/lazy/nvim-lspconfig")
local npm_servers = {
  "ts_ls",
  "pyright",
  "tailwindcss",
  "bashls",
  "emmet_ls",
  "eslint",
  "html",
  "cssls",
  "astro",
}
local all_servers = {
  "ruff",
  "taplo",
  "lua_ls",
  "ts_ls",
  "pyright",
  "tailwindcss",
  "rust_analyzer",
  "bashls",
  "emmet_ls",
  "eslint",
  "html",
  "cssls",
  "astro",
}
local ensured, enabled
package.loaded["mason-lspconfig"] = {
  setup = function(opts)
    ensured = opts.ensure_installed
    assert(opts.automatic_enable == false)
  end,
}
package.loaded["cmp_nvim_lsp"] = {
  default_capabilities = function()
    return {}
  end,
}
vim.lsp.enable = function(name)
  enabled[name] = true
end
local interactive = true
vim.api.nvim_list_uis = function()
  return interactive and { {} } or {}
end
for _, alpine in ipairs({ true, false }) do
  platform("Linux", alpine)
  enabled = {}
  require("plugins.lsp")[1].config()
  assert(
    vim.deep_equal(ensured, alpine and npm_servers or all_servers),
    "Interactive Mason must omit only Alpine native LSPs: "
      .. vim.inspect(ensured)
  )
  for _, name in ipairs(all_servers) do
    assert(enabled[name], "Native and Mason LSPs must remain enabled: " .. name)
  end
  interactive = false
  require("plugins.lsp")[1].config()
  assert(#ensured == 0, "Headless startup must not install LSPs")
  interactive = true
end
local installed, requested, synced
package.loaded["mason-registry"] = {
  refresh = function()
    return true
  end,
  is_installed = function(name)
    return installed[name] == true
  end,
}
package.loaded["mason-lspconfig.mappings"] = {
  get_mason_map = function()
    local mapping = {}
    for _, name in ipairs(all_servers) do
      mapping[name] = name
    end
    return { lspconfig_to_package = mapping }
  end,
}
package.loaded["nvim-treesitter"] = {
  install = function()
    return {
      wait = function()
        return true
      end,
    }
  end,
  update = function()
    return {
      wait = function()
        synced = true
        return true
      end,
    }
  end,
}
vim.treesitter.language.add = function()
  return true
end
vim.fn.executable = function()
  return 1
end
vim.fn.exepath = function(name)
  return "/usr/bin/" .. name
end
vim.cmd = function(command)
  assert(command:match("^MasonInstall "), "Unexpected command: " .. command)
  for name in command:sub(#"MasonInstall " + 1):gmatch("%S+") do
    installed[name] = true
    table.insert(requested, name)
  end
end
for _, alpine in ipairs({ true, false }) do
  platform("Linux", alpine)
  installed, requested, synced = {}, {}, false
  require("settings.tooling").bootstrap()
  local expected = vim.deepcopy(alpine and npm_servers or all_servers)
  if not alpine then
    table.insert(expected, "stylua")
  end
  table.sort(expected)
  assert(
    vim.deep_equal(requested, expected),
    "Bootstrap must install only platform-appropriate Mason packages: "
      .. vim.inspect(requested)
  )
  assert(synced, "Bootstrap must still synchronize Treesitter")
end
local native_tools = {
  "ruff",
  "taplo",
  "lua-language-server",
  "rust-analyzer",
  "stylua",
  "tree-sitter",
}
local diagnostic, exit_requested, refreshed
package.loaded["mason-registry"].refresh = function()
  refreshed = true
  return true
end
vim.api.nvim_err_writeln = function(message)
  diagnostic = message
end
vim.cmd = function(command)
  assert(command == "cquit 1", "Unexpected command: " .. command)
  exit_requested = true
  error("bootstrap exited")
end
platform("Linux", true)
for _, missing in ipairs(native_tools) do
  vim.fn.executable = function(name)
    return name == missing and 0 or 1
  end
  diagnostic, exit_requested, refreshed, synced = nil, false, false, false
  local ok = pcall(require("settings.tooling").bootstrap)
  assert(
    not ok and exit_requested,
    "Bootstrap accepted missing native tool: " .. missing
  )
  assert(diagnostic:find(missing, 1, true), "Missing tool must be named")
  assert(
    diagnostic:find("apk", 1, true),
    "Diagnostic must explain native apk recovery"
  )
  assert(
    not refreshed and not synced,
    "Validation must precede installation side effects"
  )
end
-- A leftover GNU Mason binary is not a substitute for a missing native package.
vim.fn.executable = function()
  return 1
end
vim.fn.exepath = function(name)
  return vim.fn.stdpath("data") .. "/mason/bin/" .. name
end
diagnostic, exit_requested, refreshed = nil, false, false
local ok = pcall(require("settings.tooling").bootstrap)
assert(
  not ok and exit_requested,
  "Bootstrap must reject fallback Mason native tools"
)
assert(not refreshed, "Mason fallback validation must precede registry refresh")
for _, name in ipairs(native_tools) do
  assert(
    diagnostic:find(name, 1, true),
    "Diagnostic must list every unavailable native tool"
  )
end
-- No new native-tool requirements on existing platforms.
platform("Linux", false)
vim.fn.executable = function()
  error("Non-Alpine must not validate native tools")
end
require("settings.tooling").bootstrap()
assert(synced)
vim.uv.os_uname = uname
vim.fn.filereadable = readable
print(
  "PASS: Alpine PATH/Mason policy and native bootstrap validation; unchanged non-Alpine defaults"
)
