local M = {}

-- ┌──────────────────────────────────────────────────┐
-- │  Background / Foreground                         │
-- │  Deep indigo terrain + lavender text             │
-- └──────────────────────────────────────────────────┘
M.bg = "#0f0f14"
M.fg = "#eae8ff"

-- ┌──────────────────────────────────────────────────┐
-- │  Grays (blue-purple tinted, darkest → lightest)  │
-- └──────────────────────────────────────────────────┘
M.black = "#06060c"

M.gray_00 = "#08080f"
M.gray_01 = "#0a0a14"
M.gray_02 = "#14141e"
M.gray_03 = "#1c1c2a"
M.gray_04 = "#242436"
M.gray_05 = "#2c2c40"
M.gray_06 = "#36364c"
M.gray_07 = "#404058"
M.gray_08 = "#4c4c66"
M.gray_09 = "#565672"
M.gray_10 = "#60607e"
M.gray_11 = "#6a6a8a"
M.gray_12 = "#747496"
M.gray_13 = "#7e7ea0"
M.gray_14 = "#8686a8"
M.gray_15 = "#8e8eb0"
M.gray_16 = "#9696b8"
M.gray_17 = "#9e9ec0"
M.gray_18 = "#a4a4c4"
M.gray_19 = "#acacca"
M.gray_20 = "#b4b4d0"
M.gray_21 = "#b8b8d4"
M.gray_22 = "#c0c0da"
M.gray_23 = "#c8c8e2"
M.gray_24 = "#cecee8"
M.gray_25 = "#d2d2ec"
M.gray_26 = "#dadaf2"
M.gray_27 = "#e2e2f6"

M.white = "#f0efff"

-- Semantic alias
M.comment = M.gray_08

-- ┌─────────────────────────────────────────────┐
-- │  Reds / Pinks                               │
-- │  From the hot pink sky gradient             │
-- └─────────────────────────────────────────────┘
M.red = "#ff5f81" -- ANSI red (hot pink-red)
M.red_vivid = "#ff7e9a" -- intense (critical errors)
M.red_rose = "#ffa8bb" -- ANSI bright red (soft rose)

-- ┌─────────────────────────────────────────────┐
-- │  Oranges                                    │
-- └─────────────────────────────────────────────┘
M.orange = "#ff9060" -- coral
M.peach = "#ffb098" -- soft peach

-- ┌─────────────────────────────────────────────┐
-- │  Yellow                                     │
-- └─────────────────────────────────────────────┘
M.yellow = "#ffda76" -- ANSI yellow (warm gold)

-- ┌─────────────────────────────────────────────┐
-- │  Greens                                     │
-- │  Cyan-shifted greens from the alien flora   │
-- └─────────────────────────────────────────────┘
M.green = "#37feb7" -- ANSI green (emerald cyan-green)
M.green_light = "#72ffcd" -- ANSI bright green
M.green_mint = "#a0ffe0" -- mint

-- ┌──────────────────────────────────────────────────┐
-- │  Cyans / Teals                                   │
-- │  The glowing river, crystals and mushrooms       │
-- └──────────────────────────────────────────────────┘
M.cyan = "#30f4f2" -- ANSI cyan (neon teal)
M.teal = "#20d8d6" -- teal (borders, links)
M.teal_bright = "#a2fbfc" -- ANSI bright cyan
M.teal_dark = "#0a1820" -- dark teal (diff backgrounds)

-- ┌─────────────────────────────────────────────┐
-- │  Blues                                      │
-- │  Periwinkle/indigo from the planet          │
-- └─────────────────────────────────────────────┘
M.blue = "#88aaf2" -- ANSI blue (periwinkle)
M.blue_light = "#b2cbff" -- ANSI bright blue
M.blue_sky = "#78a0e8" -- soft sky blue
M.blue_soft = "#8890d8" -- soft purple-blue
M.blue_vivid = "#5070ff" -- vivid indigo
M.blue_deep = "#4838a0" -- deep indigo
M.aqua = "#60ffd8" -- bright aqua glow

-- ┌─────────────────────────────────────────────┐
-- │  Purples                                    │
-- │  The sky, the atmosphere, the vibe          │
-- └─────────────────────────────────────────────┘
M.purple = "#b080ff" -- purple
M.lavender = "#9898e0" -- lavender/periwinkle
M.purple_light = "#c8a0ff" -- light purple/lilac

-- ┌─────────────────────────────────────────────┐
-- │  Magentas                                   │
-- │  The pink-magenta sky gradient              │
-- └─────────────────────────────────────────────┘
M.magenta = "#ff87bc" -- ANSI magenta (pink)
M.magenta_vivid = "#ff88ef" -- ANSI bright magenta (hot)

return M
