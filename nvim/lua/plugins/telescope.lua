local function search_args()
  return {
    "--hidden",
    "--glob=!.git",
    "--glob=!.env",
    "--glob=!.env.*",
    "--glob=!.venv",
    "--glob=!node_modules",
  }
end

return {
  "nvim-telescope/telescope.nvim",
  tag = "v0.2.1",
  dependencies = {
    "nvim-lua/plenary.nvim",
  },
  config = function()
    require("telescope").setup({
      defaults = {
        file_ignore_patterns = {
          "node_modules",
        },
      },
      pickers = {
        find_files = {
          find_command = function()
            return vim.list_extend({ "rg", "--files" }, search_args())
          end,
        },
        live_grep = { additional_args = search_args },
        buffers = {
          show_all_buffers = true,
          sort_mru = true,
        },
      },
    })
  end,
}
