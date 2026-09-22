-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_typescript.lua
-- Real LSP configurations/root discovery; intercept process launch, never run a server.
vim.opt.rtp:append(vim.fn.getcwd() .. "/nvim")
vim.opt.rtp:append(vim.fn.stdpath("data") .. "/lazy/nvim-lspconfig")
local enabled = {}
vim.lsp.enable = function(name)
  enabled[name] = true
end
package.loaded["mason-lspconfig"] = { setup = function() end }
package.loaded["cmp_nvim_lsp"] = {
  default_capabilities = function()
    return {}
  end,
}
local root = vim.fn.tempname()
vim.fn.mkdir(root, "p", 448)
root = assert(vim.uv.fs_realpath(root))
local function project(name, version)
  local dir = root .. "/" .. name
  vim.fn.mkdir(dir .. "/node_modules/typescript", "p", 448)
  vim.fn.writefile({ "{}" }, dir .. "/package-lock.json")
  if version then
    vim.fn.writefile(
      { vim.json.encode({ name = "typescript", version = version }) },
      dir .. "/node_modules/typescript/package.json"
    )
  end
  return dir
end
local ok, err = xpcall(function()
  require("plugins.lsp")[1].config()
  local function check(dir, expected, binary_root)
    local buf = vim.api.nvim_create_buf(false, false)
    vim.api.nvim_buf_set_name(buf, dir .. "/example.ts")
    local attached = {}
    for _, name in ipairs({ "ts_ls", "tsc" }) do
      if enabled[name] then
        vim.lsp.config[name].root_dir(buf, function(path)
          attached[name] = path
        end)
      end
    end
    assert(
      vim.deep_equal(attached, expected and { [expected] = dir } or {}),
      "Wrong TypeScript server selection: " .. vim.inspect(attached)
    )
    if expected then
      local command
      vim.lsp.rpc.start = function(args)
        command = args
        return {}
      end
      vim.lsp.config[expected].cmd({}, { root_dir = dir })
      local wanted = expected == "tsc"
          and {
            (binary_root or dir) .. "/node_modules/.bin/tsc",
            "--lsp",
            "--stdio",
          }
        or { "typescript-language-server", "--stdio" }
      assert(
        vim.deep_equal(command, wanted),
        "Wrong TypeScript executable: " .. vim.inspect(command)
      )
    end
    vim.api.nvim_buf_delete(buf, { force = true })
  end
  local dir = project("native project", "7.0.2")
  check(dir, "tsc")
  check(project("legacy", "6.0.3"), "ts_ls")
  check(project("without-typescript"), "ts_ls")
  local nested = project("native project/nested")
  check(nested, "tsc", dir)
  project("native project/nested", "6.0.3")
  check(nested, "ts_ls")
  check(dir, "tsc")
  local deno = dir .. "/deno"
  vim.fn.mkdir(deno, "p", 448)
  vim.fn.writefile({ "{}" }, deno .. "/deno.json")
  check(deno, nil)
  require("plugins.lsp")[1].config()
  check(dir, "tsc")
end, debug.traceback)
vim.fn.delete(root, "rf")
assert(ok, err)
print(
  "PASS: exclusive TS 7/legacy routing, executable selection, ancestor dependencies and Deno exclusion"
)
