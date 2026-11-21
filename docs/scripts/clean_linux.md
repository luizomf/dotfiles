# Linux cache cleanup

`clean_linux` removes a small, explicit set of rebuildable user caches. It was
written for LFS with Linuxbrew. Run it as the normal user, with package
managers, builds and editors closed. Requires Bash, GNU coreutils
(`rm --one-file-system`), and util-linux `findmnt`; `--system` additionally
requires systemd. LFS, Fedora and similar GNU/Linux installations provide these
tools; minimal BusyBox-only systems need them installed separately.

```sh
clean_linux                         # plan only; no cleanup commands execute
clean_linux --system --trim          # preview the full plan
clean_linux --apply --system --trim  # perform that plan
```

## Scope

- Trim unused **local Docker build cache** to a 5 GB budget when Docker and a
  compatible Buildx are available. This also removes recent cache when needed:
  repeated builds can fill a small disk within one day. Images, containers and
  volumes are never pruned. In-use/shared image layers can keep the reported
  total above 5 GB; later builds may need to rebuild/download cached inputs. The
  command pins the local `default` context and builder (ignoring `DOCKER_HOST`,
  `DOCKER_CONTEXT`, and `BUILDX_BUILDER`); remote or rootless contexts, missing
  Docker, and older Buildx are skipped.
- Run Homebrew `cleanup --prune=all` when available, with auto-update and
  automatic dependency removal disabled. Current installed tools remain; old
  versions and downloaded archives can be removed. Skip this command if its
  cache is missing, external (`XDG_CACHE_HOME`/`HOMEBREW_CACHE`), symlinked, or
  contains a mount. Pin the command to the inspected default cache path.
- Remove `~/.npm/_cacache`, `~/.npm/_logs`, and the `Homebrew`, `uv`, `pip`, and
  `nvim` subdirectories of `~/.cache`. Caches are rebuilt/downloaded on demand.
- Skip cache trees containing any mount, including nested same-filesystem bind
  mounts, and symlinked directories/ancestors. Non-default `XDG_CACHE_HOME` is
  not cleaned. Unknown cache directories are preserved, including `keepwarm`
  worker ownership state.
- `--system`: use passwordless sudo to run `systemd-tmpfiles --clean` with the
  host's age/preservation policy, then rotate and vacuum archived journals to
  seven days / 8 MiB. Active journal files are additional to that size limit.
  Old diagnostic history is permanently discarded.
- `--trim`: use passwordless sudo for `fstrim -av`, on all supported mounted
  filesystems. This advertises already unused blocks; it does not delete live
  files. Guest TRIM support does not guarantee immediate VM image shrinkage,
  especially when snapshots retain old blocks.

This does not delete histories, credentials, configurations, backups, project
build trees, installed Neovim plugins/Mason tools, system libraries, package
receipts, or unknown directories. It does not run `brew autoremove` or remove
packages that happen to have native equivalents. It does not recursively wipe
`/tmp`, `/var/tmp`, or all of `~/.cache`.

Without `--apply` it only prints the plan and cache sizes. Nothing is scheduled:
run `clean_linux --apply` when idle; the Docker budget applies per run. Applying
stops at the first failed command without rolling back. An unreadable mount
table aborts before cleanup. Do not run it alongside another cleaner or while
moving or mounting cache directories.

## Checks

```sh
python3 -m unittest tests.test_clean_linux
bash -n scripts/clean_linux
shellcheck scripts/clean_linux
```

Tests use temporary homes and intercepted commands; they perform no cleanup or
TRIM.
