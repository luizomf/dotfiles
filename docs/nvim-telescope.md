# Telescope file search

`<leader>ff` (files) and `<leader>fg` (live grep) search from the current
working directory (`:pwd`), both through ripgrep, with Telescope's default
sorters.

Both pickers include hidden files without opting out of ripgrep's normal ignore
rules. They explicitly exclude these names at any directory depth:

- `.git`
- `.env` and `.env.*` (including examples/templates)
- `.venv`
- `node_modules`

The exclusions go to ripgrep, and `.gitignore` still applies, so a non-ignored
`tmux/.tmux.conf` is searchable. This is a search convenience, not a security
boundary: other pickers and secrets under other names can still expose content.

## Verification

From the repository root:

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_telescope_search.lua
```

Requires Telescope, Plenary, and ripgrep; it uses synthetic files only.
