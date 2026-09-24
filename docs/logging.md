# Terminal logging commands

The standalone Bash commands in `scripts/` work without loading Zsh
configuration. The dotfiles Zsh setup already adds that directory to `PATH`.

| Command      | Label color | Stream |
| ------------ | ----------- | ------ |
| `loginfo`    | Blue        | stdout |
| `logsuccess` | Green       | stdout |
| `logwarn`    | Yellow      | stderr |
| `logerror`   | Red         | stderr |
| `logdebug`   | Cyan        | stderr |

```bash
loginfo 'Starting backup'
logsuccess 'Backup saved'
logwarn 'Using the default configuration'
logerror 'Could not connect'
logdebug 'Selected host:' "$host"
```

Each command prints a level label followed by all arguments joined with spaces
and a final newline. Arguments are literal message text, not options or `printf`
formats. With no arguments, only the label and a trailing space/newline are
printed. Debug messages are always printed; there is no log-level filter.

Only the label is colored, and only when its destination stream is a terminal. A
nonempty `NO_COLOR` or `TERM=dumb` disables color. Redirected output has no ANSI
color escapes added by these commands. Message contents are not sanitized.

All levels return success when printing succeeds: `logerror` reports an error
but does not exit the caller. Exit or return explicitly when needed. Each level
command starts Bash and replaces itself with the adjacent `logbase` script using
`exec`; neither script requires external utilities. Keep these commands and
`logbase` together when copying them. Bash 3.2 and newer are supported.

## Custom labels with `logbase`

```bash
logbase -t BUILD -f 6 -- 'Compiling files'
logbase -t NOTICE -f 0 -b 11 --open-tag '<' --close-tag '>' -- 'Check output'
logbase -- '--help is literal message text here'
```

`logbase` writes to stdout; use `>&2` for stderr. The terminal/color check
follows that redirection. Only a nonempty tag (including its delimiters) is
colored; without a tag, the command prints plain message text. Tag case is
preserved. With a tag, one space separates the label and message, including an
empty message. Without arguments, `logbase` prints a newline.

Options must precede the message; parsing stops at `--` or the first non-option
argument. Unknown options and missing values fail with usage on stderr. Palette
indices must be 1–3 decimal digits with a value from 0 to 255; leading zeros are
accepted. Foreground defaults to 7; background is unset. Configuration comes
from arguments, not ambient `TAG`, `TEXT`, or color variables. `NO_COLOR` and
`TERM` retain their meaning above. Use `logbase --help` for all options.

Run the focused regression checks with `bash tests/test_logging.sh`. Set
`BASH_BIN` to select the interpreter for direct test invocations; the
executables still resolve Bash through their `#!/usr/bin/env bash` shebang.

## Migration from Zsh functions

Start a new Zsh session to stop using the old in-memory logging functions.
Merely sourcing the edited function file does not remove definitions from an
existing shell. No live shell reload is performed by this change.

- Replace `logwarning` with `logwarn` and plain `log` calls with `loginfo`.
- `loginfo`, `logsuccess`, and `logerror` retain their names.
- All arguments are now printed, rather than only the first one.
- Labels replace emoji, and warnings/errors now use stderr.
- The former global color variables in `zsh/config/functions` are removed.

No generic `log` executable is installed, avoiding a collision with macOS `log`.
The installer's own logging functions remain separate and unchanged.
