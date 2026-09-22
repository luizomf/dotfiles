# Neovim spelling assets

Language selection lives in [settings/spell.lua](../nvim/lua/settings/spell.lua)
and the spelling mappings in [keymaps.lua](../nvim/lua/keymaps.lua). Keep those
preferences separate from dictionary maintenance.

## File lookup

Neovim removes the region suffix when locating a dictionary: `pt_br` loads
`spell/pt.utf-8.spl`, just as `en_us` loads `spell/en.utf-8.spl`. See
`:help spell-load`. `:spellinfo` shows the dictionaries actually loaded and any
embedded metadata. The bundled Portuguese dictionary identifies itself as
Brazilian Portuguese; this cleanup does not update its word list.

A matching `.sug` file is optional suggestion data, not the main dictionary. See
`:help spell-sug-file`. The removed `pt_br.utf-8.spl`, `pt_br.utf-8.sug` and
`pt.utf-8.sug` were HTML 404 responses, not usable spelling assets. Do not
restore them from an unchecked download. Any future replacement must have valid
contents and, for suggestion data, match its dictionary.

The valid Portuguese/English dictionaries, English suggestion data and existing
personal additions were left unchanged. Personal-word storage still needs its
own local-only path review; do not publish words or generated personal data as
part of dictionary maintenance.

## Manual verification

Use a fresh Neovim process after changing assets: loaded spelling data is
cached. In a normal writable text buffer, check these examples with spelling
enabled:

- Correct: `coração`, `português`, `hello`, `world`.
- Misspelled: `portugês`, `helllo`.
- On each misspelling, `z=` should offer `português` or `hello`, respectively.

A native headless probe passed these checks before and after removing the HTML
files, with identical suggestion lists for those two typos. This verifies the
sample behavior, not dictionary completeness or current orthographic coverage.
