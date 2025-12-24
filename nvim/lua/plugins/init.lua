return {
  {
    "luizomf/settings",
    dev = true,
    dir = vim.fn.stdpath("config") .. "/lua/settings",
    lazy = false,
    priority = 1000,
    config = function()
      require("settings").setup()
    end,
  },
}
