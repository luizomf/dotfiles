# Local Ollama models: defaults, catalogs, and runners

This is the cross-project maintenance map. Keep model catalogs, endpoint URLs,
machine configuration, and runtime selections local; never commit those files.
Service-specific implementation lives in
`~/.ollama/service/sync-model-catalogs.py`. Consult that script before running
it: its default mode also accesses another host.

## One shell default

[`zsh/.zshenv`](../zsh/.zshenv) owns the local shell default:

```sh
export LOCAL_MODEL="${LOCAL_MODEL:-muse-glimmer:30b-q4_K_M}"
export LOCAL_MODEL_REASONING="${LOCAL_MODEL_REASONING:-high}"
export MODEL="${LOCAL_MODEL}"
```

Change the fallback in `LOCAL_MODEL` only. `MODEL` is a compatibility alias, not
another default to maintain. The deployed `~/.zshenv` may be a live symlink. An
already exported `LOCAL_MODEL` wins over the fallback, including in child
shells. For an existing terminal, explicitly export the new value and refresh
`MODEL`; merely sourcing the file preserves the old exported value.

`commit`, `ollama_os`, `ask`, `llm_clean`, `translate_ptbr`,
`translate_ptbr_clean`, and `apply_persona` consume `MODEL`. Explicit command
arguments and legacy per-command `MODEL=...` overrides remain independent.
`test_models` consumes `LOCAL_MODEL`. It first runs
`sannux_ephemeral --refresh-pi-resources`, then makes real host/container model
calls (including Daily's launcher). The refresh prepares extensions, skills,
helpers and nested Codex auth, but **does not generate or synchronize model
catalogs**. Run it manually with consumers idle; it is not a static check or a
complete runner installer. `OMNIVOICE_MODEL` is a separate TTS model, not this
chat-model default.

This does not make every application's configuration environment-aware. Literal
Pi/Codex model IDs, Omnews runner argv, named profiles, and fallback chains must
not be replaced with `${LOCAL_MODEL}` unless their actual launcher implements
expansion. Queue, Bash scripts, and containers do not automatically load the
user's Zsh environment. Prefer an explicit `--model` from a verified launcher
environment for ad hoc local-model calls; keep deliberate task-specific pins and
cloud defaults intact.

## Consumer map

Paths below are relative to the executing user's home unless noted. Resolve
host/path overrides before editing; names alone do not prove the active owner.

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
| `~/.codex/automations/daily-paper-llm-roundup/`                             | Legacy Daily checkout/runner paths                                                  | Can remain a real directory, not a symlink. Inspect actual Omnews runner commands; do not assume all callers migrated  |

`models.json` is **not baked into the Pi image** in this launch path. A catalog
update normally needs neither an image rebuild nor a resource refresh. Existing
ephemeral homes retain their copied catalog; new runs copy the updated
persistent home. Do not modify active private run homes to force a switch.

[`sannux_ephemeral --refresh-pi-resources`](../scripts/sannux_ephemeral)
refreshes extensions, skills, helpers, and authentication-related resources. It
is not the model-catalog update command and should not be run merely to add a
model.

## Capabilities and limits

For `muse-glimmer:30b-q4_K_M`, the inspected daemon advertised:

- `completion`, `vision`, `tools`, and `thinking`;
- native context: **131072** tokens;
- no model-level `num_ctx` parameter in `/api/show`;
- loaded context from `ollama ps`: **60000** tokens.

These are observations, not permanent defaults. Recheck them after model/service
changes. Publish context as the minimum of native capacity, model `num_ctx` when
present, and verified service context. Do not advertise 131072 merely because it
is the native maximum. Pi's `maxTokens` is an output cap, not additional
context; the existing 32768 cap is a client policy, not a capability reported by
Ollama. Input, thinking, and output still share the effective context budget.

Pi should advertise text plus image input and reasoning for this model. Ollama's
`thinking` capability does **not** prove distinct low/medium/high/max behavior.
The local generator maps Pi `off` → `none`, `minimal` → `low`, and `xhigh` →
`max`; verify transport acceptance and actual semantics separately. GPT-OSS has
a different supported-level map. Do not apply its constraints to every model.

Likewise, `tools` does not prove reliable tool selection, JSON-schema
compliance, or parallel tool execution. Daemon request concurrency,
model-emitted parallel tool calls, and runner concurrency are separate concerns.
A configured `OLLAMA_NUM_PARALLEL` is not a successful concurrency benchmark.
Review runner concurrency/timeouts for a slower model, but do not increase them
blindly.

Skills are client instructions/resources, not Ollama model capabilities. Omnews
`has_tool_access` describes the runner contract, not just `/api/show`. Validate
tool behavior with isolated, non-destructive calls only when authorized.

## Change procedure — one machine at a time

1. **Identify the owner.** Check the actual Ollama endpoint, application
   instance/database, runner argv, Sannux template home overrides, and any
   legacy Daily paths. Read each affected project's change checklist. Before
   changing shared Daily runtime resources, obtain authorization for its
   read-only Queue/worker/marker ownership checks; defer conflicting changes
   while active.
2. **Inspect metadata without inference.** Use `ollama show <exact-id>` and
   `ollama ps` against the intended endpoint. Compare `/api/show` capabilities
   and context to the relevant catalog entries. Service templates are not
   runtime proof. Do not print complete environments, credentials, or
   application state.
3. **Check the local catalogs only.** After reviewing the installed script:

   ```sh
   python3 ~/.ollama/service/sync-model-catalogs.py --skip-remote
   ```

   Exit 2 means stale catalogs; exit 1 means a validation/error condition. This
   check queries all installed models and reads local consumer selections.

4. **Review the proposed scope and preserve rollback copies locally.** The
   generator updates the entire catalog, not just the selected model. It uses
   the host Pi catalog as a template and writes that result to the hardcoded
   default Sannux Pi home. Verify `AGENT_HOME_PATH` first; do not overwrite
   intentional consumer-specific providers or limits. Keep backups private.
5. **Apply locally only after the runtime checks permit it:**

   ```sh
   python3 ~/.ollama/service/sync-model-catalogs.py --skip-remote --write
   python3 ~/.ollama/service/sync-model-catalogs.py --skip-remote
   ```

   Never omit `--skip-remote` for local-only work. The write path changes
   catalogs **before** validating selections, so a nonzero exit can still mean
   files changed. Inspect results rather than blindly rerunning.

6. **Change the desired selection separately.** Update `LOCAL_MODEL` for the
   shell default. Review generic application defaults separately from named
   profiles and intentional fallbacks. For Omnews, edit the active Settings
   runner's literal model argument, not just its display name. Renaming runner
   IDs also requires updating all referencing chains. Use the project's required
   backup helper before any manual database mutation; do not edit a possibly
   stale local database to repair another machine's application.
7. **Verify propagation, not just valid JSON.** Check the new entry in host Pi,
   Codex, and the actual Sannux home; resolve the catalog mount. After
   authorization and ownership checks, use a fresh isolated container to verify
   model discovery and bounded tool/reasoning behavior. Do not trigger Daily
   editorial work, publication, resource refresh, service restart, or scheduling
   as validation.
8. **Report the boundary.** Separate catalog success from selections, live
   container checks, inference, and other machines. Existing sessions/ephemeral
   homes may retain old settings. Never equate a metadata check with next-run
   readiness.

### Current generator limits

The installed generator's reference check is not a complete runner audit. It
recognizes Omnews argv beginning with `pi` or `codex-ollama`; it misses a Pi
wrapper whose argv begins with `-p --model ...`. It also assumes the project's
`.omnews-data/omnews.db`, rather than discovering the deployed database via
`OMNEWS_DATA_DIR`/`OMNEWS_DB_PATH`. It does not validate every Pi settings file,
Claude template selection, Daily pin, image, or custom persistent-home override.
Check these consumers explicitly even when it reports success.

## Synchronization boundary

[`synchosts`](scripts/synchosts.md) transfers the whole `~/.ollama/service/`,
`~/.pi/`, and `~/sannux-data/` roots with shared exclusions, not a resource
allowlist. The linked page is the source of truth for the filters, backup
exception and optional caller-authoritative `--sync-auth` operation. The host
`~/.codex/` contributes only auth; Sannux's nested homes travel with that whole
root. Git metadata, ordinary DB files, Omnews `.omnews-data`, and ephemeral-run
directories remain excluded. Nothing is installed or built by these transfers.

Catalog **generation** and catalog **file transfer** remain separate. First
update the local catalogs as above, then explicitly synchronize when intended.
Copying a stale catalog or running `test_models` does not register a new model.
Normal data synchronization merges by modification time, not model-catalog
authority, and it does not propagate deletions. Inspect the result at each
consumer before treating it as current.

The host and Sannux catalog paths retain their separate namespaces: syncing host
`models.json` does not populate Sannux's `models.json` from it. Likewise,
copying project templates does not update Omnews runtime Settings. A local
check/update does not verify another host, its paths, or provider credentials.
