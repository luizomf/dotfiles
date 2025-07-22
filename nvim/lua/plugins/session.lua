return {
  "rmagatti/auto-session",
  lazy = false, -- carrega logo no início
  config = function()
    require("auto-session").setup({
      auto_restore = true,
      auto_save = true,
      git_use_branch_name = true,
      log_level = "error",
      suppressed_dirs = { "~/", "/", "~/Downloads" },
    })
  end,
}
