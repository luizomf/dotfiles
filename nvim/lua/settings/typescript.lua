local M = {}
-- Capture upstream before applying overrides, including on repeated setup.
local root_dir = vim.lsp.config.ts_ls.root_dir

-- Resolve once per workspace decision, never from a global compiler on PATH.
local function select_server(root)
  local dirs = { root }
  for parent in vim.fs.parents(root) do
    dirs[#dirs + 1] = parent
  end
  for _, dir in ipairs(dirs) do
    local package_path = dir .. "/node_modules/typescript/package.json"
    if vim.uv.fs_stat(package_path) then
      local ok, package = pcall(function()
        return vim.json.decode(
          table.concat(vim.fn.readfile(package_path), "\n")
        )
      end)
      local version = ok
        and type(package) == "table"
        and type(package.version) == "string"
        and vim.version.parse(package.version)
      if not version then
        error("Cannot determine the TypeScript version from " .. package_path)
      end
      if version.major >= 7 then
        return "tsc", dir .. "/node_modules/.bin/tsc"
      end
      return "ts_ls"
    end
  end
  return "ts_ls"
end

function M.servers()
  -- Keep upstream workspace/monorepo discovery and Deno exclusions for both.
  local function root_for(name)
    return function(bufnr, on_dir)
      root_dir(bufnr, function(root)
        if select_server(root) == name then
          on_dir(root)
        end
      end)
    end
  end
  return {
    ts_ls = { root_dir = root_for("ts_ls") },
    tsc = {
      root_dir = root_for("tsc"),
      cmd = function(dispatchers, config)
        local name, command = select_server(config.root_dir)
        if name ~= "tsc" then
          error(
            "TypeScript changed before native LSP startup; reopen the project"
          )
        end
        return vim.lsp.rpc.start({ command, "--lsp", "--stdio" }, dispatchers, {
          cwd = config.cmd_cwd,
          env = config.cmd_env,
          detached = config.detached,
        })
      end,
    },
  }
end

return M
