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
- This is not a security boundary against concurrent filesystem changes or mount
  points inside cleanup targets. Stop builds and other writers before cleanup;
  do not use it on untrusted or mounted scratch trees.
- A failure stops the run; earlier deletions are not rolled back. The `ERR` trap
  reports the failing command where Bash supports it, not every expansion error.

No installer or shell reload is needed when using the existing scripts path.

## Regression checks

Run `python3 -m unittest tests.test_clear_projects` from the repository root.
The suite launches the real Bash command with isolated `HOME` and `PROJECTS_DIR`
fixtures in temporary directories. It checks actual deletion, preservation of
outside files, symlinks, hidden entries, empty reruns, invalid roots and dry
runs. The tests also verify that the hook blocks a simulated failing regression
suite.

The [dotfiles pre-commit hook](scripts/check_staged.md) runs this suite for
staged changes to the command, its tests or the hook. Python is a test
dependency, not a runtime dependency of `clear_projects`.
