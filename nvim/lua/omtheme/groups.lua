local p = require("omtheme.palette")
local M = {}
M.set_groups = function()
  vim.api.nvim_set_hl(0, "Normal", { fg = p.fg, bg = p.bg })
  vim.api.nvim_set_hl(0, "Comment", { fg = p.comment, italic = true })
  vim.api.nvim_set_hl(0, "String", { fg = p.green })
  vim.api.nvim_set_hl(0, "Error", { fg = p.red, bold = true })
  vim.api.nvim_set_hl(0, "Function", { fg = p.blue })
  vim.api.nvim_set_hl(0, "SpecialKey", { fg = p.gray_08 })
  vim.api.nvim_set_hl(0, "EndOfBuffer", { fg = p.gray_01 })
  vim.api.nvim_set_hl(0, "TermCursor", { reverse = true })

  vim.api.nvim_set_hl(0, "NonText", { fg = p.gray_02 })
  vim.api.nvim_set_hl(0, "Whitespace", { fg = p.gray_02 })
  vim.api.nvim_set_hl(0, "CursorLineNr", { bold = false, fg = p.magenta })
  vim.api.nvim_set_hl(0, "CursorLine", { bg = p.gray_02 })
  vim.api.nvim_set_hl(0, "LineNr", { fg = p.comment, bg = p.bg })
  vim.api.nvim_set_hl(0, "VirtColumn", { link = "ColorColumn" })
  vim.api.nvim_set_hl(0, "ColorColumn", { bg = p.gray_02 })

  -- vim.api.nvim_set_hl(0, "LineNr", { fg = p.gray_03 })
  -- vim.api.nvim_set_hl(0, "LineNrAbove", { fg = p.gray_03 })
  -- vim.api.nvim_set_hl(0, "LineNrBelow", { fg = p.gray_03 })

  vim.api.nvim_set_hl(0, "Directory", { fg = p.blue })

  vim.api.nvim_set_hl(0, "Errorpalette.g", { fg = p.red })
  vim.api.nvim_set_hl(0, "IncSearch", { fg = p.black, bg = p.orange })
  vim.api.nvim_set_hl(0, "Search", { fg = p.gray_22, bg = p.blue3 })
  vim.api.nvim_set_hl(0, "palette.repalette.g", { fg = p.blue })
  vim.api.nvim_set_hl(0, "palette.depalette.g", { bold = true, fg = p.gray_19 })
  vim.api.nvim_set_hl(0, "Question", { fg = p.blue })

  vim.api.nvim_set_hl(0, "StatusLine", { fg = p.gray_24, bg = p.black })
  vim.api.nvim_set_hl(0, "StatusLineNC", { fg = p.gray_06, bg = p.black })
  vim.api.nvim_set_hl(0, "WinSeparator", { bold = true, fg = p.gray_02 })
  vim.api.nvim_set_hl(0, "VertSplit", { fg = p.gray_02 })
  vim.api.nvim_set_hl(0, "Title", { bold = true, fg = p.blue })
  vim.api.nvim_set_hl(0, "Visual", { bg = p.gray_04 })
  vim.api.nvim_set_hl(0, "Warningp.g", { fg = p.yellow })
  vim.api.nvim_set_hl(0, "Wildp.nu", { bg = p.gray_04 })
  vim.api.nvim_set_hl(0, "Folded", { fg = p.blue, bg = p.gray_06 })
  vim.api.nvim_set_hl(0, "FoldColumn", { fg = p.gray_08, bg = p.gray_01 })

  vim.api.nvim_set_hl(0, "DiffAdd", { bg = p.teal2 })
  vim.api.nvim_set_hl(0, "DiffChange", { bg = p.gray_03 })
  vim.api.nvim_set_hl(0, "DiffDelete", { fg = p.red })
  vim.api.nvim_set_hl(0, "DiffText", { fg = p.blue2 })
  vim.api.nvim_set_hl(0, "SignColumn", { fg = p.gray_08 })
  vim.api.nvim_set_hl(0, "Conceal", { fg = p.gray_10 })
  vim.api.nvim_set_hl(0, "SpellBad", { underdashed = true, sp = p.gray_10 })
  vim.api.nvim_set_hl(0, "SpellCap", { undercurl = true, sp = p.yellow })
  vim.api.nvim_set_hl(0, "SpellRare", { undercurl = true, sp = p.blue })
  vim.api.nvim_set_hl(0, "SpellLocal", { undercurl = true, sp = p.blue7 })

  vim.api.nvim_set_hl(0, "Pmenu", { fg = p.gray_22, bg = p.black })
  vim.api.nvim_set_hl(0, "PmenuSel", { bg = p.gray_03 })
  vim.api.nvim_set_hl(0, "PmenuMatch", { fg = p.blue1, bg = p.black })
  vim.api.nvim_set_hl(0, "PmenuMatchSel", { fg = p.blue1, bg = p.gray_03 })
  vim.api.nvim_set_hl(0, "PmenuSbar", { bg = p.black })
  vim.api.nvim_set_hl(0, "PmenuThumb", { bg = p.gray_06 })
  vim.api.nvim_set_hl(0, "TabLine", { fg = p.gray_06, bg = p.black })
  vim.api.nvim_set_hl(0, "TabLineSel", { fg = p.gray_02, bg = p.blue })
  vim.api.nvim_set_hl(0, "TabLineFill", { bg = p.gray_01 })
  vim.api.nvim_set_hl(0, "CursorColumn", { bg = p.gray_02 })

  vim.api.nvim_set_hl(0, "QuickFixLine", { bold = true, bg = p.gray_03 })
  vim.api.nvim_set_hl(0, "NormalNC", { fg = p.gray_22, bg = p.gray_01 })
  vim.api.nvim_set_hl(0, "NormalFloat", { bg = p.black })
  vim.api.nvim_set_hl(0, "MsgArea", { fg = p.gray_19 })
  vim.api.nvim_set_hl(0, "FloatBorder", { fg = p.teal, bg = p.black })
  vim.api.nvim_set_hl(0, "Cursor", { fg = p.gray_01, bg = p.gray_22 })
  vim.api.nvim_set_hl(0, "FloatTitle", { fg = p.teal, bg = p.black })

  vim.api.nvim_set_hl(0, "RedrawDebugNormal", { reverse = true })
  vim.api.nvim_set_hl(0, "Underlined", { underline = true })
  vim.api.nvim_set_hl(0, "lCursor", { fg = p.gray_01, bg = p.gray_22 })
  vim.api.nvim_set_hl(0, "CursorIM", { fg = p.gray_01, bg = p.gray_22 }) -- guifg=p.gray_01 guibg=p.gray_22
  vim.api.nvim_set_hl(0, "Substitute", { fg = p.black, bg = p.red }) -- guifg=p.black guibg=p.red
  vim.api.nvim_set_hl(0, "VisualNOS", { bg = p.gray_04 }) -- guibg=p.gray_04
  vim.api.nvim_set_hl(0, "Normal", { fg = p.gray_22, bg = p.gray_01 }) -- guifg=p.gray_22 guibg=p.gray_01
  vim.api.nvim_set_hl(0, "Character", { fg = p.green }) -- guifg=p.green
  vim.api.nvim_set_hl(0, "Constant", { fg = p.orange }) -- guifg=p.orange
  vim.api.nvim_set_hl(0, "Statement", { fg = p.magenta }) -- guifg=p.magenta

  vim.api.nvim_set_hl(0, "Keyword", { italic = true, fg = p.cyan }) -- cterm=italic gui=italic guifg=p.cyan
  vim.api.nvim_set_hl(0, "PreProc", { fg = p.cyan }) -- guifg=p.cyan
  vim.api.nvim_set_hl(0, "Type", { fg = p.blue1 }) -- guifg=p.blue1
  vim.api.nvim_set_hl(0, "Special", { fg = p.blue1 }) -- guifg=p.blue1
  vim.api.nvim_set_hl(0, "Debug", { fg = p.orange }) -- guifg=p.orange
  vim.api.nvim_set_hl(0, "LspCodeLens", { fg = p.gray_08 }) -- guifg=p.gray_08
  vim.api.nvim_set_hl(0, "LspInlayHint", { fg = p.gray_08, bg = p.gray_04 }) -- guifg=p.gray_08 guibg=p.gray_04
  vim.api.nvim_set_hl(0, "LspReferenceRead", { bg = p.gray_06 }) -- guibg=p.gray_06
  vim.api.nvim_set_hl(0, "LspReferenceText", { bg = p.gray_06 }) -- guibg=p.gray_06
  vim.api.nvim_set_hl(0, "LspReferenceWrite", { bg = p.gray_06 }) -- guibg=p.gray_06

  vim.api.nvim_set_hl(
    0,
    "LspSignatureActiveParameter",
    { bold = true, bg = p.gray_05 }
  )

  vim.api.nvim_set_hl(0, "DiagnosticError", { fg = p.red }) -- guifg=p.red
  vim.api.nvim_set_hl(0, "DiagnosticWarn", { fg = p.yellow }) -- guifg=p.yellow
  vim.api.nvim_set_hl(0, "DiagnosticInfo", { fg = p.blue7 }) -- guifg=p.blue7
  vim.api.nvim_set_hl(0, "DiagnosticHint", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "DiagnosticOk", { fg = p.green }) -- ctermfg=10 guifg=NvimLightGreen
  vim.api.nvim_set_hl(0, "DiagnosticVirtualTextError", { bg = p.gray_06 }) -- guifg=p.red guibg=p.gray6
  vim.api.nvim_set_hl(
    0,
    "DiagnosticVirtualTextWarn",
    { fg = p.yellow, bg = p.gray_05 }
  ) -- guifg=p.yellow guibg=p.gray_05
  vim.api.nvim_set_hl(
    0,
    "DiagnosticVirtualTextInfo",
    { fg = p.blue6, bg = p.gray_08 }
  ) -- guifg=p.blue6guibg=p.gray_8
  vim.api.nvim_set_hl(
    0,
    "DiagnosticVirtualTextHint",
    { fg = p.blue, bg = p.gray_03 }
  ) -- guifg=p.blue guibg=p.gray_3

  vim.api.nvim_set_hl(0, "DiagnosticUnnecessary", { fg = p.gray_08 }) -- guifg=p.gray_08
  vim.api.nvim_set_hl(0, "Comment", { italic = true, fg = p.gray_08 }) -- cterm=italic gui=italic guifg=p.gray_08
  vim.api.nvim_set_hl(0, "@variable", { fg = p.gray_22 }) -- guifg=p.gray_22
  vim.api.nvim_set_hl(0, "@variable.builtin", { fg = p.red }) -- guifg=p.red
  vim.api.nvim_set_hl(0, "@variable.parameter", { fg = p.yellow }) -- guifg=p.yellow
  vim.api.nvim_set_hl(0, "@variable.parameter.builtin", { fg = p.yellow }) -- guifg=p.yellow
  vim.api.nvim_set_hl(0, "@module.builtin", { fg = p.red }) -- guifg=p.red
  vim.api.nvim_set_hl(0, "@label", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "String", { fg = p.green }) -- guifg=p.green
  vim.api.nvim_set_hl(0, "@string.regexp", { fg = p.blue7 }) -- guifg=p.blue7

  vim.api.nvim_set_hl(0, "@string.escape", { fg = p.magenta }) -- guifg=p.magenta
  vim.api.nvim_set_hl(0, "@type.builtin", { fg = p.blue1 }) -- guifg=p.blue1
  vim.api.nvim_set_hl(0, "@property", { fg = p.blue6 }) -- guifg=p.blue6
  vim.api.nvim_set_hl(0, "Identifier", { fg = p.magenta }) -- guifg=p.magenta
  vim.api.nvim_set_hl(0, "Function", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "@constructor", { fg = p.magenta }) -- guifg=p.magenta
  vim.api.nvim_set_hl(0, "@operator", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "Operator", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "@keyword", { italic = true, fg = p.purple }) -- cterm=italic gui=italic guifg=p.purple
  vim.api.nvim_set_hl(0, "@punctuation.special", { fg = p.blue }) -- guifg=p.blue

  vim.api.nvim_set_hl(0, "@comment", { italic = true, fg = p.gray_08 }) -- cterm=italic gui=italic guifg=p.gray_08
  vim.api.nvim_set_hl(0, "@comment.error", { fg = p.red }) -- guifg=p.red
  vim.api.nvim_set_hl(0, "@comment.warning", { fg = p.yellow }) -- guifg=p.yellow
  vim.api.nvim_set_hl(0, "@comment.note", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "@comment.todo", { fg = p.blue5 }) -- guifg=p.blue5
  vim.api.nvim_set_hl(0, "Todo", { fg = p.gray_01, bg = p.yellow }) -- guifg=p.gray_01 guibg=p.yellow
  vim.api.nvim_set_hl(0, "@markup.strong", { bold = true }) -- cterm=bold gui=bold
  vim.api.nvim_set_hl(0, "@markup.italic", { italic = true }) -- cterm=italic gui=italic
  vim.api.nvim_set_hl(0, "@markup.strikethrough", { strikethrough = true }) -- cterm=strikethrough gui=strikethrough

  vim.api.nvim_set_hl(0, "@markup.underline", { underline = true }) -- cterm=underline gui=underline
  vim.api.nvim_set_hl(0, "@markup.link", { fg = p.teal }) -- guifg=p.teal
  vim.api.nvim_set_hl(0, "Added", { fg = p.green }) -- ctermfg=10 guifg=NvimLightGreen
  vim.api.nvim_set_hl(0, "Removed", { fg = p.red }) -- ctermfg=9 guifg=NvimLightRed
  vim.api.nvim_set_hl(0, "Changed", { fg = p.cyan }) -- ctermfg=14 guifg=NvimLightCyan
  vim.api.nvim_set_hl(
    0,
    "@markup.heading.1.delimiter.vimdoc",
    { underdouble = true, nocombine = true, sp = p.bg, bg = p.bg, fg = p.fg }
  ) -- cterm=underdouble,nocombine gui=underdouble,nocombine guifg=bg guibg=bg guisp=fg
  vim.api.nvim_set_hl(
    0,
    "@markup.heading.2.delimiter.vimdoc",
    { underline = true, nocombine = true, sp = p.bg, bg = p.bg, fg = p.fg }
  ) -- cterm=underline,nocombine gui=underline,nocombine guifg=bg guibg=bg guisp=fg

  vim.api.nvim_set_hl(0, "@lsp.type.interface", { fg = p.blue }) -- guifg=p.blue

  vim.api.nvim_set_hl(
    0,
    "DiagnosticDeprecated",
    { strikethrough = true, sp = p.red }
  ) -- cterm=strikethrough gui=strikethrough guisp=NvimLightRed
  vim.api.nvim_set_hl(0, "FloatShadow", { bg = p.gray_03, blend = 80 }) -- ctermbg=0 guibg=NvimDarkGrey4 blend=80
  vim.api.nvim_set_hl(0, "FloatShadowThrough", { bg = p.gray_03, blend = 100 }) -- ctermbg=0 guibg=NvimDarkGrey4 blend=100
  vim.api.nvim_set_hl(0, "p.tchParen", { fg = p.orange, bold = true }) -- cterm=bold gui=bold guifg=p.orange
  vim.api.nvim_set_hl(0, "RedrawDebugClear", { fg = p.black, bg = p.yellow }) -- ctermfg=0 ctermbg=11 guibg=NvimDarkYellow
  vim.api.nvim_set_hl(0, "RedrawDebugComposed", { bg = p.green }) -- ctermfg=0 ctermbg=10 guibg=NvimDarkGreen
  vim.api.nvim_set_hl(0, "RedrawDebugRecompose", { fg = p.black, bg = p.red }) -- ctermfg=0 ctermbg=9 guibg=NvimDarkRed

  vim.api.nvim_set_hl(0, "Error", { fg = p.red }) -- guifg=p.red
  vim.api.nvim_set_hl(
    0,
    "DiagnosticUnderlineError",
    { undercurl = true, sp = p.red }
  ) -- cterm=undercurl gui=undercurl guisp=p.red
  vim.api.nvim_set_hl(
    0,
    "DiagnosticUnderlineWarn",
    { undercurl = true, sp = p.yellow }
  ) -- cterm=undercurl gui=undercurl guisp=p.yellow
  vim.api.nvim_set_hl(
    0,
    "DiagnosticUnderlineInfo",
    { undercurl = true, sp = p.blue7 }
  ) -- cterm=undercurl gui=undercurl guisp=p.blue7
  vim.api.nvim_set_hl(
    0,
    "DiagnosticUnderlineHint",
    { undercurl = true, sp = p.blue }
  ) -- cterm=undercurl gui=undercurl guisp=p.blue
  vim.api.nvim_set_hl(
    0,
    "DiagnosticUnderlineOk",
    { underline = true, sp = p.green }
  ) -- cterm=underline gui=underline guisp=NvimLightGreen
  vim.api.nvim_set_hl(0, "NvimInternalError", { fg = p.red, bg = p.red }) -- ctermfg=9 ctermbg=9 guifg=Red guibg=Red
  vim.api.nvim_set_hl(0, "Bold", { bold = true, fg = p.gray_22 }) -- cterm=bold gui=bold guifg=p.gray_22
  vim.api.nvim_set_hl(0, "TelescopeResultsComment", { fg = p.gray_08 }) -- guifg=p.gray_08
  vim.api.nvim_set_hl(
    0,
    "TelescopePromptTitle",
    { fg = p.gray_22, bg = p.black }
  ) -- guifg=p.gray_22 guibg=p.black

  vim.api.nvim_set_hl(
    0,
    "TelescopePromptBorder",
    { fg = p.gray_08, bg = p.black }
  ) -- guifg=p.gray_08 guibg=p.black
  vim.api.nvim_set_hl(0, "TelescopeNormal", { fg = p.gray_22, bg = p.black }) -- guifg=p.gray_22 guibg=p.black
  vim.api.nvim_set_hl(0, "TelescopeBorder", { fg = p.gray_08, bg = p.black }) -- guifg=p.gray_08 guibg=p.black
  vim.api.nvim_set_hl(0, "ComplHint", { fg = p.gray_08 }) -- guifg=p.gray_08
  vim.api.nvim_set_hl(0, "@keyword.function", { fg = p.magenta }) -- guifg=p.magenta
  vim.api.nvim_set_hl(0, "healthError", { fg = p.red }) -- guifg=p.red
  vim.api.nvim_set_hl(0, "NormalSB", { fg = p.gray_24, bg = p.gray_01 }) -- guifg=p.gray_24 guibg=p.gray_01
  vim.api.nvim_set_hl(0, "diffAdded", { fg = p.teal0, bg = p.teal2 }) -- guifg=p.teal0 guibg=p.teal2

  vim.api.nvim_set_hl(0, "@markup.list", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "@markup.list.checked", { fg = p.blue6 }) -- guifg=p.blue6
  vim.api.nvim_set_hl(0, "CmpItemp.nu", { fg = p.gray_08 }) -- guifg=p.gray_08
  vim.api.nvim_set_hl(0, "diffOldFile", { fg = p.blue1, bg = p.orange2 }) -- guifg=p.blue1 guibg=p.orange2
  vim.api.nvim_set_hl(0, "diffRemoved", { fg = p.red2, bg = p.orange2 }) -- guifg=p.red2 guibg=p.orange2
  vim.api.nvim_set_hl(
    0,
    "@markup.heading.1.markdown",
    { bold = true, fg = p.blue5 }
  ) -- cterm=bold gui=bold guifg=p.blue5
  vim.api.nvim_set_hl(
    0,
    "@markup.heading.6.markdown",
    { bold = true, fg = p.purple2 }
  ) -- cterm=bold gui=bold guifg=p.purple2
  vim.api.nvim_set_hl(0, "CmpItemKindTabNine", { fg = p.teal }) -- guifg=p.teal
  vim.api.nvim_set_hl(0, "LspInfoBorder", { fg = p.teal, bg = p.black }) -- guifg=#p.teal guibg=p.black

  vim.api.nvim_set_hl(0, "healthWarning", { fg = p.yellow }) -- guifg=p.yellow
  vim.api.nvim_set_hl(0, "Foo", { fg = p.gray_22, bg = p.magenta2 }) -- guifg=p.gray_22 guibg=p.magenta2
  vim.api.nvim_set_hl(
    0,
    "@markup.heading.5.markdown",
    { bold = true, fg = p.purple }
  ) -- cterm=bold gui=bold guifg=p.purple
  vim.api.nvim_set_hl(0, "@comment.info", { fg = p.blue7 }) -- guifg=p.blue7
  vim.api.nvim_set_hl(0, "@tag.javascript", { fg = p.red }) -- guifg=p.red
  vim.api.nvim_set_hl(0, "@string.documentation", { fg = p.yellow }) -- guifg=p.yellow
  vim.api.nvim_set_hl(0, "@constructor.tsx", { fg = p.blue1 }) -- guifg=p.blue1

  vim.api.nvim_set_hl(
    0,
    "@markup.heading.8.markdown",
    { bold = true, fg = p.red }
  ) -- cterm=bold gui=bold guifg=p.red
  vim.api.nvim_set_hl(0, "@punctuation.delimiter", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "debugBreakpoint", { fg = p.blue6, bg = p.gray_08 }) -- guifg=p.blue6 guibg=p.gray_8
  vim.api.nvim_set_hl(
    0,
    "CmpDocumentationBorder",
    { fg = p.teal, bg = p.black }
  ) -- guifg=#p.teal guibg=p.black
  vim.api.nvim_set_hl(
    0,
    "@lsp.type.unresolvedReference",
    { undercurl = true, sp = p.red }
  ) -- cterm=undercurl gui=undercurl guisp=p.red

  vim.api.nvim_set_hl(0, "CmpItemAbbrp.tch", { fg = p.blue1 }) -- guifg=p.blue1
  vim.api.nvim_set_hl(0, "LazyProgressDone", { bold = true, fg = p.magenta2 }) -- cterm=bold gui=bold guifg=p.magenta2
  vim.api.nvim_set_hl(0, "@variable.member", { fg = p.blue6 }) -- guifg=p.blue6
  vim.api.nvim_set_hl(
    0,
    "@markup.heading.7.markdown",
    { bold = true, fg = p.orange }
  ) -- cterm=bold gui=bold guifg=p.orange

  vim.api.nvim_set_hl(0, "@punctuation.special.markdown", { fg = p.orange }) -- guifg=p.orange
  vim.api.nvim_set_hl(0, "helpCommand", { fg = p.blue, bg = p.blue3 }) -- guifg=p.blue guibg=p.blue3
  vim.api.nvim_set_hl(0, "htmlH2", { bold = true, fg = p.blue }) -- cterm=bold gui=bold guifg=p.blue
  vim.api.nvim_set_hl(0, "@markup.raw.markdown_inline", { fg = p.blue }) -- guifg=p.blue guibg=p.blue3

  vim.api.nvim_set_hl(
    0,
    "@markup.heading.3.markdown",
    { bold = true, fg = p.green1 }
  ) -- cterm=bold gui=bold guifg=p.green1
  vim.api.nvim_set_hl(0, "LazyProgressTodo", { bold = true, fg = p.gray_06 }) -- cterm=bold gui=bold guifg=p.gray_06
  vim.api.nvim_set_hl(0, "@punctuation.bracket", { fg = p.gray_19 }) -- guifg=p.gray_19
  vim.api.nvim_set_hl(0, "CmpItemKindDefault", { fg = p.blue1 }) -- guifg=p.blue1

  vim.api.nvim_set_hl(0, "@comment.hint", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "helpExample", { fg = p.gray_08 }) -- guifg=p.gray_08
  vim.api.nvim_set_hl(0, "qfFileName", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "@markup.list.unchecked", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "CmpItemKindCodeium", { fg = p.teal }) -- guifg=p.teal
  vim.api.nvim_set_hl(0, "CmpGhostText", { fg = p.blue3 }) -- guifg=p.blue3

  vim.api.nvim_set_hl(
    0,
    "CmpItemAbbrDeprecated",
    { strikethrough = true, fg = p.gray_06 }
  ) -- cterm=strikethrough gui=strikethrough guifg=p.gray_06
  vim.api.nvim_set_hl(0, "CmpItemKindCopilot", { fg = p.teal }) -- guifg=p.teal
  vim.api.nvim_set_hl(0, "CmpItemKindSupermaven", { fg = p.teal }) -- guifg=p.teal
  vim.api.nvim_set_hl(0, "CmpItemAbbr", { fg = p.gray_22 }) -- guifg=p.gray_22

  vim.api.nvim_set_hl(
    0,
    "@markup.heading.2.markdown",
    { bold = true, fg = p.orange2 }
  ) -- cterm=bold gui=bold guifg=p.orange2
  vim.api.nvim_set_hl(
    0,
    "@lsp.typemod.typeAlias.defaultLibrary",
    { fg = p.blue1 }
  ) -- guifg=p.blue1

  vim.api.nvim_set_hl(0, "@lsp.typemod.type.defaultLibrary", { fg = p.blue1 }) -- guifg=p.blue1

  vim.api.nvim_set_hl(0, "debugPC", { bg = p.gray_01 }) -- guibg=p.gray_01
  vim.api.nvim_set_hl(0, "qfLineNr", { fg = p.gray_11 }) -- guifg=p.gray_11
  vim.api.nvim_set_hl(
    0,
    "@markup.heading.4.markdown",
    { bold = true, fg = p.green2 }
  ) -- cterm=bold gui=bold guifg=p.green2
  vim.api.nvim_set_hl(0, "diffLine", { fg = p.gray_08 }) -- guifg=p.gray_08

  vim.api.nvim_set_hl(0, "diffFile", { fg = p.blue }) -- guifg=p.blue
  vim.api.nvim_set_hl(0, "SignColumnSB", { fg = p.gray_06, bg = p.gray_01 }) -- guifg=p.gray_06 guibg=p.gray_01
  vim.api.nvim_set_hl(0, "htmlH1", { bold = true, fg = p.magenta }) -- cterm=bold gui=bold guifg=p.magenta
  vim.api.nvim_set_hl(0, "healthSuccess", { fg = p.blue6 }) -- guifg=p.blue6
  vim.api.nvim_set_hl(0, "diffNewFile", { fg = p.blue1, bg = p.teal2 }) -- guifg=p.blue1 guibg=p.teal2
  vim.api.nvim_set_hl(0, "CmpDocumentation", { fg = p.gray_22, bg = p.black }) -- guifg=p.gray_22 guibg=p.black
  vim.api.nvim_set_hl(0, "@tag.tsx", { fg = p.red }) -- guifg=p.red
  vim.api.nvim_set_hl(0, "@tag.delimiter.tsx", { fg = p.blue5 }) -- guifg=p.blue5

  vim.api.nvim_set_hl(0, "Italic", { italic = true, fg = p.gray_22 }) -- cterm=italic gui=italic guifg=p.gray_22
  vim.api.nvim_set_hl(0, "@markup.emphasis", { italic = true }) -- cterm=italic gui=italic
  vim.api.nvim_set_hl(0, "CmpItemAbbrp.tchFuzzy", { fg = p.blue1 }) -- guifg=p.blue1
  vim.api.nvim_set_hl(0, "diffChanged", { fg = p.blue5, bg = p.gray_03 }) -- guifg=p.blue5 guibg=p.gray_03
  vim.api.nvim_set_hl(
    0,
    "@markup.list.markdown",
    { bold = true, fg = p.orange }
  ) -- cterm=bold gui=bold guifg=p.orange
  vim.api.nvim_set_hl(0, "diffIndexLine", { fg = p.magenta }) -- guifg=p.magenta
  vim.api.nvim_set_hl(0, "CmpItemAbbrDefault", { fg = p.gray_22 }) -- guifg=p.gray_22

  vim.api.nvim_set_hl(0, "CmpItemAbbrDeprecatedDefault", { fg = p.gray_08 }) -- guifg=p.gray_08
  vim.api.nvim_set_hl(0, "CmpItemAbbrp.tchDefault", { fg = p.gray_22 }) -- guifg=p.gray_22
  vim.api.nvim_set_hl(0, "CmpItemAbbrp.tchFuzzyDefault", { fg = p.gray_22 }) -- guifg=p.gray_22
  vim.api.nvim_set_hl(0, "CmpItemKindIconDefault", { fg = p.blue1 }) -- guifg=p.blue1
  vim.api.nvim_set_hl(0, "CmpItemp.nuDefault", { fg = p.gray_22 }) -- guifg=p.gray_22
end

return M
