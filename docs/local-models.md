# Local Ollama models: defaults, catalogs, and runners

This is the cross-project maintenance map. Keep model catalogs, endpoint URLs,
machine configuration, and runtime selections local; never commit those files.
Service-specific implementation lives in
`~/.ollama/service/sync-model-catalogs.py`. Consult that script before running
it: its default mode also accesses another host.

## One shell default

[`zsh/config/env`](../zsh/config/env), loaded by `.zshenv`, owns the local shell
default:

```sh
export LOCAL_MODEL="${LOCAL_MODEL:-qwen3.8:27b-mlx}"
export LOCAL_MODEL_REASONING="${LOCAL_MODEL_REASONING:-high}"
export MODEL="${LOCAL_MODEL}"
```

Change the fallback in `LOCAL_MODEL` only. `MODEL` is a compatibility alias, not
another default to maintain. The deployed `~/.zshenv` may be a live symlink. An
already exported `LOCAL_MODEL` wins over the fallback, including in child
shells. For an existing terminal, explicitly export the new value and refresh
`MODEL`; merely sourcing the file preserves the old exported value.

`commit`, `ollama_os`, `ask`, `llm_clean`, `translate_ptbr`, and
`translate_ptbr_clean` consume `MODEL`; `test_models` consumes `LOCAL_MODEL`.
`OMNIVOICE_MODEL` is a separate TTS model.

Literal Pi/Codex model IDs, Omnews runner argv, named profiles, and fallback
chains do not expand `${LOCAL_MODEL}`; change them explicitly. Queue jobs, Bash
scripts, and containers do not load the Zsh environment, so pass `--model`
explicitly there.

## Consumer map

Paths are relative to the executing user's home unless noted. Check host/path
overrides before editing.

| Owner / path                                                                | What it controls                                                                    | How changes reach consumers                                                                                            |
| --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Ollama `/api/tags`, `/api/show`, `/api/ps`                                  | Installed IDs, advertised capabilities, native and loaded context                   | Metadata queries do not generate text; service/model options determine effective context                               |
| `~/.ollama/service/homebrew.mxcl.ollama.plist` and actual service overrides | Context and parallelism policy                                                      | Template values alone do not prove the running daemon's environment; Linux has its own service configuration           |
| `~/.pi/agent/models.json`                                                   | Host Pi model catalog, transport compatibility, reasoning, modalities, token limits | Pi reloads the catalog when opening `/model`; it does not automatically select the new model                           |
| `~/.pi/agent/settings.json`                                                 | Host Pi default provider/model                                                      | Separate from the Ollama shell default; do not replace a cloud default incidentally                                    |
| `~/.ollama/service/ollama_models.json`                                      | Codex/Ollama catalog                                                                | Referenced by Codex configuration and optionally mounted read-only into Sannux                                         |
| `~/.codex/config.toml`, `~/.codex/ollama-launch.config.toml`                | Host Codex provider, default/profile selections, catalog path                       | Inspect root and profiles; a named Qwen profile is not a generic default                                               |
| `~/.ollama/config.json` → `integrations`                                    | Model selections for `ollama launch` integrations                                   | Separate from catalog generation and shell defaults                                                                    |
| `$PROJECTS_DIR/sannux/templates/pi/.env` → `AGENT_HOME_PATH`                | Actual persistent Pi home                                                           | Default: `~/sannux-data/agent-homes/pi`; inspect the configured override without dumping secrets                       |
| `$AGENT_HOME_PATH/.pi/agent/models.json` and `settings.json`                | Sannux Pi catalog and defaults                                                      | `sannux_ephemeral pi` copies the persistent home into a private per-run home; editing host Pi alone does not update it |
| `$PROJECTS_DIR/sannux/templates/codex-ollama/.env`                          | Codex home and `CODEX_MODEL_CATALOG_HOST_PATH`                                      | Compose mounts the host catalog at `CODEX_MODEL_CATALOG_PATH`, normally `/opt/sannux/model_catalog.json`               |
| Codex-Ollama persistent home → `.codex/config.toml`                         | Container Codex root/profile model selections                                       | Default home: `~/sannux-data/agent-homes/codex-ollama`; ephemeral launches copy this config                            |
| `$PROJECTS_DIR/sannux/templates/claude-ollama/.env` → `ANTHROPIC_MODEL`     | Claude/Ollama selection                                                             | Separate explicit template selection; do not assume it follows `LOCAL_MODEL`                                           |
| Active Omnews SQLite `app_settings.runtime_config` → `ai.external_runners`  | Executable, literal model argv, timeout, tool-access declaration                    | Edit through Settings; summarization, curation, and briefing each select literal runner chains                         |
| `~/.config/omnews/config.toml`                                              | Legacy Omnews import                                                                | Not the current Settings authority; editing it does not update the active database                                     |
| Daily Paper `runners/run-pi-ephemeral.sh`                                   | Daily mounts/environment, then `sannux_ephemeral pi`                                | Forwards argv; uses the same persistent Pi catalog, not an independent image-baked catalog                             |
| Daily Paper `runners/queue-automatic-daily-paper-live.sh`                   | Scheduled editorial model selection                                                 | Explicit cloud-model pin; changing the local Ollama default must not replace it                                        |

