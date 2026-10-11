-- Run from the repository root with an installed public Lazy checkout (read-only):
-- nvim --clean --headless -i NONE -l tests/test_nvim_locked_restore.lua [lazy-source]
local repo = vim.fn.getcwd()
local source = arg[1] or (vim.fn.stdpath("data") .. "/lazy/lazy.nvim")
local root = vim.fn.tempname()
local locked = "306a05526ada86a7b30af95c5cc81ffba93fef97"
local stable = "85c7ff3711b730b4030d03144f6db6375044ae82"
local nvim = vim.v.progpath
vim.fn.mkdir(root, "p")
-- Git is physically unable to use HTTP/SSH, even if Lazy changes an origin.
vim.env.GIT_ALLOW_PROTOCOL = "file"
vim.env.GIT_CONFIG_NOSYSTEM = "1"
vim.env.GIT_CONFIG_GLOBAL = root .. "/gitconfig"
vim.env.HOME = root
vim.env.NVIM_APPNAME = "nvim"

local function run(args)
  local output = vim.fn.system(args)
  assert(vim.v.shell_error == 0, table.concat(args, " ") .. "\n" .. output)
  return vim.trim(output)
end

local function git(dir, ...)
  return run({ "git", "-C", dir, ... })
end

local function write(path, text)
  vim.fn.mkdir(vim.fn.fnamemodify(path, ":h"), "p")
  vim.fn.writefile(vim.split(text, "\n", { plain = true }), path, "b")
end

local function read(path)
  return table.concat(vim.fn.readfile(path, "b"), "\n")
end

local function native_lock(lock)
  local names, lines = vim.tbl_keys(lock), { "{" }
  table.sort(names)
  for i, name in ipairs(names) do
    local pin = lock[name]
    lines[#lines + 1] = ('  %q: { "branch": %q, "commit": %q }%s'):format(
      name,
      pin.branch,
      pin.commit,
      i == #names and "" or ","
    )
  end
  return table.concat(lines, "\n") .. "\n}\n"
end

