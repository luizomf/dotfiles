-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_telescope_search.lua
-- Uses installed Telescope/Plenary and ripgrep against synthetic temporary files.
local repo = vim.fn.getcwd()
local data = vim.fn.stdpath("data")
local temp = vim.fn.tempname()
vim.fn.mkdir(temp .. "/project", "p", 448)
local root = assert(vim.uv.fs_realpath(temp .. "/project"))
vim.env.XDG_STATE_HOME = temp .. "/state"
vim.env.XDG_CACHE_HOME = temp .. "/cache"
vim.env.RIPGREP_CONFIG_PATH = nil
vim.opt.rtp:append(repo .. "/nvim")
vim.opt.rtp:append(data .. "/lazy/plenary.nvim")
vim.opt.rtp:append(data .. "/lazy/telescope.nvim")
vim.o.columns = 160
vim.o.lines = 45

local function write(path, lines)
  vim.fn.mkdir(vim.fn.fnamemodify(root .. "/" .. path, ":h"), "p", 448)
  vim.fn.writefile(lines, root .. "/" .. path)
end

local ok, err = xpcall(function()
  assert(vim.fn.executable("rg") == 1, "ripgrep is required")
  write(".gitignore", { "ignored.txt" })
  for _, file in ipairs({
    "visible.txt",
    "tmux/.tmux.conf",
    "nested/.configrc",
    ".env",
    ".env.local",
    "nested/.env",
    "nested/.env.test",
    ".venv/private.txt",
    "nested/.venv/private.txt",
    "node_modules/pkg/index.js",
    "nested/node_modules/pkg/index.js",
    ".git/config",
    "nested/.git/config",
    "ignored.txt",
  }) do
    write(file, { "fixture_search_token" })
  end
  require("plugins.telescope").config()
  local function check_picker(name, opts, expected)
    local results
    opts.cwd = root
    -- Avoid asynchronous preview reads during fixture teardown; production keeps previews.
    opts.previewer = false
    opts.on_complete = {
      function(picker)
        results = {}
        for entry in picker.manager:iter() do
          local path = entry.filename or entry.value
          path = path:gsub("^" .. vim.pesc(root .. "/"), ""):gsub("^%./", "")
          table.insert(results, path)
        end
        table.sort(results)
      end,
    }
    require("telescope.builtin")[name](opts)
    assert(
      vim.wait(5000, function()
        return results ~= nil
      end),
      name .. " did not complete"
    )
    assert(
      vim.deep_equal(results, expected),
      "Unexpected " .. name .. " results: " .. vim.inspect(results)
    )
    require("telescope.actions").close(vim.api.nvim_get_current_buf())
  end
  check_picker(
    "find_files",
    {},
    { ".gitignore", "nested/.configrc", "tmux/.tmux.conf", "visible.txt" }
  )
  check_picker(
    "live_grep",
    { default_text = "fixture_search_token" },
    { "nested/.configrc", "tmux/.tmux.conf", "visible.txt" }
  )
end, debug.traceback)
vim.fn.delete(temp, "rf")
assert(ok, err)
print("PASS: Telescope hidden files and search exclusions")
