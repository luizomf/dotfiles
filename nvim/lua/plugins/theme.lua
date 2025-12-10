return {
  {
    "folke/tokyonight.nvim",
    lazy = false,
    priority = 1000,
    config = function()
      require("tokyonight").setup({
        style = "night", -- The theme comes in three styles, `storm`, a darker variant `night` and `day`
        light_style = "day", -- The theme is used when the background is set to light
        transparent = true, -- Enable this to disable setting the background color
        terminal_colors = false, -- Configure the colors used when opening a `:terminal` in Neovim
        styles = {
          -- Style to be applied to different syntax groups
          -- Value is any valid attr-list value for `:help nvim_set_hl`
          comments = { italic = true },
          keywords = { italic = true },
          functions = {},
          variables = {},
          -- Background styles. Can be "dark", "transparent" or "normal"
          sidebars = "dark", -- style for sidebars, see below
          floats = "dark", -- style for floating windows
        },
        day_brightness = 0.3, -- Adjusts the brightness of the colors of the **Day** style. Number between 0 and 1, from dull to vibrant colors
        dim_inactive = false, -- dims inactive windows
        lualine_bold = false, -- When `true`, section headers in the lualine theme will be bold

        --- You can override specific color groups to use other groups or a hex color
        --- function will be called with a ColorScheme table
        ---@param colors ColorScheme
        on_colors = function(colors)
          colors.black = "#0c0e14"

          colors.bg_sidebar = "#0c0e14"
          colors.bg_float = "#0c0e14"
          colors.bg_popup = "#0c0e14"
          colors.bg_statusline = "#0c0e14"
          colors.comment = "#43455e"
          colors.bg_visual = "#232534"

          -- colors.red = "#f7768e"
          -- colors.red1 = "#ff8787"
          colors.green = "#5fffaf"
          -- colors.yellow = "#ffffaf"
          -- colors.teal = "#5fffd7"
          -- colors.orange = "#ffaf00"
          -- colors.blue0 = "#87ffff"
          -- colors.blue1 = "#afd7ff"
          -- colors.blue2 = "#5fd7ff"
          -- colors.blue5 = "#00afff"
          -- colors.blue6 = "#0087ff"
          -- colors.blue7 = "#005fff"
          -- colors.magenta = "#d7afff"
          -- colors.magenta2 = "#af87ff"
          -- colors.cyan = "#5fffff"
          --
          -- colors.bg = "#13141f"
          -- colors.bg_dark = "#11131b"
          -- colors.bg_dark1 = "#0c0e14"
          --
          -- colors.fg = "#ebeef5"
          -- colors.fg_dark = "#bbc7e2"
          -- colors.fg_gutter = "#343b52"
          --
          -- colors.dark3 = "#343b52"
          -- colors.dark5 = "#00FF00"

          colors.comment = "#52557c"
        end,

        --- You can override specific highlights to use other groups or a hex color
        --- function will be called with a Highlights and ColorScheme table
        ---@param highlights tokyonight.Highlights
        ---@param colors ColorScheme
        on_highlights = function(hl, c)
          hl.CursorLine = { bg = "#232534" }
          hl.Visual = { bg = "#232534" }
        end,

        cache = true, -- When set to true, the theme will be cached for better performance

        ---@type table<string, boolean|{enabled:boolean}>
        plugins = {
          -- enable all plugins when not using lazy.nvim
          -- set to false to manually enable/disable plugins
          all = package.loaded.lazy == nil,
          -- uses your plugin manager to automatically enable needed plugins
          -- currently only lazy.nvim is supported
          auto = true,
          -- add any plugins here that you want to enable
          -- for all possible plugins, see:
          --   * https://github.com/folke/tokyonight.nvim/tree/main/lua/tokyonight/groups
          -- telescope = true,
        },
      })
      vim.cmd("colorscheme tokyonight-night")
    end,
  },
}