`models.json` is not baked into the Pi image: new ephemeral runs copy the
persistent home, so a catalog update needs no image rebuild or resource refresh.
[`sannux_ephemeral --refresh-pi-resources`](../scripts/sannux_ephemeral)
refreshes extensions, skills, and helpers; it does not touch credentials or
model catalogs.

### Independent Sannux logins

The Pi container has two independent credentials: Pi's `.pi/agent/auth.json` and
the nested Codex helper's `.codex/auth.json`, logged in separately from the
standalone Codex container:

```sh
sannux compose pi run --rm --entrypoint codex agent login --device-auth
sannux compose pi run --rm -T --entrypoint codex agent login status
```

Ephemeral runs copy the persistent home, so a token refreshed during a run is
discarded with it. This is an accepted limitation.

`test_models` first runs `sannux_ephemeral --refresh-pi-resources`, then makes
real model requests on the host and in the Sannux homes (local Ollama models and
Claude Code `opus`, `sonnet`, `haiku`) and exits nonzero on any failure. Run it
with consumers idle. It does not log in.

### keepwarm

`keepwarm` is a single central worker. Every round pings each target on `m132`,
`m4128`, and `fedoraair` over SSH: host Claude Code (skipped on the daily
driver, whose macOS Keychain login is unreachable over SSH), Sannux Claude Code
(`haiku`, override with `KEEPWARM_CLAUDE_MODEL`), and Sannux Antigravity
(`gemini-3.8-flash-low`, 120-second print timeout). The OpenAI targets are
commented out in the script.

The `agy` ping passes its prompt in argv, not through `sannux_agy_stdin`: Gemini
may spend minutes on tools before a one-word reply, which stalls the serial
round. `sannux_agy_stdin` sends its stdin prompt as one
`--input-format stream-json` turn, prints only the final response, and exits
nonzero on an error or an early end such as `print_timeout`.

```sh
keepwarm --once  # Foreground round over all targets; nonzero if any request fails
keepwarm         # Replace the worker on this machine and start the hourly loop
```

Each hourly cycle runs two rounds 30 seconds apart. A new loop publishes an
ownership token in `~/.cache/keepwarm/current`; the previous worker exits after
its in-flight request. Run the loop on one machine only, and restart it after
updating the script: a running worker keeps its old functions. Do not use
`pkill -f keepwarm`. The log is `~/dotfiles/scripts/keepwarm.log` on that
machine.

## Capabilities and limits

Ollama's advertised capabilities (`/api/show`) and native context are not the
effective limits. Publish context as the minimum of native capacity, model
`num_ctx` when present, and the loaded context from `ollama ps`. Pi's
`maxTokens` is an output cap, not extra context.

`thinking` does not prove distinct reasoning levels, and `tools` does not prove
reliable tool selection or JSON-schema compliance. The local generator maps Pi
`off` → `none`, `minimal` → `low`, and `xhigh` → `max`; GPT-OSS uses a different
map. Omnews `has_tool_access` describes the runner contract, not `/api/show`.

## Change procedure — one machine at a time

1. **Identify the owner:** the actual Ollama endpoint, application database,
   runner argv, and Sannux home overrides. Do not change shared Daily runtime
   resources while its Queue jobs are active.
2. **Inspect metadata:** `ollama show <exact-id>` and `ollama ps` against the
   intended endpoint. Service templates do not prove the running configuration.
3. **Check the local catalogs** (review the installed script first):

   ```sh
   python3 ~/.ollama/service/sync-model-catalogs.py --skip-remote
   ```

   Exit 2 means stale catalogs; exit 1 means a validation error.

4. **Keep private rollback copies.** The generator rewrites the whole catalog,
   using the host Pi catalog as a template, and writes it to the default Sannux
   Pi home. Verify `AGENT_HOME_PATH` first.
5. **Apply locally:**

   ```sh
   python3 ~/.ollama/service/sync-model-catalogs.py --skip-remote --write
   python3 ~/.ollama/service/sync-model-catalogs.py --skip-remote
   ```

   Never omit `--skip-remote` for local-only work. The write changes catalogs
   **before** validating selections, so a nonzero exit can still mean files
   changed.

6. **Change selections separately:** `LOCAL_MODEL` for the shell default; for
   Omnews, the Settings runner's literal model argument (renaming a runner ID
   means updating every chain that references it).
7. **Verify propagation** in host Pi, Codex, and the actual Sannux home, then in
   a fresh container. Do not trigger Daily editorial work, publication, or
   scheduling as validation. Existing sessions and ephemeral homes keep old
   settings.

### Generator limits

The generator's reference check is not a complete runner audit. It recognizes
Omnews argv beginning with `pi` or `codex-ollama`; it misses a Pi wrapper whose
argv begins with `-p --model ...`. It also assumes the project's
`.omnews-data/omnews.db`, rather than discovering the deployed database via
`OMNEWS_DATA_DIR`/`OMNEWS_DB_PATH`. It does not validate every Pi settings file,
Claude template selection, Daily pin, image, or custom persistent-home override.
Check these consumers explicitly even when it reports success.

## Synchronization

[`synchosts`](scripts/synchosts.md) copies `~/.ollama/service/`, `~/.pi/`, and
`~/sannux-data/` between hosts. Generating catalogs and transferring them are
separate steps: update the local catalogs first, then sync. Sync merges by
modification time and does not propagate deletions; host `models.json` does not
populate Sannux's, and copying templates does not update Omnews Settings.