local ok, err = xpcall(function()
  -- Copy public source objects; never checkout/fetch/write inside the source.
  local manager_origin = root .. "/manager-origin"
  run({
    "git",
    "clone",
    "--no-hardlinks",
    "--branch=main",
    source,
    manager_origin,
  })
  git(manager_origin, "cat-file", "-e", locked .. "^{commit}")
  git(manager_origin, "cat-file", "-e", stable .. "^{commit}")
  git(manager_origin, "branch", "stable", stable)
  run({
    "git",
    "config",
    "--global",
    "url." .. manager_origin .. ".insteadOf",
    "https://github.com/folke/lazy.nvim.git",
  })

  local plugin_origin = root .. "/plugin-origin"
  run({ "git", "init", "-b", "main", plugin_origin })
  write(plugin_origin .. "/README", "inert plugin\n")
  git(plugin_origin, "add", ".")
  git(
    plugin_origin,
    "-c",
    "user.name=Fixture",
    "-c",
    "user.email=fixture@example.invalid",
    "commit",
    "-m",
    "first"
  )
  local pin = git(plugin_origin, "rev-parse", "HEAD")
  write(plugin_origin .. "/README", "second inert revision\n")
  git(plugin_origin, "add", ".")
  git(
    plugin_origin,
    "-c",
    "user.name=Fixture",
    "-c",
    "user.email=fixture@example.invalid",
    "commit",
    "-m",
    "second"
  )

  for _, name in ipairs({ "existing", "disabled" }) do
    run({ "git", "clone", plugin_origin, plugin_origin .. "-" .. name })
  end

  local lock = {
    ["lazy.nvim"] = { branch = "main", commit = locked },
    missing = { branch = "main", commit = pin },
    existing = { branch = "main", commit = pin },
    disabled = { branch = "main", commit = pin },
  }
  local original = native_lock(lock)
  local installer_command = assert(
    read(repo .. "/install.sh"):match(
      "[^\n]*nvim [^\n]*%$REPO_DIR/nvim/restore%.lua[^\n]*"
    ),
    "Installer must use the explicit locked restore entry point"
  )
  local function fixture(name, existing)
    local case = root .. "/" .. name .. " with spaces"
    for _, kind in ipairs({ "DATA", "STATE", "CACHE", "CONFIG" }) do
      vim.env["XDG_" .. kind .. "_HOME"] = case .. "/" .. kind:lower()
    end
    local config = case .. "/config/nvim"
    write(config .. "/init.lua", read(repo .. "/nvim/init.lua"))
    write(config .. "/lazy-lock.json", original)
    write(
      config .. "/lua/settings/init.lua",
      "return { setup = function() end }"
    )
    write(config .. "/lua/settings/theme.lua", "return {}")
    write(config .. "/lua/keymaps.lua", "return {}")
    write(
      config .. "/lua/settings/lazy_bootstrap.lua",
      read(repo .. "/nvim/lua/settings/lazy_bootstrap.lua")
    )
    write(
      config .. "/lua/plugins/init.lua",
      ([[return {
      { name = 'existing', url = %q, lazy = true },
      { name = 'missing', url = %q, lazy = true },
      { name = 'disabled', url = %q, enabled = false },
    }]]):format(
        plugin_origin .. "-existing",
        plugin_origin,
        plugin_origin .. "-disabled"
      )
    )
    local data = case .. "/data/nvim/lazy"
    if existing then
      vim.fn.mkdir(data, "p")
      run({
        "git",
        "clone",
        "--branch=stable",
        "https://github.com/folke/lazy.nvim.git",
        data .. "/lazy.nvim",
      })
      run({ "git", "clone", plugin_origin .. "-existing", data .. "/existing" })
    end
    return config, data
  end

  -- Reach the original startup -> missing install -> restore ordering.
  local config = fixture("legacy", false)
  write(
    config .. "/legacy.lua",
    ([[
    vim.opt.rtp:prepend(%q)
    dofile(%q .. '/init.lua')
    vim.cmd('Lazy! restore')
  ]]):format(config, config)
  )
  run({
    nvim,
    "--clean",
    "--headless",
    "-i",
    "NONE",
    "-l",
    config .. "/legacy.lua",
  })
  local drifted = vim.json.decode(read(config .. "/lazy-lock.json"))
  assert(
    drifted["lazy.nvim"].commit == stable,
    "Legacy fixture did not reproduce self-pin drift: " .. vim.inspect(drifted)
  )
  assert(
    drifted.missing.commit == pin,
    "Legacy fixture lost the missing plugin's pin"
  )
  print("BEFORE: legacy clean bootstrap overwrites Lazy's pin before restore")

  for _, scenario in ipairs({ "clean", "partial" }) do
    local config_path, data = fixture(scenario, scenario == "partial")
    write(config_path .. "/restore.lua", read(repo .. "/nvim/restore.lua"))
    for iteration = 1, 2 do
      -- Execute only the actual restore command, never install.sh. The function
      -- selects the current test binary without changing the installer's args.
      run({
        "/bin/bash",
        "-c",
        'REPO_DIR="$1"; NVIM_TEST_BIN="$2"; nvim() { "$NVIM_TEST_BIN" "$@"; }; '
          .. installer_command,
        "fixture",
        vim.fn.fnamemodify(config_path, ":h"),
        nvim,
      })
      assert(
        read(config_path .. "/lazy-lock.json") == original,
        "Restore rewrote lockfile bytes"
      )
      for _, plugin in ipairs({ "lazy.nvim", "missing", "existing" }) do
        assert(
          git(data .. "/" .. plugin, "rev-parse", "HEAD") == lock[plugin].commit,
          plugin .. " was not restored"
        )
      end
      print(
        ("AFTER: %s pass %d: all installed HEADs locked; lock bytes unchanged"):format(
          scenario,
          iteration
        )
      )
    end
    -- Ordinary Lazy can also serialize the canonical file without byte drift.
    write(
      config_path .. "/native.lua",
      ([[
      vim.opt.rtp:prepend(%q)
      dofile(%q .. '/init.lua')
      vim.cmd('Lazy! restore')
    ]]):format(config_path, config_path)
    )
    run({
      nvim,
      "--clean",
      "--headless",
      "-i",
      "NONE",
      "-l",
      config_path .. "/native.lua",
    })
    assert(
      read(config_path .. "/lazy-lock.json") == original,
      "Native writer changed canonical bytes"
    )
  end

  for _, failure in ipairs({ "dirty", "unavailable", "malformed", "unpinned" }) do
    local config_path, data = fixture(failure, true)
    write(config_path .. "/restore.lua", read(repo .. "/nvim/restore.lua"))
    if failure == "dirty" then
      write(data .. "/existing/README", "uncommitted user change\n")
    elseif failure == "unavailable" then
      local broken = vim.deepcopy(lock)
      broken.missing.commit = string.rep("0", 40)
      write(config_path .. "/lazy-lock.json", native_lock(broken))
    elseif failure == "unpinned" then
      local broken = vim.deepcopy(lock)
      broken.missing = nil
      write(config_path .. "/lazy-lock.json", native_lock(broken))
    else
      write(config_path .. "/lazy-lock.json", "not JSON\n")
    end
    local before = read(config_path .. "/lazy-lock.json")
    local output = vim.fn.system({
      nvim,
      "--clean",
      "--headless",
      "-i",
      "NONE",
      "-l",
      config_path .. "/restore.lua",
    })
    assert(
      vim.v.shell_error ~= 0,
      "Restore falsely succeeded: " .. failure .. "\n" .. output
    )
    assert(
      read(config_path .. "/lazy-lock.json") == before,
      "Failed restore changed the lockfile"
    )
    if failure == "dirty" then
      assert(
        read(data .. "/existing/README") == "uncommitted user change\n",
        "Restore discarded local edits"
      )
      assert(output:find("Lazy task failed", 1, true), output)
    end
    if failure == "unpinned" then
      assert(
        vim.fn.isdirectory(data .. "/missing") == 0,
        "Unpinned plugin was installed\n" .. output
      )
    end
    print("PASS: " .. failure .. " fails without lockfile changes")
  end
end, debug.traceback)
vim.fn.delete(root, "rf")
assert(ok, err)
