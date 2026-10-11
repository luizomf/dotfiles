-- Bootstrap policy is shared by normal startup and explicit locked restoration.
return function()
  local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
  if not vim.loop.fs_stat(lazypath) then
    local output = vim.fn.system({
      "git",
      "clone",
      "--filter=blob:none",
      "https://github.com/folke/lazy.nvim.git",
      "--branch=stable",
      lazypath,
    })
    if vim.v.shell_error ~= 0 then
      error(
        ("Failed to bootstrap lazy.nvim at %s (git exit %d):\n%s"):format(
          lazypath,
          vim.v.shell_error,
          output
        ),
        0
      )
    end
  end
  vim.opt.rtp:prepend(lazypath)
end
