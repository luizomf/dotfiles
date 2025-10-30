return {
  "nvim-telescope/telescope.nvim",
  tag = "0.1.8",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "crispgm/telescope-heading.nvim",
    { "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
  },
  extensions = {
    heading = {
      treesitter = true,
    },
  },
  config = function()
    require("telescope").setup({
      pickers = {
        buffers = {
          show_all_buffers = true,
          short_mru = true,
        },
      },
    })
  end,
}
