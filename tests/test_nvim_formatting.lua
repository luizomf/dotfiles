-- Run from the repository root: nvim --clean --headless -i NONE -l tests/test_nvim_formatting.lua
-- Requires installed Conform, Prettier, StyLua, Ruff and Taplo; no tools are installed.
local repo = vim.fn.getcwd()
local data = vim.fn.stdpath("data")
local root = vim.fn.tempname()
vim.fn.mkdir(root, "p", 448)
vim.env.XDG_CONFIG_HOME = root .. "/config"
vim.env.XDG_STATE_HOME = root .. "/state"
vim.env.XDG_CACHE_HOME = root .. "/cache"
vim.opt.rtp:append(repo .. "/nvim")
vim.opt.rtp:append(data .. "/lazy/conform.nvim")
vim.env.PATH = data .. "/mason/bin:" .. vim.env.PATH

local function write(path, contents)
  vim.fn.mkdir(vim.fn.fnamemodify(path, ":h"), "p")
  vim.fn.writefile(vim.split(contents, "\n", { plain = true }), path)
end

local function format(path, ft, input, expected)
  local buf = vim.api.nvim_create_buf(false, false)
  vim.api.nvim_buf_set_name(buf, path)
  vim.bo[buf].filetype = ft
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, input)
  local finished = false
  local err
  require("conform").format(
    { bufnr = buf, async = false, timeout_ms = 5000, lsp_format = "never" },
    function(error)
      err = error
      finished = true
    end
  )
  assert(finished, "Formatting did not complete")
  local actual = vim.api.nvim_buf_get_lines(buf, 0, -1, false)
  if expected then
    assert(not err, tostring(err))
    assert(
      vim.deep_equal(actual, expected),
      path .. ": got " .. vim.inspect(actual)
    )
  else
    assert(err, "Invalid project configuration must report an error")
    assert(
      vim.deep_equal(actual, input),
      "Failed formatting changed the buffer"
    )
  end
  vim.api.nvim_buf_delete(buf, { force = true })
end

local ok, err = xpcall(function()
  vim.cmd.cd(root)
  write(
    root .. "/config/nvim/config_files/prettierrc.json",
    '{"singleQuote": true, "semi": true}'
  )
  write(
    root .. "/config/nvim/config_files/stylua.toml",
    'indent_type = "Spaces"\nindent_width = 2\nquote_style = "ForceDouble"'
  )
  local opts = require("plugins.formatter")[1].opts
  opts.format_on_save = nil
  opts.notify_on_error = false -- The invalid-config case asserts the callback error.
  require("conform").setup(opts)

  write(
    root .. "/project/.prettierrc.json",
    '{"singleQuote": false, "semi": false}'
  )
  vim.fn.mkdir(root .. "/project/src", "p")
  format(
    root .. "/project/src/example.js",
    "javascript",
    { "const value='hello';" },
    { 'const value = "hello"' }
  )

  write(
    root .. "/project/.stylua.toml",
    'indent_type = "Spaces"\nindent_width = 4\nquote_style = "ForceSingle"'
  )
  format(
    root .. "/project/src/example.lua",
    "lua",
    { 'if true then print("hello") end' },
    { "if true then", "    print('hello')", "end" }
  )

  vim.fn.mkdir(root .. "/unconfigured", "p")
  format(
    root .. "/unconfigured/example.js",
    "javascript",
    { 'const value="hello"' },
    { "const value = 'hello';" }
  )
  format(
    root .. "/unconfigured/example.lua",
    "lua",
    { "if true then print('hello') end" },
    { "if true then", '  print("hello")', "end" }
  )

  write(
    root .. "/package/package.json",
    '{"prettier": {"singleQuote": false, "semi": false}}'
  )
  vim.fn.mkdir(root .. "/package/src", "p")
  format(
    root .. "/package/src/example.js",
    "javascript",
    { "const value='hello';" },
    { 'const value = "hello"' }
  )

  write(
    root .. "/editor/.editorconfig",
    "root = true\n[*]\nindent_style = space\nindent_size = 4"
  )
  vim.fn.mkdir(root .. "/editor/src", "p")
  format(
    root .. "/editor/src/example.js",
    "javascript",
    { 'function f(){console.log("hi")}' },
    { "function f() {", '    console.log("hi");', "}" }
  )
  format(
    root .. "/editor/src/example.lua",
    "lua",
    { 'if true then print("hello") end' },
    { "if true then", '    print("hello")', "end" }
  )

  write(
    root .. "/python/pyproject.toml",
    "[tool.ruff.format]\nquote-style = 'single'"
  )
  vim.fn.mkdir(root .. "/python/src", "p")
  format(
    root .. "/python/src/example.py",
    "python",
    { 'value = "hello"' },
    { "value = 'hello'" }
  )

  write(
    root .. "/toml/.taplo.toml",
    "[formatting]\nindent_entries = true\nindent_string = '    '"
  )
  vim.fn.mkdir(root .. "/toml/src", "p")
  format(
    root .. "/toml/src/example.toml",
    "toml",
    { "[section]", "key=1" },
    { "[section]", "    key = 1" }
  )

  write(root .. "/invalid/.prettierrc.json", "{invalid json")
  format(
    root .. "/invalid/example.js",
    "javascript",
    { "const value='hello';" },
    nil
  )
end, debug.traceback)
vim.cmd.cd(repo)
vim.api.nvim_create_autocmd("VimLeave", {
  once = true,
  callback = function()
    vim.fn.delete(root, "rf")
  end,
})
assert(ok, err)
print("PASS: project-first formatting")
