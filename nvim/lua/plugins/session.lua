return {
  "rmagatti/auto-session",
  lazy = false, -- carrega logo no início
  config = function()
    require("auto-session").setup({
      log_level = "error",
      auto_session_suppress_dirs = { "~/", "/", "~/Downloads" },
      auto_save_enabled = true,
      auto_restore_enabled = true,
      auto_session_use_git_branch = true,
    })
  end,
}
