#!/usr/bin/env python3
"""Save tmux structure and activate restored windows on demand (no daemon)."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid

REPO = Path(__file__).resolve().parents[2]


def default_socket():
    return (Path(os.environ.get('TMUX_TMPDIR', '/tmp')) / f'tmux-{os.getuid()}' / 'default').resolve()


def socket_path(explicit=None):
    inherited = os.environ.get('TMUX', '').rsplit(',', 2)[0]
    return Path(explicit or inherited or default_socket()).resolve()


def state_directory(socket):
    if os.environ.get('TMUX_LAZY_STATE_DIR'):
        return Path(os.environ['TMUX_LAZY_STATE_DIR']).expanduser()
    # A configured server owns its state path. Query the option rather than
    # exporting it into pane environments (which would leak into custom servers).
    binary = shutil.which('tmux')
    if binary and socket.exists():
        owner = subprocess.run([binary, '-S', str(socket), 'show-option', '-gqv', '@lazy_state_dir'],
                               text=True, capture_output=True, timeout=10)
        value = owner.stdout.removesuffix('\n')
        if owner.returncode == 0 and value:
            return Path(value)
    base = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'tmux/lazy'
    # Agent/test/custom servers must not overwrite the default server's snapshot.
    if socket != default_socket():
        base /= 'servers/' + hashlib.sha256(os.fsencode(socket)).hexdigest()[:16]
    return base


def literal_format(value):
    """Prevent literal paths from being interpreted as tmux format expressions."""
    return str(value).replace('#', '##')


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def validate_state(state):
    if not isinstance(state, dict) or state.get('version') != 1 or not state.get('sessions'):
        raise ValueError('Unsupported or empty lazy snapshot')
    if set(state) != {'version', 'sessions', 'focus'} or not isinstance(state['sessions'], list):
        raise ValueError('Unexpected snapshot fields')
    if not isinstance(state['focus'], dict) or set(state['focus']) != {'session', 'window'}:
        raise ValueError('Invalid saved focus')
    identities = set()
    for session in state['sessions']:
        if set(session) != {'uid', 'name', 'windows'} or not isinstance(session['windows'], list):
            raise ValueError('Invalid session record')
        for item in [session, *session['windows']]:
            if not isinstance(item['uid'], str) or not item['uid'] or item['uid'] in identities:
                raise ValueError('Snapshot identities must be nonempty and unique')
            identities.add(item['uid'])
            if not isinstance(item['name'], str) or any(c in item['name'] for c in '\t\r\n\0'):
                raise ValueError('Names containing tabs/newlines are not supported')
        if not session['windows'] or not session['name'] or ':' in session['name'] or '.' in session['name']:
            raise ValueError('Invalid session name or empty session')
        indices = set()
        for window in session['windows']:
            if set(window) != {'uid', 'index', 'name', 'active', 'zoom', 'layout', 'panes'}:
                raise ValueError('Invalid window record')
            if not isinstance(window['active'], bool) or not isinstance(window['zoom'], bool):
                raise ValueError('Invalid window active/zoom flags')
            index = window['index']
            if not isinstance(index, int) or index < 0 or index in indices or not window['panes']:
                raise ValueError('Invalid window index or empty window')
            indices.add(index)
            layout = window['layout']
            if not isinstance(layout, str) or (layout and not re.fullmatch(r'[0-9a-f]+,[0-9x,{}\[\]]+', layout)):
                raise ValueError('Invalid saved layout')
            for pane in window['panes']:
                if set(pane) != {'cwd', 'title', 'active'} or not isinstance(pane['active'], bool):
                    raise ValueError('Invalid pane record')
                cwd = pane['cwd']
                if not isinstance(cwd, dict) or set(cwd) not in ({'home'}, {'absolute'}):
                    raise ValueError('cwd must be explicitly home-relative or absolute')
                value = next(iter(cwd.values()))
                if not isinstance(value, str) or any(c in value for c in '\t\r\n\0'):
                    raise ValueError('cwd containing control characters is not supported')
                if 'home' in cwd and (Path(value).is_absolute() or '..' in Path(value).parts):
                    raise ValueError('Home-relative cwd must remain inside home')
                if 'absolute' in cwd and not Path(value).is_absolute():
                    raise ValueError('Absolute cwd must be absolute')
                if not isinstance(pane['title'], str) or any(c in pane['title'] for c in '\t\r\n'):
                    raise ValueError('Invalid pane title')
    return state


class LazyTmux:
    def __init__(self, directory, socket, home, shell, quiet=False):
        self.root = Path(directory).expanduser().resolve()
        self.socket = Path(socket).resolve()
        self.home = Path(home).resolve()
        self.shell = shell
        self.quiet = quiet
        self.state_file = self.root / 'state.json'
        self.env = dict(os.environ)
        for name in ('TMUX', 'TMUX_PANE', 'ENV', 'BASH_ENV'):
            self.env.pop(name, None)
        self.env['HOME'] = str(self.home)
        self.binary = shutil.which('tmux')
        if not self.binary:
            raise RuntimeError('tmux is required in PATH (prefer Homebrew)')
        if not Path(shell).is_absolute() or not os.access(shell, os.X_OK):
            raise ValueError('Select an executable absolute shell path with --shell')

    @contextmanager
    def locked(self):
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (self.root / 'state.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield

    def tmux(self, *args, configuration=None):
        command = [self.binary, '-S', str(self.socket)]
        if configuration is None:
            # A failed connection must not silently create a replacement server.
            command += ['-N', '-f', '/dev/null']
        else:
            command += ['-f', str(configuration)]
        result = subprocess.run([*command, *args], env=self.env, text=True, capture_output=True, timeout=30)
        if result.returncode:
            raise RuntimeError(f'tmux {args[0]}: {result.stderr.strip()}')
        return result.stdout.removesuffix('\n')

    def alive(self):
        if not self.socket.exists():
            return False
        try:
            owner = self.tmux('show-option', '-gqv', '@lazy_state_dir')
        except RuntimeError as exc:
            if 'no server running' in str(exc) or 'Connection refused' in str(exc):
                return False
            raise
        if owner and Path(owner).resolve() != self.root:
            raise RuntimeError('This server uses another lazy state directory; refusing to redirect it')
        return True

    def notify(self, message, *, in_tmux=False):
        if not self.quiet:
            if in_tmux:
                self.tmux('display-message', message)
            else:
                print(message)

    def encode_cwd(self, cwd):
        path = Path(cwd)
        try:
            return {'home': str(path.relative_to(self.home))}
        except ValueError:
            return {'absolute': str(path)}

    def decode_cwd(self, cwd):
        path = self.home / cwd['home'] if 'home' in cwd else Path(cwd['absolute'])
        if not path.is_dir():
            raise RuntimeError(f'Missing cwd; activation refused: {path}')
        return str(path)

    def panes(self, window=None):
        target = ['-t', window] if window else ['-a']
        fields = '#{pane_id}\t#{pane_pid}\t#{pane_current_path}\t#{@lazy_cwd}\t#{pane_active}'
        rows = [line.split('\t') for line in self.tmux('list-panes', *target, '-F', fields).splitlines()]
        if any(len(row) != 5 for row in rows):
            raise ValueError('Pane data contains unsupported tabs/newlines')
        return rows

    def load(self):
        return validate_state(json.loads(self.state_file.read_text()))

    def import_snapshot(self, snapshot):
        if self.state_file.exists():
            raise RuntimeError('A lazy snapshot already exists; refusing to overwrite it')
        sessions, panes = {}, {}
        selected = None
        for line in Path(snapshot).read_text().splitlines():
            f = line.split('\t')
            if f[0] == 'grouped_session':
                raise ValueError('Grouped sessions are not supported')
            if f[0] == 'pane':
                if len(f) != 11:
                    raise ValueError('Unsupported Resurrect pane record')
                panes.setdefault((f[1], int(f[2])), []).append(f)
            elif f[0] == 'window':
                if len(f) < 7:
                    raise ValueError('Unsupported Resurrect window record')
                session = sessions.setdefault(f[1], {'uid': str(uuid.uuid4()), 'name': f[1], 'windows': []})
                session['windows'].append({'uid': str(uuid.uuid4()), 'index': int(f[2]),
                                           'name': f[3].removeprefix(':'), 'active': f[4] == '1',
                                           'zoom': 'Z' in f[5], 'layout': f[6], 'panes': []})
            elif f[0] == 'state' and len(f) > 1:
                selected = f[1]
        for session in sessions.values():
            session['windows'].sort(key=lambda w: w['index'])
            for window in session['windows']:
                for p in sorted(panes.get((session['name'], window['index']), []), key=lambda p: int(p[5])):
                    raw = p[7].removeprefix(':')
                    if raw == '#{HOME}' or raw.startswith('#{HOME}/'):
                        cwd = {'home': raw[len('#{HOME}'):].lstrip('/') or '.'}
                    elif raw == '~' or raw.startswith('~/'):
                        cwd = {'home': raw[2:] or '.'}
                    else:
                        cwd = self.encode_cwd(raw)
                    window['panes'].append({'cwd': cwd, 'title': p[6], 'active': p[8] == '1'})
        if not sessions:
            raise ValueError('No sessions in the supplied snapshot')
        chosen = sessions.get(selected, next(iter(sessions.values())))
        window = next((w for w in chosen['windows'] if w['active']), chosen['windows'][0])
        state = {'version': 1, 'sessions': list(sessions.values()),
                 'focus': {'session': chosen['uid'], 'window': window['uid']}}
        atomic_json(self.state_file, validate_state(state))
        self.notify('Imported Resurrect structure; no saved process commands will be executed.')

    def command(self, action):
        # Quiet is per invocation: a quiet configure must not silence prefix C-s.
        return literal_format(shlex.join([sys.executable, str(Path(__file__).resolve()), '--state-dir', str(self.root),
                                          '--socket', str(self.socket), '--home', str(self.home), '--shell', self.shell, action]))

    def configure(self):
        if not self.alive():
            raise RuntimeError('No running tmux server to configure')
        self.tmux('set-option', '-g', '@lazy_state_dir', str(self.root))
        self.tmux('set-option', '-g', 'default-shell', self.shell)
        generation = self.tmux('show-option', '-gqv', '@lazy_generation') or str(uuid.uuid4())
        self.tmux('set-option', '-g', '@lazy_generation', generation)
        self.tmux('bind-key', 'C-s', 'run-shell', '-b', self.command('save'))
        self.tmux('bind-key', 'C-r', 'display-message', 'Lazy restore: save, stop the server when safe, then run tmux-lazy start')
        for hook in ('session-window-changed', 'client-session-changed', 'client-attached'):
            # Session IDs contain '$', so shell-single-quote the expanded IDs.
            command = self.command('visit') + " '#{window_id}' '#{session_id}' " + shlex.quote(generation)
            self.tmux('set-hook', '-g', hook + '[200]', 'run-shell -b ' + shlex.quote(command))

    def boot(self):
        if self.alive():
            # Reconfiguration/adoption never kills or restores into an existing server.
            self.configure()
            return
        version = re.search(r'(\d+)\.(\d+)', self.tmux('-V'))
        if not version or tuple(map(int, version.groups())) < (3, 5):
            raise RuntimeError('tmux >= 3.5 is required; prefer Homebrew tmux in PATH')
        if not self.state_file.exists():
            resurrect = self.home / '.local/share/tmux/resurrect/last'
            if self.socket == default_socket() and resurrect.is_file():
                self.import_snapshot(resurrect)
        self.socket.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        state = self.load() if self.state_file.exists() else None
        started = False
        try:
            # tmux reads -f only for a newly created server. A native creator may
            # win between alive() and start-server; only our startup-only token
            # proves that the bootstrap settings were applied to a server we made.
            token = str(uuid.uuid4())
            with tempfile.NamedTemporaryFile('w', prefix='startup-', suffix='.conf', dir=self.root) as config:
                config.write('set-option -s exit-empty off\n'
                             f'set-option -g @lazy_boot_owner {token}\n'
                             f'set-option -g @lazy_state_dir {shlex.quote(str(self.root))}\n'
                             'set-option -g default-shell /bin/sh\n'
                             'set-option -g remain-on-exit on\n'
                             'set-option -g base-index 1\n'
                             'set-option -g pane-base-index 1\n')
                config.flush()
                self.tmux('start-server', configuration=config.name)
            if self.tmux('show-option', '-gqv', '@lazy_boot_owner') != token:
                raise RuntimeError('Another tmux server started concurrently; left it unchanged. Attach or retry.')
            started = True
            self.tmux('new-session', '-d', '-s', '__lazy_bootstrap', '-x', '120', '-y', '40', '')
            self.tmux('set-option', '-s', 'exit-empty', 'on')
            if state:
                sid, wid = self.restore_structure(state)
            else:
                sid = self.tmux('new-session', '-d', '-s', 'HOME', '-c', literal_format(self.home), '-P', '-F', '#{session_id}',
                                'exec ' + shlex.quote(self.shell) + ' -l')
                wid = self.tmux('list-windows', '-t', sid, '-F', '#{window_id}')
            self.tmux('kill-session', '-t', '=__lazy_bootstrap')
            self.tmux('set-option', '-g', 'remain-on-exit', 'off')
            self.tmux('set-option', '-g', 'default-shell', self.shell)
            self.tmux('source-file', str(REPO / 'tmux/.tmux.conf'))
            self.configure()
            self.tmux('set-option', '-g', '@lazy_attach', sid)
            atomic_json(self.root / 'focus.json', {'session': self.uid(sid), 'window': self.uid(wid, True)})
            # Config errors precede real user shell startup. Missing cwd leaves a
            # visible pending window for correction/retry, never a silent fallback.
            try:
                self.activate(wid)
            except RuntimeError as exc:
                print(f'tmux-lazy: {exc}', file=sys.stderr)
        except BaseException:
            if started:
                print('tmux-lazy: restore incomplete; inspect the partial server before stopping it. '
                      'The saved snapshot was not replaced.', file=sys.stderr)
            raise

    def restore_structure(self, state):
        targets = {}
        focus_path = self.root / 'focus.json'
        focus = json.loads(focus_path.read_text()) if focus_path.exists() else state.get('focus', {})
        for session in state['sessions']:
            if session['name'] == '__lazy_bootstrap':
                raise ValueError('Reserved bootstrap session name in snapshot')
            dimensions = re.match(r'^[0-9a-f]+,(\d+)x(\d+),', session['windows'][0]['layout'])
            width, height = map(int, dimensions.groups()) if dimensions else (120, 40)
            sid = self.tmux('new-session', '-d', '-s', session['name'], '-x', str(width), '-y', str(height),
                            '-P', '-F', '#{session_id}', '')
            self.tmux('set-option', '-t', sid, '@lazy_uid', session['uid'])
            for number, window in enumerate(session['windows']):
                if number == 0:
                    wid = self.tmux('list-windows', '-t', sid, '-F', '#{window_id}')
                    if window['index'] != 1:
                        self.tmux('move-window', '-s', wid, '-t', f"{sid}:{window['index']}")
                else:
                    wid = self.tmux('new-window', '-d', '-t', f"{sid}:{window['index']}", '-P', '-F', '#{window_id}', '')
                match = re.match(r'^[0-9a-f]+,(\d+)x(\d+),', window['layout'])
                width, height = map(int, match.groups()) if match else (120, 40)
                self.tmux('resize-window', '-t', wid, '-x', str(max(width, len(window['panes']) * 4, 20)), '-y', str(max(height, 10)))
                bootstrap = self.panes(wid)[0][0]
                # Only split-window '' is genuinely process-free. Replace the
                # short-lived /bin/sh bootstrap we created, never a user pane.
                self.tmux('split-window', '-d', '-h', '-t', wid, '')
                self.tmux('kill-pane', '-t', bootstrap)
                for _ in window['panes'][1:]:
                    self.tmux('split-window', '-d', '-h', '-t', wid, '')
                    self.tmux('select-layout', '-t', wid, 'even-horizontal')
                self.tmux('select-layout', '-t', wid, window['layout'] or 'even-horizontal')
                self.tmux('rename-window', '-t', wid, window['name'])
                self.tmux('set-option', '-w', '-t', wid, '@lazy_uid', window['uid'])
                self.tmux('set-option', '-w', '-t', wid, '@lazy_pending', '1')
                rows = self.panes(wid)
                for row, pane in zip(rows, window['panes']):
                    self.tmux('set-option', '-p', '-t', row[0], '@lazy_cwd', json.dumps(pane['cwd']))
                    self.tmux('select-pane', '-t', row[0], '-T', pane['title'])
                active = next((r[0] for r, p in zip(rows, window['panes']) if p['active']), rows[0][0])
                self.tmux('select-pane', '-t', active)
                if window['zoom']:
                    self.tmux('resize-pane', '-Z', '-t', active)
                self.tmux('set-option', '-w', '-u', '-t', wid, 'window-size')
                targets[(session['uid'], window['uid'])] = (sid, wid)
            active_window = next((w for w in session['windows'] if w['active']), session['windows'][0])
            self.tmux('select-window', '-t', targets[(session['uid'], active_window['uid'])][1])
        saved_focus = state['focus']
        fallback = targets.get((saved_focus['session'], saved_focus['window']), next(iter(targets.values())))
        sid, wid = targets.get((focus.get('session'), focus.get('window')), fallback)
        self.tmux('select-window', '-t', wid)
        return sid, wid

    def activate(self, window):
        rows = [p for p in self.panes(window) if p[3]]
        directories = [self.decode_cwd(json.loads(p[3])) for p in rows]
        for row, cwd in zip(rows, directories):
            if row[1] not in ('', '0'):
                raise RuntimeError('Marked pane already has a process; refusing to replace it')
            self.tmux('respawn-pane', '-t', row[0], '-c', literal_format(cwd), 'exec ' + shlex.quote(self.shell) + ' -l')
            self.tmux('set-option', '-p', '-u', '-t', row[0], '@lazy_cwd')
        self.tmux('set-option', '-w', '-u', '-t', window, '@lazy_pending')
        # No success message here: display-message can freeze pane redraw.

    def uid(self, target, window=False):
        args = ['-w'] if window else []
        uid = self.tmux('show-option', *args, '-qv', '-t', target, '@lazy_uid')
        if not uid:
            uid = str(uuid.uuid4())
            self.tmux('set-option', *args, '-t', target, '@lazy_uid', uid)
        return uid

    def visit(self, window, session, generation):
        if not self.alive() or self.tmux('show-option', '-gqv', '@lazy_generation') != generation:
            return
        try:
            if window not in self.tmux('list-windows', '-a', '-F', '#{window_id}').splitlines():
                return
            if session not in self.tmux('list-sessions', '-F', '#{session_id}').splitlines():
                return
            if self.tmux('display-message', '-p', '-t', session, '#{window_id}') != window:
                return
            self.activate(window)
            atomic_json(self.root / 'focus.json', {'session': self.uid(session), 'window': self.uid(window, True)})
            self.tmux('set-option', '-g', '@lazy_attach', session)
        finally:
            if self.alive():
                self.tmux('wait-for', '-S', 'lazy-visit-complete')

    def save(self, if_running=False):
        if not self.alive():
            if if_running:
                return
            raise RuntimeError('No running tmux server to save')
        sessions = []
        for line in self.tmux('list-sessions', '-F', '#{session_id}\t#{session_name}\t#{session_grouped}').splitlines():
            sid, name, grouped = line.split('\t')
            if grouped == '1':
                raise ValueError('Grouped sessions are unsupported; previous snapshot left intact')
            session = {'uid': self.uid(sid), 'name': name, 'windows': []}
            fields = '#{window_id}\t#{window_index}\t#{window_name}\t#{window_layout}\t#{window_active}\t#{window_zoomed_flag}\t#{window_linked}'
            for line in self.tmux('list-windows', '-t', sid, '-F', fields).splitlines():
                wid, index, name, layout, active, zoom, linked = line.split('\t')
                if linked == '1':
                    raise ValueError('Linked windows are unsupported; previous snapshot left intact')
                panes = [{'cwd': json.loads(p[3]) if p[3] else self.encode_cwd(p[2]),
                          'title': self.tmux('display-message', '-p', '-t', p[0], '#{pane_title}'), 'active': p[4] == '1'}
                         for p in self.panes(wid)]
                session['windows'].append({'uid': self.uid(wid, True), 'index': int(index), 'name': name,
                                           'layout': layout, 'active': active == '1', 'zoom': zoom == '1', 'panes': panes})
            sessions.append(session)
        fallback = {'session': sessions[0]['uid'], 'window': sessions[0]['windows'][0]['uid']}
        focus = json.loads((self.root / 'focus.json').read_text()) if (self.root / 'focus.json').exists() else fallback
        atomic_json(self.state_file, validate_state({'version': 1, 'sessions': sessions, 'focus': focus}))
        self.notify('Tmux structure saved', in_tmux=True)

    def export(self, destination):
        state = self.load()
        # Only state.json crosses machines. Locks, focus and socket-specific data
        # stay local; home-relative cwd is already portable without substitutions.
        destination = Path(destination)
        destination.mkdir(mode=0o700, parents=True, exist_ok=False)
        atomic_json(destination / 'state.json', state)
        self.notify('Portable tmux snapshot exported')

    def status(self):
        if not self.alive():
            return {'running': False}
        panes = self.panes()
        return {'running': True, 'sessions': len(self.tmux('list-sessions', '-F', '#{session_id}').splitlines()),
                'windows': len(self.tmux('list-windows', '-a', '-F', '#{window_id}').splitlines()), 'panes': len(panes),
                'pending_panes': sum(bool(p[3]) for p in panes),
                'process_free_panes': sum(p[1] in ('', '0') for p in panes)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--socket', type=Path, help='Explicit socket; otherwise TMUX or the default socket')
    parser.add_argument('--state-dir', type=Path, help='Local JSON/lock directory (or TMUX_LAZY_STATE_DIR)')
    parser.add_argument('--home', type=Path, default=Path.home(), help=argparse.SUPPRESS)
    parser.add_argument('--shell', help='Login shell for new panes (otherwise the server/login shell)')
    quiet_help = 'Suppress confirmations; preserve errors, warnings and status JSON'
    parser.add_argument('--quiet', action='store_true', help=quiet_help)
    quiet_options = argparse.ArgumentParser(add_help=False)
    quiet_options.add_argument('--quiet', action='store_true', default=argparse.SUPPRESS, help=quiet_help)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('import', parents=[quiet_options]).add_argument('--snapshot', type=Path, required=True)
    for action in ('boot', 'start', 'configure', 'status'):
        sub.add_parser(action, parents=[quiet_options])
    sub.add_parser('save', parents=[quiet_options]).add_argument('--if-running', action='store_true')
    sub.add_parser('export', parents=[quiet_options]).add_argument('destination', type=Path)
    visit = sub.add_parser('visit', parents=[quiet_options])
    visit.add_argument('window')
    visit.add_argument('session')
    visit.add_argument('generation')
    sub.add_parser('stop', parents=[quiet_options]).add_argument('--yes', action='store_true', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    socket = socket_path(args.socket)
    shell = args.shell or os.environ.get('SHELL') or pwd.getpwuid(os.getuid()).pw_shell
    app = LazyTmux(args.state_dir or state_directory(socket), socket, args.home, shell, args.quiet)
    if args.action == 'start' and (os.environ.get('TMUX') or not os.isatty(0)):
        raise RuntimeError('Run start from a normal terminal outside tmux')
    with app.locked():
        # Another launcher may be constructing the server with /bin/sh. Resolve
        # implicit shell selection only after its startup lock has been released.
        if not args.shell and app.alive():
            app.shell = app.tmux('show-option', '-gqv', 'default-shell') or shell
        if args.action == 'import':
            app.import_snapshot(args.snapshot)
        elif args.action in ('boot', 'start'):
            app.boot()
        elif args.action == 'configure':
            app.configure()
        elif args.action == 'visit':
            app.visit(args.window, args.session, args.generation)
        elif args.action == 'save':
            app.save(args.if_running)
        elif args.action == 'export':
            app.export(args.destination)
        elif args.action == 'status':
            print(json.dumps(app.status()))
        elif args.action == 'stop' and app.alive():
            app.tmux('kill-server')
            app.notify('Tmux server stopped; only explicitly saved structure will return')
    if args.action == 'start':
        target = app.tmux('show-option', '-gqv', '@lazy_attach')
        command = [app.binary, '-S', str(socket)]
        if os.environ.get('TERM_PROGRAM') == 'OMXTerm':
            command += ['-T', 'sync']
        command += ['attach-session']
        sessions = app.tmux('list-sessions', '-F', '#{session_id}').splitlines()
        if target in sessions:
            command += ['-t', target]
        os.execvpe(app.binary, command, app.env)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f'tmux-lazy: {exc}', file=sys.stderr)
        if os.environ.get('TMUX'):
            subprocess.run(['tmux', 'display-message', '-l', f'tmux-lazy: {exc}'], check=False)
        sys.exit(1)
