-- Explicit maintenance process; normal editor startup keeps its bootstrap policy.
-- Run: nvim --clean --headless -i NONE -l ~/dotfiles/nvim/restore.lua
local config = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h")
local lockfile = config .. "/lazy-lock.json"
local original = table.concat(vim.fn.readfile(lockfile, "b"), "\n")
local pins = vim.json.decode(original)
assert(type(pins) == "table" and pins["lazy.nvim"], "Missing Lazy lockfile pin")
for name, pin in pairs(pins) do
  assert(
    type(pin) == "table"
      and type(pin.commit) == "string"
      and pin.commit:match("^%x+$")
      and #pin.commit == 40,
    "Invalid lockfile commit for " .. name
  )
end

vim.opt.rtp:prepend(config)
require("settings.lazy_bootstrap")()

-- Lazy writes every installed revision after missing-plugin installation, not
-- just the plugins it installed. Freeze its writer BEFORE setup so both startup
-- installation and restore read the original pins, including Lazy's own pin.
-- This internal API is covered against the locked manager by the regression test.
local Lock = require("lazy.manage.lock")
local update = Lock.update
Lock.update = function() end

-- Lazy emits this after resolving specs/state and before installing anything.
-- Refuse unpinned Git plugins rather than let a locked operation select HEAD.
local guard = vim.api.nvim_create_autocmd("User", {
  pattern = "LazyPlugins",
  callback = function()
    for name, plugin in pairs(require("lazy.core.config").plugins) do
      if plugin.url and not plugin._.is_local and not pins[name] then
        -- Autocommand errors are reported but do not abort Lazy's caller.
        io.stderr:write("No lockfile pin for " .. name .. "\n")
        vim.cmd("cquit 1")
      end
    end
  end,
})

local function check_tasks()
  for name, plugin in pairs(require("lazy.core.config").plugins) do
    for _, task in ipairs(plugin._.tasks or {}) do
      assert(
        not task:has_errors(),
        "Lazy task failed for " .. name .. ": " .. task:output()
      )
    end
  end
end

local ok, err = xpcall(function()
  vim.g.mapleader = " "
  require("settings").setup()
  require("keymaps")
  require("settings.theme")
  require("lazy").setup("plugins", { lockfile = lockfile })
  check_tasks()
  require("lazy").restore({ wait = true, show = false })
  check_tasks()

  local Git = require("lazy.manage.git")
  for name, plugin in pairs(require("lazy.core.config").plugins) do
    if plugin.url and not plugin._.is_local then
      local pin = assert(pins[name], "No lockfile pin for " .. name)
      local info = Git.info(plugin.dir)
      assert(
        info and info.commit == pin.commit,
        "Locked restore did not reach the pin for " .. name
      )
    end
  end
  assert(
    table.concat(vim.fn.readfile(lockfile, "b"), "\n") == original,
    "Lockfile changed during locked restore"
  )
end, debug.traceback)
Lock.update = update
vim.api.nvim_del_autocmd(guard)
assert(ok, err)
print("Locked plugin restore completed; lockfile unchanged")
