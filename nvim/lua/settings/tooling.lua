local M = {}

M.lsp_servers = {
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

M.mason_tools = {
  "stylua",
}

M.treesitter_parsers = {
  "c",
  "cpp",
  "go",
  "rust",
  "just",
  "cmake",
  "bash",
  "tmux",
  "zsh",
  "ssh_config",
  "dockerfile",
  "editorconfig",
  "lua",
  "vim",
  "vimdoc",
  "html",
  "xml",
  "css",
  "scss",
  "styled",
  "javascript",
  "typescript",
  "tsx",
  "jsx",
  "json",
  "yaml",
  "toml",
  "htmldjango",
  "passwd",
  "terraform",
  "markdown",
  "markdown_inline",
  "python",
  "astro",
}

local function abort(message)
  vim.api.nvim_err_writeln(message)
  vim.cmd("cquit 1")
end

local function mason_packages()
  local mapping = require("mason-lspconfig.mappings").get_mason_map()
  local packages = {}
  local seen = {}

  for _, server in ipairs(M.lsp_servers) do
    local package = mapping.lspconfig_to_package[server]
    if not package then
      abort("No Mason package mapping found for LSP server: " .. server)
    end
    if not seen[package] then
      seen[package] = true
      table.insert(packages, package)
    end
  end

  for _, package in ipairs(M.mason_tools) do
    if not seen[package] then
      seen[package] = true
      table.insert(packages, package)
    end
  end

  table.sort(packages)
  return packages
end

local function install_mason_packages()
  local registry = require("mason-registry")
  local refreshed = registry.refresh()
  if not refreshed then
    abort("Mason registry refresh failed.")
  end

  local packages = mason_packages()
  local missing = {}
  for _, package in ipairs(packages) do
    if not registry.is_installed(package) then
      table.insert(missing, package)
    end
  end

  local command_ok, command_error = true, nil
  if #missing > 0 then
    command_ok, command_error =
      pcall(vim.cmd, "MasonInstall " .. table.concat(missing, " "))
  end

  local still_missing = {}
  for _, package in ipairs(packages) do
    if not registry.is_installed(package) then
      table.insert(still_missing, package)
    end
  end
  if #still_missing > 0 then
    local detail = command_ok and "" or " (" .. tostring(command_error) .. ")"
    abort(
      "Missing Mason packages: " .. table.concat(still_missing, ", ") .. detail
    )
  end
end

function M.sync_treesitter()
  local task = require("nvim-treesitter").install(M.treesitter_parsers, {
    summary = true,
  })
  local completed = task:wait(600000)
  if not completed then
    error("Treesitter parser installation failed; inspect :TSLog")
  end
  local updated =
    require("nvim-treesitter").update(nil, { summary = true }):wait(600000)
  if not updated then
    error("Treesitter parser update failed; inspect :TSLog")
  end

  local missing = {}
  for _, parser in ipairs(M.treesitter_parsers) do
    if not pcall(vim.treesitter.language.add, parser) then
      table.insert(missing, parser)
    end
  end
  if #missing > 0 then
    error(
      "Missing or unloadable Treesitter parsers: "
        .. table.concat(missing, ", ")
    )
  end
end

function M.bootstrap()
  install_mason_packages()
  local ok, err = pcall(M.sync_treesitter)
  if not ok then
    abort(tostring(err))
  end
end

return M
