# Linux cache cleanup

`clean_linux` removes a small, explicit set of rebuildable user caches. It was
created for LFS with Linuxbrew, not as a distro package uninstaller or system
optimizer. Run it as the normal user, with package managers, builds and editors
closed. Requires Bash, GNU coreutils (`rm --one-file-system`), and util-linux
`findmnt`; `--system` additionally requires systemd. LFS, Fedora and similar
GNU/Linux installations provide these tools; minimal BusyBox-only systems need
them installed separately.

```sh
clean_linux                         # plan only; no cleanup commands execute
clean_linux --system --trim          # preview the full plan
clean_linux --apply --system --trim  # perform that plan
```

## Scope

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

Default execution only prints the plan and measures existing caches. Applying
stops on cleanup-command failure; cleanup already completed is not rolled back.
Failure to read the mount table aborts before cleanup; unreadable cache paths
are skipped. Requested system-tool and sudo availability checks happen before
user-cache removal. No services are stopped automatically; run at an idle
moment. Do not run the script concurrently with another cleaner or move/mount
cache directories while it is running. The initial mount-table snapshot protects
existing mounts; GNU `rm --one-file-system` is an additional safeguard for
different filesystems. This is not a sandbox for concurrent/adversarial
filesystem changes.

## Checks

```sh
python3 -m unittest tests.test_clean_linux
bash -n scripts/clean_linux
shellcheck scripts/clean_linux
```

Tests use temporary homes and intercepted package/system commands; they perform
no system cleanup or TRIM. They check dry-run behavior, allowlisted deletion,
symlink/descendant-mount preservation, fail-closed mount inspection, external
Homebrew cache exclusions, and retention of unrelated data. On macOS the
deletion fixture adapts GNU rm's option to the local rm while keeping target
selection unchanged. A disposable LFS check also exercised real same-filesystem
bind mounts below both uv and Homebrew cache roots: neither tree was deleted and
Homebrew was not invoked. The full cleanup and TRIM path was exercised on an LFS
ARM64 guest; Fedora and other distros have not been directly exercised.
