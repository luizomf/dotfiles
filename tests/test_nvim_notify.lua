-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_notify.lua
vim.opt.rtp:append(vim.fn.getcwd() .. "/nvim")
require("settings.utils")
local notify = vim.notify
local notification
vim.notify = function(message, level, opts)
  notification = { message = message, level = level, opts = opts }
end

local ok, err = xpcall(function()
  vim.cmd("Notify hello warn 3500")
  assert(notification.message == "hello", "Notify changed the message")
  assert(
    notification.level == vim.log.levels.WARN,
    "Notify did not normalize the severity name"
  )
  assert(notification.opts.timeout == 3500, "Notify changed the timeout")

  for _, case in ipairs({
    { "ERROR", vim.log.levels.ERROR },
    { "3", vim.log.levels.WARN },
    { "0", vim.log.levels.TRACE },
  }) do
    vim.cmd("Notify hello " .. case[1])
    assert(
      notification.level == case[2],
      "Notify did not normalize severity " .. case[1]
    )
  end
  vim.cmd("Notify")
  assert(
    notification.message == "NO MESSAGE"
      and notification.level == vim.log.levels.INFO
      and notification.opts.timeout == 2000,
    "Notify changed its defaults"
  )
  vim.cmd([[Notify hello\ world info]])
  assert(
    notification.message == "hello world",
    "Notify changed Ex-escaped message handling"
  )

  for _, invalid in ipairs({ "banana", "-1", "1.5", "99" }) do
    vim.cmd("Notify hello " .. invalid)
    assert(
      notification.level == vim.log.levels.ERROR
        and notification.message ~= "hello"
        and notification.message:find(invalid, 1, true),
      "Notify did not explain invalid severity " .. invalid
    )
  end
end, debug.traceback)
vim.notify = notify
assert(ok, err)
print(
  "PASS: Notify severity names/codes, invalid-level errors, defaults and escaped messages"
)
