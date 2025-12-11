return {
  {
    "folke/tokyonight.nvim",
    lazy = false,
    priority = 1000,
    config = function()
      local black = "#000000"

      local bg = "#121212"
      local bg_dark = "#1c1c1c"
      local bg_dark1 = "#080808"
      local bg_highlight = "#262626"
      local bg_sidebar = "#121212"

      local blue = "#87afff"
      local blue0 = "#005faf"
      local blue1 = "#5fafff"
      local blue2 = "#5fafd7"

      local blue5 = "#87afff"
      local blue6 = "#afffff"
      local blue7 = "#5f5f87"

      local comment = "#585858"
      local cyan = "#87ffff"

      local dark3 = "#585858"
      local dark5 = "#767676"

      local fg = "#c6c6c6"
      local fg_sidebar = "#d7d7d7"
      local fg_dark = "#b2b2b2"
      local fg_float = "#c6c6c6"

      local fg_gutter = "#444444"

      local green = "#00ff87"
      local green1 = "#afffaf"
      local green2 = "#00af5f"

      local magenta = "#ffafff"
      local magenta2 = "#ff87ff"

      local red = "#ff8787"
      local red1 = "#ff5f5f"

      local purple = "#af87ff"
      local orange = "#ffaf87"
      local teal = "#87d7d7"
      local yellow = "#ffff87"

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
          colors.bg_highlight = bg_highlight
          colors.bg_sidebar = bg_sidebar

          colors.bg = bg
          colors.bg_dark = bg_dark
          colors.bg_dark1 = bg_dark1

          colors.dark3 = dark3
          colors.dark5 = dark5

          colors.fg = fg
          colors.fg_dark = fg_dark
          colors.fg_gutter = fg_gutter
          colors.fg_sidebar = fg_sidebar
          colors.fg_float = fg_float

          colors.dark3 = dark3
          colors.dark5 = dark5

          colors.comment = comment
          colors.black = black

          colors.error = red
          colors.warning = yellow
          colors.info = blue6
          colors.hint = blue5

          -- colors.border = ""
          -- colors.border_highlight = ""
          -- colors.bg_visual = ""

          colors.red = red
          colors.red1 = red1

          colors.green = green
          colors.green1 = green1
          colors.green2 = green2

          colors.blue = blue
          colors.blue0 = blue0
          colors.blue1 = blue1
          colors.blue2 = blue2

          colors.blue5 = blue5
          colors.blue6 = blue6
          colors.blue7 = blue7

          colors.magenta = magenta
          colors.magenta2 = magenta2
          colors.purple = purple

          colors.yellow = yellow
          colors.teal = teal
          colors.orange = orange
          colors.cyan = cyan
        end,

        --- You can override specific highlights to use other groups or a hex color
        --- function will be called with a Highlights and ColorScheme table
        on_highlights = function(hl)
          hl.CursorLine = { bg = bg_highlight }
          hl.Visual = { bg = bg_highlight }
          hl.ComplHint = { fg = comment }
          hl.DiagnosticUnnecessary = { fg = comment }
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
