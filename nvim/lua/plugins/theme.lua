return {
  {
    "folke/tokyonight.nvim",
    lazy = false,
    priority = 1000,
    config = function()
      local black = "#000000"
      local black1 = "#080808"
      local black2 = "#121212"
      local black3 = "#1c1c1c"
      local black4 = "#262626"
      local black5 = "#303030"
      local black6 = "#3a3a3a"
      local black7 = "#444444"
      local black8 = "#4e4e4e"
      local black9 = "#585858"
      local black10 = "#626262"

      local white = "#FFFFFF"
      local white1 = "#eeeeee"
      local white2 = "#e4e4e4"
      local white3 = "#dadada"
      local white4 = "#d0d0d0"
      local white5 = "#c6c6c6"
      local white6 = "#bcbcbc"
      local white7 = "#b2b2b2"
      local white8 = "#a8a8a8"
      local white9 = "#9e9e9e"
      local white10 = "#949494"

      local gray1 = "#6c6c6c"
      local gray2 = "#808080"
      local gray3 = "#949494"

      local red = "#ff8787"
      local red1 = "#ff5f5f"
      local red2 = "#ff5f87"
      local red3 = "#db4b4b"

      local green_pale = "#afffaf"
      local green_pale = "#afffaf"
      local green_pale = "#afffaf"
      local green_pale = "#afffaf"

      local green = "#87ffaf"
      local green1 = "#00ff87"
      local green2 = "#00ff5f"
      local green3 = "#00d787"

      local yellow = "#ffffaf"
      local yellow1 = "#ffff87"
      local yellow2 = "#ffff5f"
      local yellow3 = "#ffff00"

      local blue = "#afd7ff"
      local blue1 = "#87afff"
      local blue2 = "#5fafff"
      local blue3 = "#00afff"
      local blue4 = "#005fd7"
      local blue5 = "#005faf"
      local blue6 = "#0000d7"

      local purple = "#d7afff"
      local purple1 = "#af87ff"
      local purple2 = "#af5fff"
      local purple4 = "#875fff"

      local cyan = "#87ffff"
      local cyan1 = "#5fffff"
      local cyan2 = "#00ffff"
      local cyan3 = "#00d7d7"

      local orange = "#ffafaf"
      local orange1 = "#ffaf87"
      local orange2 = "#ffaf5f"
      local orange3 = "#ffaf00"

      require("tokyonight").setup({
        style = "night", -- The theme comes in three styles, `storm`, a darker variant `night` and `day`
        light_style = "day", -- The theme is used when the background is set to light
        transparent = false, -- Enable this to disable setting the background color
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
          colors.bg_sidebar = black
          colors.bg_float = black
          colors.bg_popup = black
          colors.bg_statusline = black

          colors.bg = black2
          colors.bg_dark = black3
          colors.bg_dark1 = black4

          colors.fg = white2
          colors.fg_dark = white8
          colors.fg_gutter = black6

          colors.dark3 = black8
          colors.dark5 = black10

          colors.comment = black8
          -- colors.bg_visual = black9

          colors.black = black

          colors.red = red
          colors.red1 = red1

          colors.green = green
          colors.green1 = green1
          colors.green2 = green2

          colors.blue = blue
          colors.blue0 = blue1
          colors.blue1 = blue2
          colors.blue2 = blue3

          colors.blue5 = cyan1
          colors.blue6 = cyan2
          colors.blue7 = blue6

          colors.magenta = purple
          colors.magenta2 = purple1
          colors.purple = purple2

          colors.yellow = yellow1
          colors.teal = cyan3
          colors.orange = orange1
          colors.cyan = cyan
        end,

        --- You can override specific highlights to use other groups or a hex color
        --- function will be called with a Highlights and ColorScheme table
        on_highlights = function(hl, c)
          hl.CursorLine = { bg = black2 }
          hl.Visual = { bg = black3 }
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
