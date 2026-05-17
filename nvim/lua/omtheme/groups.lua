local p = require("omtheme.palette")
local M = {}

M.set_groups = function()
  local hl = function(name, opts)
    vim.api.nvim_set_hl(0, name, opts)
  end

  -- ┌─────────────────────────────────────────────┐
  -- │  Base / Editor UI                           │
  -- └─────────────────────────────────────────────┘
  hl("Normal", { fg = p.gray_22, bg = p.bg })
  hl("NormalNC", { fg = p.gray_22, bg = p.gray_01 })
  hl("NormalSB", { fg = p.gray_24, bg = p.gray_01 })

  -- For blur and transparent background
  -- hl("Normal", { fg = p.gray_22, bg = "NONE" })
  -- hl("NormalNC", { fg = p.gray_22, bg = "NONE" })
  -- hl("NormalSB", { fg = p.gray_24, bg = "NONE" })

  hl("NonText", { fg = p.gray_02 })
  hl("Whitespace", { fg = p.gray_02 })
  hl("EndOfBuffer", { fg = p.gray_01 })
  hl("SpecialKey", { fg = p.gray_08 })
  hl("TermCursor", { reverse = true })
  hl("Cursor", { fg = p.gray_01, bg = p.gray_22 })
  hl("lCursor", { fg = p.gray_01, bg = p.gray_22 })
  hl("CursorIM", { fg = p.gray_01, bg = p.gray_22 })
  hl("MsgArea", { fg = p.gray_19 })
  hl("Conceal", { fg = p.gray_10 })
  hl("Directory", { fg = p.blue_light })

  -- ┌─────────────────────────────────────────────┐
  -- │  Cursor / Line / Column                     │
  -- └─────────────────────────────────────────────┘
  hl("CursorLine", { bg = p.gray_02 })
  hl("CursorColumn", { bg = p.gray_02 })
  hl("CursorLineNr", { bold = false, fg = p.magenta })
  hl("LineNr", { fg = p.comment, bg = p.bg })
  hl("ColorColumn", { bg = p.gray_02 })
  hl("VirtColumn", { link = "ColorColumn" })
  hl("SignColumn", { fg = p.gray_08 })
  hl("SignColumnSB", { fg = p.gray_06, bg = p.gray_01 })
  hl("FoldColumn", { fg = p.gray_08, bg = p.gray_01 })
  hl("Folded", { fg = p.blue_light, bg = p.gray_06 })

  -- ┌─────────────────────────────────────────────┐
  -- │  Search / Visual / Substitute               │
  -- └─────────────────────────────────────────────┘
  hl("Search", { fg = p.gray_22, bg = p.blue_deep })
  hl("IncSearch", { fg = p.black, bg = p.orange })
  hl("Visual", { bg = p.gray_04 })
  hl("VisualNOS", { bg = p.gray_04 })
  hl("Substitute", { fg = p.black, bg = p.red })

  -- ┌─────────────────────────────────────────────┐
  -- │  Status / Window / Tab                      │
  -- └─────────────────────────────────────────────┘
  hl("StatusLine", { fg = p.gray_24, bg = p.black })
  hl("StatusLineNC", { fg = p.gray_06, bg = p.black })
  hl("WinSeparator", { bold = true, fg = p.gray_02 })
  hl("VertSplit", { fg = p.gray_02 })
  hl("TabLine", { fg = p.gray_06, bg = p.black })
  hl("TabLineSel", { fg = p.gray_02, bg = p.blue_light })
  hl("TabLineFill", { bg = p.gray_01 })
  hl("Title", { bold = true, fg = p.blue_light })
  hl("WildMenu", { bg = p.gray_04 })

  -- ┌─────────────────────────────────────────────┐
  -- │  Messages                                   │
  -- └─────────────────────────────────────────────┘
  hl("ErrorMsg", { fg = p.red })
  hl("WarningMsg", { fg = p.yellow })
  hl("MoreMsg", { fg = p.blue_light })
  hl("ModeMsg", { bold = true, fg = p.gray_19 })
  hl("Question", { fg = p.blue_light })

  -- ┌─────────────────────────────────────────────┐
  -- │  Popup / Completion Menu                    │
  -- └─────────────────────────────────────────────┘
  hl("Pmenu", { fg = p.gray_22, bg = p.black })
  hl("PmenuSel", { bg = p.gray_03 })
  hl("PmenuMatch", { fg = p.blue, bg = p.black })
  hl("PmenuMatchSel", { fg = p.blue, bg = p.gray_03 })
  hl("PmenuSbar", { bg = p.black })
  hl("PmenuThumb", { bg = p.gray_06 })
  hl("QuickFixLine", { bold = true, bg = p.gray_03 })

  -- ┌─────────────────────────────────────────────┐
  -- │  Floating Windows                           │
  -- └─────────────────────────────────────────────┘
  hl("NormalFloat", { bg = p.black })
  hl("FloatBorder", { fg = p.teal, bg = p.black })
  hl("FloatTitle", { fg = p.teal, bg = p.black })
  hl("FloatShadow", { bg = p.gray_03, blend = 80 })
  hl("FloatShadowThrough", { bg = p.gray_03, blend = 100 })

  -- ┌─────────────────────────────────────────────┐
  -- │  Spell                                      │
  -- └─────────────────────────────────────────────┘
  hl("SpellBad", { underdashed = true, sp = p.gray_10 })
  hl("SpellCap", { undercurl = true, sp = p.yellow })
  hl("SpellRare", { undercurl = true, sp = p.blue_light })
  hl("SpellLocal", { undercurl = true, sp = p.blue_sky })

  -- ┌─────────────────────────────────────────────┐
  -- │  Diff                                       │
  -- └─────────────────────────────────────────────┘
  hl("DiffAdd", { bg = p.teal_dark })
  hl("DiffChange", { bg = p.gray_03 })
  hl("DiffDelete", { fg = p.red })
  hl("DiffText", { fg = p.blue_vivid })
  hl("Added", { fg = p.green })
  hl("Removed", { fg = p.red })
  hl("Changed", { fg = p.cyan })
  hl("diffAdded", { fg = p.teal_bright, bg = p.teal_dark })
  hl("diffRemoved", { fg = p.red_rose, bg = p.peach })
  hl("diffChanged", { fg = p.blue_soft, bg = p.gray_03 })
  hl("diffFile", { fg = p.blue_light })
  hl("diffLine", { fg = p.gray_08 })
  hl("diffIndexLine", { fg = p.magenta })
  hl("diffOldFile", { fg = p.blue, bg = p.peach })
  hl("diffNewFile", { fg = p.blue, bg = p.teal_dark })

  -- ┌─────────────────────────────────────────────┐
  -- │  Syntax: General                            │
  -- └─────────────────────────────────────────────┘
  hl("Comment", { italic = true, fg = p.comment })
  hl("String", { fg = p.green })
  hl("Character", { fg = p.green })
  hl("Constant", { fg = p.orange })
  hl("Identifier", { fg = p.magenta })
  hl("Statement", { fg = p.magenta })
  hl("Function", { fg = p.blue_light })
  hl("Keyword", { italic = true, fg = p.cyan })
  hl("Operator", { fg = p.blue_light })
  hl("PreProc", { fg = p.cyan })
  hl("Type", { fg = p.blue })
  hl("Special", { fg = p.blue })
  hl("Debug", { fg = p.orange })
  hl("Error", { fg = p.red, bold = true })
  hl("Todo", { fg = p.gray_01, bg = p.yellow })
  hl("Bold", { bold = true, fg = p.gray_22 })
  hl("Italic", { italic = true, fg = p.gray_22 })
  hl("Underlined", { underline = true })
  hl("MatchParen", { fg = p.orange, bold = true })

  -- ┌─────────────────────────────────────────────┐
  -- │  Treesitter: Syntax                         │
  -- └─────────────────────────────────────────────┘
  hl("@variable", { fg = p.gray_22 })
  hl("@variable.builtin", { fg = p.red })
  hl("@variable.parameter", { fg = p.yellow })
  hl("@variable.parameter.builtin", { fg = p.yellow })
  hl("@variable.member", { fg = p.aqua })
  hl("@module.builtin", { fg = p.red })
  hl("@label", { fg = p.blue_light })
  hl("@string.regexp", { fg = p.blue_sky })
  hl("@string.escape", { fg = p.magenta })
  hl("@string.documentation", { fg = p.yellow })
  hl("@type.builtin", { fg = p.blue })
  hl("@property", { fg = p.aqua })
  hl("@constructor", { fg = p.magenta })
  hl("@operator", { fg = p.blue_light })
  hl("@keyword", { italic = true, fg = p.purple })
  hl("@keyword.function", { fg = p.magenta })
  hl("@punctuation.bracket", { fg = p.gray_19 })
  hl("@punctuation.delimiter", { fg = p.blue_light })
  hl("@punctuation.special", { fg = p.blue_light })

  -- ┌─────────────────────────────────────────────┐
  -- │  Treesitter: Comments                       │
  -- └─────────────────────────────────────────────┘
  hl("@comment", { italic = true, fg = p.comment })
  hl("@comment.error", { fg = p.red })
  hl("@comment.warning", { fg = p.yellow })
  hl("@comment.note", { fg = p.blue_light })
  hl("@comment.todo", { fg = p.blue_soft })
  hl("@comment.hint", { fg = p.blue_light })
  hl("@comment.info", { fg = p.blue_sky })

  -- ┌─────────────────────────────────────────────┐
  -- │  Treesitter: Markup (Markdown / Vimdoc)     │
  -- └─────────────────────────────────────────────┘
  hl("@markup.strong", { bold = true })
  hl("@markup.italic", { italic = true })
  hl("@markup.emphasis", { italic = true })
  hl("@markup.strikethrough", { strikethrough = true })
  hl("@markup.underline", { underline = true })
  hl("@markup.link", { fg = p.teal })
  hl("@markup.list", { fg = p.blue_light })
  hl("@markup.list.checked", { fg = p.aqua })
  hl("@markup.list.unchecked", { fg = p.blue_light })
  hl("@markup.list.markdown", { bold = true, fg = p.orange })
  hl("@markup.raw.markdown_inline", { fg = p.blue_light })
  hl("@punctuation.special.markdown", { fg = p.orange })
  hl("@markup.heading.1.markdown", { bold = true, fg = p.blue_soft })
  hl("@markup.heading.2.markdown", { bold = true, fg = p.peach })
  hl("@markup.heading.3.markdown", { bold = true, fg = p.green_light })
  hl("@markup.heading.4.markdown", { bold = true, fg = p.green_mint })
  hl("@markup.heading.5.markdown", { bold = true, fg = p.purple })
  hl("@markup.heading.6.markdown", { bold = true, fg = p.purple_light })
  hl("@markup.heading.7.markdown", { bold = true, fg = p.orange })
  hl("@markup.heading.8.markdown", { bold = true, fg = p.red })
  hl("@markup.heading.1.delimiter.vimdoc", {
    underdouble = true,
    nocombine = true,
    sp = p.bg,
    bg = p.bg,
    fg = p.fg,
  })
  hl("@markup.heading.2.delimiter.vimdoc", {
    underline = true,
    nocombine = true,
    sp = p.bg,
    bg = p.bg,
    fg = p.fg,
  })

  -- ┌─────────────────────────────────────────────┐
  -- │  Treesitter: JSX / TSX                      │
  -- └─────────────────────────────────────────────┘
  hl("@tag.javascript", { fg = p.red })
  hl("@tag.tsx", { fg = p.red })
  hl("@tag.delimiter.tsx", { fg = p.blue_soft })
  hl("@constructor.tsx", { fg = p.blue })

  -- ┌─────────────────────────────────────────────┐
  -- │  LSP Highlights                             │
  -- └─────────────────────────────────────────────┘
  hl("LspCodeLens", { fg = p.comment })
  hl("LspInlayHint", { fg = p.comment, bg = p.gray_04 })
  hl("LspReferenceRead", { bg = p.gray_06 })
  hl("LspReferenceText", { bg = p.gray_06 })
  hl("LspReferenceWrite", { bg = p.gray_06 })
  hl("LspSignatureActiveParameter", { bold = true, bg = p.gray_05 })
  hl("LspInfoBorder", { fg = p.teal, bg = p.black })
  hl("@lsp.type.interface", { fg = p.blue_light })
  hl("@lsp.type.unresolvedReference", { undercurl = true, sp = p.red })
  hl("@lsp.typemod.typeAlias.defaultLibrary", { fg = p.blue })
  hl("@lsp.typemod.type.defaultLibrary", { fg = p.blue })

  -- ┌─────────────────────────────────────────────┐
  -- │  Diagnostics                                │
  -- └─────────────────────────────────────────────┘
  hl("DiagnosticError", { fg = p.red })
  hl("DiagnosticWarn", { fg = p.yellow })
  hl("DiagnosticInfo", { fg = p.blue_sky })
  hl("DiagnosticHint", { fg = p.blue_light })
  hl("DiagnosticOk", { fg = p.green })
  hl("DiagnosticUnnecessary", { fg = p.comment })
  hl("DiagnosticDeprecated", { strikethrough = true, sp = p.red })
  hl("DiagnosticVirtualTextError", { bg = p.gray_06 })
  hl("DiagnosticVirtualTextWarn", { fg = p.yellow, bg = p.gray_05 })
  hl("DiagnosticVirtualTextInfo", { fg = p.aqua, bg = p.gray_08 })
  hl("DiagnosticVirtualTextHint", { fg = p.blue_light, bg = p.gray_03 })
  hl("DiagnosticUnderlineError", { undercurl = true, sp = p.red })
  hl("DiagnosticUnderlineWarn", { undercurl = true, sp = p.yellow })
  hl("DiagnosticUnderlineInfo", { undercurl = true, sp = p.blue_sky })
  hl("DiagnosticUnderlineHint", { undercurl = true, sp = p.blue_light })
  hl("DiagnosticUnderlineOk", { underline = true, sp = p.green })
  hl("NvimInternalError", { fg = p.red, bg = p.red })

  -- ┌─────────────────────────────────────────────┐
  -- │  Telescope                                  │
  -- └─────────────────────────────────────────────┘
  hl("TelescopeNormal", { fg = p.gray_22, bg = p.black })
  hl("TelescopeBorder", { fg = p.gray_08, bg = p.black })
  hl("TelescopePromptTitle", { fg = p.gray_22, bg = p.black })
  hl("TelescopePromptBorder", { fg = p.gray_08, bg = p.black })
  hl("TelescopeResultsComment", { fg = p.comment })

  -- ┌─────────────────────────────────────────────┐
  -- │  Cmp (Completion)                           │
  -- └─────────────────────────────────────────────┘
  hl("CmpItemAbbr", { fg = p.gray_22 })
  hl("CmpItemAbbrDefault", { fg = p.gray_22 })
  hl("CmpItemAbbrDeprecated", { strikethrough = true, fg = p.gray_06 })
  hl("CmpItemAbbrDeprecatedDefault", { fg = p.gray_08 })
  hl("CmpItemAbbrMatch", { fg = p.blue })
  hl("CmpItemAbbrMatchFuzzy", { fg = p.blue })
  hl("CmpItemAbbrMatchDefault", { fg = p.gray_22 })
  hl("CmpItemAbbrMatchFuzzyDefault", { fg = p.gray_22 })
  hl("CmpItemMenu", { fg = p.comment })
  hl("CmpItemMenuDefault", { fg = p.gray_22 })
  hl("CmpItemKindDefault", { fg = p.blue })
  hl("CmpItemKindIconDefault", { fg = p.blue })
  hl("CmpItemKindCopilot", { fg = p.teal })
  hl("CmpItemKindSupermaven", { fg = p.teal })
  hl("CmpItemKindTabNine", { fg = p.teal })
  hl("CmpItemKindCodeium", { fg = p.teal })
  hl("CmpGhostText", { fg = p.blue_deep })
  hl("CmpDocumentation", { fg = p.gray_22, bg = p.black })
  hl("CmpDocumentationBorder", { fg = p.teal, bg = p.black })
  hl("ComplHint", { fg = p.comment })

  -- ┌─────────────────────────────────────────────┐
  -- │  Lazy.nvim                                  │
  -- └─────────────────────────────────────────────┘
  hl("LazyProgressDone", { bold = true, fg = p.magenta_vivid })
  hl("LazyProgressTodo", { bold = true, fg = p.gray_06 })

  -- ┌─────────────────────────────────────────────┐
  -- │  Debug                                      │
  -- └─────────────────────────────────────────────┘
  hl("debugPC", { bg = p.gray_01 })
  hl("debugBreakpoint", { fg = p.aqua, bg = p.gray_08 })
  hl("RedrawDebugNormal", { reverse = true })
  hl("RedrawDebugClear", { fg = p.black, bg = p.yellow })
  hl("RedrawDebugComposed", { bg = p.green })
  hl("RedrawDebugRecompose", { fg = p.black, bg = p.red })

  -- ┌─────────────────────────────────────────────┐
  -- │  Health                                     │
  -- └─────────────────────────────────────────────┘
  hl("healthError", { fg = p.red })
  hl("healthWarning", { fg = p.yellow })
  hl("healthSuccess", { fg = p.aqua })

  -- ┌─────────────────────────────────────────────┐
  -- │  HTML / Help                                │
  -- └─────────────────────────────────────────────┘
  hl("htmlH1", { bold = true, fg = p.magenta })
  hl("htmlH2", { bold = true, fg = p.blue_light })
  hl("helpCommand", { fg = p.blue_light, bg = p.blue_deep })
  hl("helpExample", { fg = p.comment })

  -- ┌─────────────────────────────────────────────┐
  -- │  Quickfix                                   │
  -- └─────────────────────────────────────────────┘
  hl("qfFileName", { fg = p.blue_light })
  hl("qfLineNr", { fg = p.gray_11 })

  -- ┌─────────────────────────────────────────────┐
  -- │  Misc                                       │
  -- └─────────────────────────────────────────────┘
  hl("Foo", { fg = p.gray_22, bg = p.magenta_vivid })
end

return M
