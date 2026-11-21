# Neovim spelling assets

Language selection lives in [settings/spell.lua](../nvim/lua/settings/spell.lua)
and the spelling mappings in [keymaps.lua](../nvim/lua/keymaps.lua).

## File lookup

Neovim drops the region suffix when locating a dictionary: `pt_br` loads
`spell/pt.utf-8.spl`, and `en_us` loads `spell/en.utf-8.spl`
(`:help spell-load`). `:spellinfo` shows what actually loaded. A matching `.sug`
file is optional suggestion data (`:help spell-sug-file`).

Never add a dictionary or `.sug` file from an unchecked download: earlier
`pt_br` files here were HTML 404 pages. A replacement must be valid and, for
suggestion data, match its dictionary.

## Personal words

`spellfile` is unset, so `zg` writes personal words to
`stdpath("data")/site/spell/pt.utf-8.add` (with the current Portuguese-first
selection) and compiles its `.add.spl` there. Repository-local `.add` and
`.add.spl` files are gitignored; never commit the vocabulary.

## Manual verification

Use a fresh Neovim process after changing assets. With spelling enabled in a
writable text buffer:

- Correct: `coração`, `português`, `hello`, `world`.
- Misspelled: `portugês`, `helllo`; `z=` should offer `português` and `hello`.
