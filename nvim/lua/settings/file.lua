vim.opt.completeopt = { "menu", "menuone", "noselect" }
vim.opt.encoding = "utf-8"
vim.opt.fileencoding = "utf-8"

-- https://neovim.io/doc/user/lua.html#vim.filetype.add()
vim.filetype.add({
  pattern = {
    [vim.fn.expand("~") .. "/dotfiles/zsh/config/.*"] = "sh",
    [vim.fn.expand("~") .. "/dotfiles/ghostty/config"] = "sh",
    [vim.fn.expand("~") .. "/%.ssh/config%.d/.*"] = "sshconfig",
  },
})
