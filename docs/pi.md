# Pi Coding Agent configuration

Personal Pi configuration lives in `~/.pi/`, outside this public repository. The
installer does not create or link Pi settings, instructions, or themes. The Pi
package and utility wrappers remain part of the dotfiles tooling.

[`synchosts`](scripts/synchosts.md) transfers the existing Pi home between
trusted hosts, including settings, instructions, themes, sessions, and
resources, subject to its existing exclusions. Use `synchosts --sync-auth` for
the existing caller-authoritative auth flow, including nested Sannux agent
homes. This change does not alter that policy or require fresh logins.

Skills and extensions are maintained separately in
[omskills](https://github.com/luizomf/omskills) and
[ompi](https://github.com/luizomf/ompi).

## Migrating an existing installation

Before updating an old checkout that contains `pi/agent/`, replace its four
symlinks under `~/.pi/agent/` with regular files containing their current
contents:

- `AGENTS.md`;
- `RTK.md`;
- `settings.json`;
- `themes/omtheme.json`.

Back up and verify each host's contents before removing the link targets from
its checkout. Preserve local changes; do not replace settings with a Git copy.
Do this on every existing host before running `synchosts`: its Git-update step
runs before data collection, and rsync preserves symlinks rather than resolving
them. Fresh hosts should receive regular files from an already-migrated peer.

Settings travel as a whole file, including identifiers written by Pi; there is
no per-field merge or host-local override added here. Normal synchronization
retains its existing mtime-based behavior. Do not commit a copied Pi home back
into this repository. Removing files from the current tree does not erase their
previous versions from Git history.
