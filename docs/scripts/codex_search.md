# Codex search helper routes

`scripts/codex_search` is a direct Codex CLI helper. Its `--profile quick`
(default) uses `gpt-6-luna` with `xhigh` reasoning; `--profile research` uses
`gpt-6-sol` with `medium` reasoning. `codex_search --help` shows the current
profiles, permissions, and invocation examples.

The profile defaults can be changed with `CODEX_SEARCH_QUICK_MODEL`,
`CODEX_SEARCH_QUICK_REASONING`, `CODEX_SEARCH_RESEARCH_MODEL`, and
`CODEX_SEARCH_RESEARCH_REASONING`. `CODEX_SEARCH_MODEL` and
`CODEX_SEARCH_REASONING` override either profile for one invocation. Remaining
Codex CLI options are passed through literally.

The ompi Pi extension uses this helper but explicitly supplies its own model and
reasoning flags for every intent (`gpt-6-astra` at `medium` reasoning), so these
direct-helper defaults and environment overrides do not select Pi's extension
route. Consult ompi's README and background-tools context for its intent and
authorization boundaries. Updating this source script does not update previously
installed copies; deploy separately when ready.
