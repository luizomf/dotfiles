# Telescope file search

The existing `<leader>ff` (files) and `<leader>fg` (live grep) mappings search
from the current working directory; check it with `:pwd`. File search uses
ripgrep, which is already required for live grep and included in the setup.

Both pickers include hidden files without opting out of ripgrep's normal ignore
rules. They explicitly exclude these names at any directory depth:

- `.git`
- `.env` and `.env.*` (including examples/templates)
- `.venv`
- `node_modules`

These exclusions are passed to ripgrep rather than only filtering Telescope
results afterward. Other files ignored by `.gitignore` remain ignored; enabling
hidden files does not mean ignoring `.gitignore`. For example, a non-ignored
`tmux/.tmux.conf` is searchable.

The preview and existing layout remain unchanged. This is a search convenience,
not a security boundary: other pickers, open buffers, explicit file opens and
secrets stored under different names can still expose content.

## Verification

From the repository root:

```sh
nvim --clean --headless -i NONE -l tests/test_nvim_telescope_search.lua
```

Requires installed Telescope, Plenary and ripgrep. It opens the real file and
live-grep pickers against synthetic temporary files, checking hidden files,
root/nested exclusions and `.gitignore` handling. No real secrets are read.
Preview is disabled only in the headless test to avoid asynchronous preview
reads during teardown; verify it visually in a normal editor. No plugins or
tools are installed by the test.
