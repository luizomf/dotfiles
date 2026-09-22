-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_lsp_formatting.lua
-- Requires installed Conform. The LSP server runs in-process; no server/tool is launched.
local repo = vim.fn.getcwd()
local data = vim.fn.stdpath("data")
local root = vim.fn.tempname()
vim.fn.mkdir(root, "p", 448)
vim.env.XDG_STATE_HOME = root .. "/state"
vim.env.XDG_CACHE_HOME = root .. "/cache"
vim.opt.rtp:append(repo .. "/nvim")
vim.opt.rtp:append(data .. "/lazy/conform.nvim")
vim.g.mapleader = " "
require("keymaps")

local client_id
local function server(dispatchers)
  local closing = false
  local request_id = 0
  local function stop()
    if not closing then
      closing = true
      dispatchers.on_exit(0, 0)
    end
  end
  return {
    request = function(method, _, callback)
      request_id = request_id + 1
      local result
      if method == "initialize" then
        result = {
          capabilities = {
            documentFormattingProvider = true,
            textDocumentSync = 1,
          },
        }
      elseif method == "textDocument/formatting" then
        result = {
          {
            range = {
              start = { line = 0, character = 0 },
              ["end"] = { line = 1, character = 0 },
            },
            newText = "formatted by LSP\n",
          },
        }
      end
      vim.schedule(function()
        callback(nil, result)
      end)
      return true, request_id
    end,
    notify = function(method)
      if method == "exit" then
        stop()
      end
      return true
    end,
    is_closing = function()
      return closing
    end,
    terminate = stop,
  }
end

local ok, err = xpcall(function()
  require("conform").setup(require("plugins.formatter")[1].opts)
  local buf = vim.api.nvim_create_buf(false, false)
  vim.api.nvim_set_current_buf(buf)
  local path = root .. "/example.txt"
  vim.api.nvim_buf_set_name(buf, path)
  vim.bo[buf].filetype = "lsp_format_test"
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "unformatted" })
  client_id = vim.lsp.start({
    name = "formatting-fixture",
    cmd = server,
    root_dir = root,
  })
  assert(client_id, "Could not start the in-process fixture")
  assert(
    vim.wait(1000, function()
      local client = vim.lsp.get_client_by_id(client_id)
      return client
        and client.initialized
        and vim.lsp.buf_is_attached(buf, client_id)
    end),
    "Fixture did not attach"
  )

  vim.cmd("silent write")
  assert(
    vim.deep_equal(vim.fn.readfile(path), { "formatted by LSP" }),
    "Save did not use LSP fallback"
  )

  local function manual_format(expected)
    vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "unformatted" })
    vim.api.nvim_feedkeys(" f", "xt", false)
    assert(
      vim.deep_equal(
        vim.api.nvim_buf_get_lines(buf, 0, -1, false),
        { expected }
      ),
      "Manual formatting selected the wrong provider"
    )
  end
  manual_format("formatted by LSP")

  local conform = require("conform")
  conform.formatters.missing_fixture =
    { command = root .. "/not-installed", args = {}, stdin = true }
  conform.formatters_by_ft.lsp_format_test = { "missing_fixture" }
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "unformatted" })
  vim.cmd("silent write")
  assert(
    vim.deep_equal(vim.fn.readfile(path), { "formatted by LSP" }),
    "Unavailable formatter prevented LSP fallback"
  )

  -- A Conform formatter must retain priority over LSP, on save and manually.
  conform.formatters.lua_fixture = {
    format = function(_, _, _, callback)
      callback(nil, { "formatted by Conform" })
    end,
  }
  conform.formatters_by_ft.lsp_format_test = { "lua_fixture" }
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, { "unformatted" })
  vim.cmd("silent write")
  assert(
    vim.deep_equal(vim.fn.readfile(path), { "formatted by Conform" }),
    "LSP overrode the Conform formatter on save"
  )
  manual_format("formatted by Conform")
end, debug.traceback)

local client = client_id and vim.lsp.get_client_by_id(client_id)
if client then
  client:stop(true)
end
vim.api.nvim_create_autocmd("VimLeave", {
  once = true,
  callback = function()
    vim.fn.delete(root, "rf")
  end,
})
assert(ok, err)
print(
  "PASS: save/manual LSP fallback, unavailable formatter fallback and Conform priority"
)
