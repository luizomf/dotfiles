# Pi Coding Agent configuration

The installer links the tracked static configuration in `pi/agent/` into
`~/.pi/agent/`. Credentials, sessions, trust decisions, generated resources, and
machine-specific model settings remain local and must never be committed.

Skills and extensions are maintained separately in
[omskills](https://github.com/luizomf/omskills) and
[ompi](https://github.com/luizomf/ompi).

## Theme

`pi/agent/themes/omtheme.json` shares its foreground, ANSI accents, and
selection background with `omxterm/themes/omtheme.json`. The dim foreground uses
`brightBlack`, and the maximum-thinking indicator uses `brightMagenta`.

The formats differ, so these colors are copied rather than automatically synced.
Muted text and message/tool backgrounds remain Pi-specific to preserve readable
text and distinct blocks over the terminal's transparent background.
