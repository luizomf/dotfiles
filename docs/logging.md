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
but does not exit the caller. Exit or return explicitly when needed. Each
invocation starts a Bash process, but the command itself uses only builtins.

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
