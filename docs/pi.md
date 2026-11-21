# Pi Coding Agent configuration

Personal Pi configuration lives in `~/.pi/`, outside this public repository. The
installer does not install Pi or create its settings, instructions, or themes;
install it from <https://pi.dev>. The Pi utility wrappers in `scripts/` remain
part of the dotfiles.

[`synchosts`](scripts/synchosts.md) copies the Pi home between trusted hosts
(settings, instructions, themes, sessions, and resources), and
`synchosts --sync-auth` publishes its auth. Settings travel as a whole file with
mtime-based merging; there is no per-field merge. Never commit a copied Pi home
here.

Skills and extensions are maintained separately in
[omskills](https://github.com/luizomf/omskills) and
[ompi](https://github.com/luizomf/ompi).
