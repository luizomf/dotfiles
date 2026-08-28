local M = {}

-- ┌──────────────────────────────────────────────────┐
-- │  Background / Foreground                         │
-- │  Deep indigo terrain + lavender text             │
-- └──────────────────────────────────────────────────┘
M.bg = "#000000" -- old #0f0f14
M.fg = "#f0f0ff" -- old #eae8ff

-- ┌──────────────────────────────────────────────────┐
-- │  Grays (blue-purple tinted, darkest → lightest)  │
-- └──────────────────────────────────────────────────┘
M.black = "#000000" -- old #06060c

M.gray_00 = "#08080f"
M.gray_01 = "#141418"
M.gray_02 = "#161620"
M.gray_03 = "#1c1c1f"
M.gray_04 = "#242428"
M.gray_05 = "#2c2c2f"
M.gray_06 = "#36363f"
M.gray_07 = "#40404f"
M.gray_08 = "#4c4c5c"
M.gray_09 = "#56565f"
M.gray_10 = "#606076"
M.gray_11 = "#6a6a80"
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

M.white = "#f0f0ff"

-- Semantic alias
M.comment = M.gray_08

-- ┌─────────────────────────────────────────────┐
-- │  Reds / Pinks                               │
-- │  From the hot pink sky gradient             │
-- └─────────────────────────────────────────────┘
M.red = "#f7718d" -- ANSI red (hot pink-red)
M.red_vivid = "#ffafc0" -- intense (critical errors)
M.red_rose = "#ffc1cf" -- ANSI bright red (soft rose)

-- ┌─────────────────────────────────────────────┐
-- │  Oranges                                    │
-- └─────────────────────────────────────────────┘
M.orange = "#ffab87" -- coral
M.peach = "#ffc0ad" -- soft peach

-- ┌─────────────────────────────────────────────┐
-- │  Yellow                                     │
-- └─────────────────────────────────────────────┘
M.yellow = "#ffdc95" -- ANSI yellow (warm gold)

-- ┌─────────────────────────────────────────────┐
-- │  Greens                                     │
-- │  Cyan-shifted greens from the alien flora   │
-- └─────────────────────────────────────────────┘
M.green = "#18ffc8" -- ANSI green (emerald cyan-green)
M.green_light = "#6fffdd" -- ANSI bright green
M.green_mint = "#96ffe6" -- mint

-- ┌──────────────────────────────────────────────────┐
-- │  Cyans / Teals (Accent)                          │
-- │  The glowing river, crystals and mushrooms       │
-- └──────────────────────────────────────────────────┘
-- M.cyan = "#30f4f2" -- (old accent) ANSI cyan (neon teal)

-- MAIN ACCENT COLOR
M.cyan = "#59d9ff" -- ANSI cyan (neon teal)
-- M.teal = "#20d8d6" -- teal (borders, links)
M.teal = "#81e2ff" -- teal (borders, links)
M.teal_bright = "#abecff" -- ANSI bright cyan
M.teal_dark = "#7fcee6" -- dark teal (diff backgrounds)

-- ┌─────────────────────────────────────────────┐
-- │  Blues                                      │
-- │  Periwinkle/indigo from the planet          │
-- └─────────────────────────────────────────────┘
M.blue = "#8fb1ff" -- ANSI blue (periwinkle)
M.blue_light = "#8fc3ff" -- ANSI bright blue
M.blue_sky = "#9eb7ff" -- soft sky blue
M.blue_soft = "#afd3ff" -- soft purple-blue
M.blue_vivid = "#5194ff" -- vivid indigo
M.blue_deep = "#5173ff" -- deep indigo
M.aqua = "#4fbdff" -- bright aqua glow

-- ┌─────────────────────────────────────────────┐
-- │  Purples                                    │
-- │  The sky, the atmosphere, the vibe          │
-- └─────────────────────────────────────────────┘
M.purple = "#c88bff" -- purple
M.lavender = "#b1a6ff" -- lavender/periwinkle
M.purple_light = "#d6b6ff" -- light purple/lilac

-- ┌─────────────────────────────────────────────┐
-- │  Magentas                                   │
-- │  The pink-magenta sky gradient              │
-- └─────────────────────────────────────────────┘
M.magenta = "#ff98f0" -- ANSI magenta (pink)
M.magenta_vivid = "#ffaff3" -- ANSI bright magenta (hot)

return M
