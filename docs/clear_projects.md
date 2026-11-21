# clear_projects

`scripts/clear_projects` permanently removes the contents of `.scratch` and
`release` in each immediate, non-hidden directory under `PROJECTS_DIR`, plus
`$HOME/dotfiles`. It preserves the `.scratch` and `release` directories
themselves. These names are treated as disposable; the script does not check
whether work is finished or releases have been published.

```bash
clear_projects --dry-run
clear_projects
```

`--dry-run` prints shell-escaped paths without deleting anything. The default
uses `rm -rf`, not the trash. There is no confirmation or undo.

After project cleanup, it prunes unused Docker build cache to 5 GB
(`docker buildx prune --all --force --max-used-space 5GB`) on the local default
context and builder only. Images, containers, and volumes are never removed.
Missing Docker or an old Buildx is skipped, a prune failure only warns, and dry
runs never invoke Docker.

## Safety and requirements

- Requires Bash (including macOS Bash 3.2) and `rm`; no Python or development
  environment is needed.
- `HOME` and `PROJECTS_DIR` must be nonempty existing directories. The projects
  root is resolved to a physical absolute path and must not be `/` or `HOME`.
  Always verify it points to the intended projects directory.
- Symlink roots, symlink project entries, and symlink `.scratch` or `release`
  targets are rejected or skipped. Intermediate root symlinks are resolved
  during physical-path normalization. Symlinks inside cleanup targets are
  removed, not followed by `rm`.
- Missing cleanup directories and nondirectory project entries are skipped.
  Empty targets are a no-op. Hidden contents are included.
- It does not guard against concurrent changes or mounts inside the targets:
  stop builds and other writers first.
- A failure stops the run; earlier deletions are not rolled back.

## Regression checks

```sh
python3 -m unittest tests.test_clear_projects
```

The suite runs the real command against temporary `HOME` and `PROJECTS_DIR`
fixtures with a fake Docker. The
[dotfiles pre-commit hook](scripts/check_staged.md) runs it when the command,
its tests, or the hook are staged.
