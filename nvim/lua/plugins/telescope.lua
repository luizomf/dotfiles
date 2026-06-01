return {
  "nvim-telescope/telescope.nvim",
  tag = "v0.2.1",
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
      defaults = {
        file_ignore_patterns = {
          "node_modules",
        },
      },
      pickers = {
        buffers = {
          show_all_buffers = true,
          short_mru = true,
        },
      },
    })
  end,
}
