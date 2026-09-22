-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_bootstrap.lua
-- Uses a failing Git fixture and isolated data paths; no downloads or installed plugins.
local repo = vim.fn.getcwd()
local root = vim.fn.tempname()
vim.fn.mkdir(root .. "/bin", "p", 448)
vim.env.XDG_DATA_HOME = root .. "/data"
vim.env.XDG_STATE_HOME = root .. "/state"
vim.env.XDG_CACHE_HOME = root .. "/cache"
vim.env.XDG_CONFIG_HOME = root .. "/config"
vim.env.PATH = root .. "/bin"
vim.opt.rtp = { vim.env.VIMRUNTIME, repo .. "/nvim" }
vim.fn.writefile(
  { "#!/bin/sh", "printf '%s\\n' 'simulated clone failure' >&2", "exit 23" },
  root .. "/bin/git"
)
assert(vim.uv.fs_chmod(root .. "/bin/git", 448))

local ok, err = xpcall(function()
  local started, failure = pcall(dofile, repo .. "/nvim/init.lua")
  assert(not started, "Initialization continued after failed Git clone")
  assert(
    tostring(failure):find("simulated clone failure", 1, true),
    "Initialization lost the Git error: " .. tostring(failure)
  )
  assert(
    tostring(failure):find("git exit 23", 1, true),
    "Initialization lost the Git exit status"
  )
  assert(
    tostring(failure):find(vim.fn.stdpath("data") .. "/lazy/lazy.nvim", 1, true),
    "Initialization did not identify the installation path"
  )

  -- An existing plugin is reused even when Git would fail.
  local plugin = vim.fn.stdpath("data") .. "/lazy/lazy.nvim/lua"
  vim.fn.mkdir(plugin, "p", 448)
  vim.fn.writefile(
    { "return { setup = function() end }" },
    plugin .. "/lazy.lua"
  )
  dofile(repo .. "/nvim/init.lua")
  assert(
    vim.fn.maparg(" f", "n") ~= "",
    "Existing-plugin startup did not load the normal mappings"
  )
end, debug.traceback)
vim.fn.delete(root, "rf")
assert(ok, err)
print(
  "PASS: Lazy clone error context, isolated data path and reuse of an existing plugin"
)
