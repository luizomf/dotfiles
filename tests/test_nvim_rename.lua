-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_rename.lua
vim.opt.rtp:append(vim.fn.getcwd() .. "/nvim")
vim.o.swapfile = false
require("settings.utils")
local root = vim.fn.tempname()
vim.fn.mkdir(root, "p", 448)
root = assert(vim.uv.fs_realpath(root))

local function open_file(path)
  vim.fn.writefile({ "original contents" }, path)
  vim.api.nvim_cmd(
    { cmd = "edit", args = { path }, magic = { file = false } },
    {}
  )
  vim.api.nvim_buf_set_lines(0, 0, -1, false, { "edited contents" })
end

local protected = root .. "/readonly"
local notify = vim.notify
local ok, err = xpcall(function()
  for i, name in ipairs({
    "old %.txt",
    "old #.txt",
    "old !.txt",
    "spaces ' ü.txt",
  }) do
    local old = root .. "/" .. name
    local new = root .. "/renamed " .. i .. " ü.txt"
    open_file(old)
    vim.cmd.Rename({ new })
    assert(
      vim.fn.filereadable(old) == 0,
      "Rename left the original file behind: " .. name
    )
    assert(
      vim.deep_equal(vim.fn.readfile(new), { "edited contents" }),
      "Rename lost unsaved edits"
    )
    assert(
      vim.api.nvim_buf_get_name(0) == new,
      "Rename did not keep the destination current"
    )
  end

  local old = root .. "/overwrite-source.txt"
  local new = root .. "/existing.txt"
  open_file(old)
  vim.fn.writefile({ "do not overwrite" }, new)
  assert(
    not pcall(vim.cmd.Rename, { new }),
    "Rename overwrote an existing destination"
  )
  assert(
    vim.deep_equal(vim.fn.readfile(new), { "do not overwrite" }),
    "Existing destination changed"
  )
  assert(
    vim.deep_equal(vim.fn.readfile(old), { "original contents" }),
    "Refused rename changed the source file"
  )
  assert(
    vim.deep_equal(
      vim.api.nvim_buf_get_lines(0, 0, -1, false),
      { "edited contents" }
    ),
    "Refused rename lost unsaved edits"
  )
  vim.bo.modified = false

  vim.fn.mkdir(protected, "p", 448)
  old = protected .. "/original.txt"
  new = root .. "/saved-despite-delete-failure.txt"
  open_file(old)
  assert(vim.uv.fs_chmod(protected, 320)) -- 0500: readable, not writable.
  if vim.uv.fs_access(protected, "W") then
    print(
      "SKIP: deletion denial (directory permissions are not enforced for this user)"
    )
  else
    local message, level
    vim.notify = function(msg, severity)
      message, level = msg, severity
    end
    vim.cmd.Rename({ new })
    vim.notify = notify
    assert(vim.fn.filereadable(old) == 1, "Deletion failure lost the original")
    assert(
      vim.deep_equal(vim.fn.readfile(new), { "edited contents" }),
      "Deletion failure lost the destination"
    )
    assert(
      vim.api.nvim_buf_get_name(0) == new,
      "Deletion failure switched away from the saved destination"
    )
    assert(
      level == vim.log.levels.ERROR
        and message:find(old, 1, true)
        and message:find(new, 1, true),
      "Deletion failure was not reported with both paths"
    )
  end
end, debug.traceback)
vim.notify = notify
vim.uv.fs_chmod(protected, 448)
vim.fn.delete(root, "rf")
assert(ok, err)
print(
  "PASS: Rename literal filenames, edited content, overwrite protection and deletion-failure handling (unless skipped above)"
)
