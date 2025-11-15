return {
  "rmagatti/auto-session",
  lazy = false, -- carrega logo no início
  config = function()
    require("auto-session").setup({
      git_use_branch_name = true,
      suppressed_dirs = { "~/", "/", "~/Downloads" },

      -- Saving / restoring
      enabled = true, -- Enables/disables auto creating, saving and restoring
      auto_save = true, -- Enables/disables auto saving session on exit
      auto_restore = true, -- Enables/disables auto restoring session on start
      auto_create = true, -- Enables/disables auto creating new session files. Can be a function that returns true if a new session file should be allowed
      auto_restore_last_session = false, -- On startup, loads the last saved session if session for cwd does not exist
      cwd_change_handling = false, -- Automatically save/restore sessions when changing directories
      single_session_mode = false, -- Enable single session mode to keep all work in one session regardless of cwd changes. When enabled, prevents creation of separate sessions for different directories and maintains one unified session. Does not work with cwd_change_handling

      -- Filtering
      allowed_dirs = nil, -- Allow session restore/create in certain directories
      bypass_save_filetypes = nil, -- List of filetypes to bypass auto save when the only buffer open is one of the file types listed, useful to ignore dashboards
      close_filetypes_on_save = { "checkhealth" }, -- Buffers with matching filetypes will be closed before saving
      close_unsupported_windows = true, -- Close windows that aren't backed by normal file before autosaving a session
      preserve_buffer_on_restore = nil, -- Function that returns true if a buffer should be preserved when restoring a session

      -- Git / Session naming
      git_auto_restore_on_branch_change = false, -- Should we auto-restore the session when the git branch changes. Requires git_use_branch_name
      custom_session_tag = nil, -- Function that can return a string to be used as part of the session name

      -- Deleting
      auto_delete_empty_sessions = true, -- Enables/disables deleting the session if there are only unnamed/empty buffers when auto-saving
      purge_after_minutes = nil, -- Sessions older than purge_after_minutes will be deleted asynchronously on startup, e.g. set to 14400 to delete sessions that haven't been accessed for more than 10 days, defaults to off (no purging), requires >= nvim 0.10

      -- Saving extra data
      save_extra_data = nil, -- Function that returns extra data that should be saved with the session. Will be passed to restore_extra_data on restore
      restore_extra_data = nil, -- Function called when there's extra data saved for a session

      -- Argument handling
      args_allow_single_directory = true, -- Follow normal session save/load logic if launched with a single directory as the only argument
      args_allow_files_auto_save = false, -- Allow saving a session even when launched with a file argument (or multiple files/dirs). It does not load any existing session first. Can be true or a function that returns true when saving is allowed. See documentation for more detail

      -- Misc
      log_level = "error", -- Sets the log level of the plugin (debug, info, warn, error).
      root_dir = vim.fn.stdpath("data") .. "/sessions/", -- Root dir where sessions will be stored
      show_auto_restore_notif = false, -- Whether to show a notification when auto-restoring
      restore_error_handler = nil, -- Function called when there's an error restoring. By default, it ignores fold and help errors otherwise it displays the error and returns false to disable auto_save. Default handler is accessible as require('auto-session').default_restore_error_handler
      continue_restore_on_error = true, -- Keep loading the session even if there's an error
      lsp_stop_on_restore = false, -- Should language servers be stopped when restoring a session. Can also be a function that will be called if set. Not called on autorestore from startup
      lazy_support = true, -- Automatically detect if Lazy.nvim is being used and wait until Lazy is done to make sure session is restored correctly. Does nothing if Lazy isn't being used
      legacy_cmds = true, -- Define legacy commands: Session*, Autosession (lowercase s), currently true. Set to false to prevent defining them
    })
  end,
}
