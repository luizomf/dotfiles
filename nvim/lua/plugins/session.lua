return {
  "rmagatti/auto-session",
  lazy = false,
  config = function()
    require("auto-session").setup({
      git_use_branch_name = true,
      suppressed_dirs = { "~/", "/", "~/Downloads" },
      session_lens = {
        picker = "telescope",
      },
    })
  end,
}
