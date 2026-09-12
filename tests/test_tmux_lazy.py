"""Real tmux integration on private sockets; never touch an existing server."""
import json
import os
from pathlib import Path
import pty
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / 'tmux/scripts/lazy.py'


@unittest.skipUnless(shutil.which('tmux'), 'tmux is required')
class LazyTmuxTests(unittest.TestCase):
    def test_import_visit_save_and_restart_preserve_pending_and_running_windows(self):
        with tempfile.TemporaryDirectory(prefix='lazy-demo-test-') as temporary:
            root = Path(temporary).resolve()
            home = root / 'home'
            (home / 'one').mkdir(parents=True)
            (home / 'two').mkdir()
            (home / 'dotfiles').symlink_to(REPO, target_is_directory=True)
            trial = root / 'trial'
            fixture = root / 'snapshot.txt'
            fixture.write_text('\n'.join([
                f'pane\talpha\t1\t1\t:*\t1\tfirst\t:{home}/one\t1\tzsh\t:',
                f'pane\talpha\t2\t0\t:\t1\tsecond\t:{home}/two\t1\tzsh\t:',
                f'pane\tbeta\t1\t1\t:*\t1\tthird\t:{home}/one\t1\tzsh\t:',
                'window\talpha\t1\t:code\t1\t:*\t\t:',
                'window\talpha\t2\t:terminal\t0\t:\t\t:',
                'window\tbeta\t1\t:code\t1\t:*\t\t:',
                'state\talpha\tbeta',
            ]) + '\n')
            cli = [sys.executable, str(SCRIPT), '--state-dir', str(trial), '--socket', str(trial / 'socket'),
                   '--home', str(home), '--shell', '/bin/sh']
            env = dict(os.environ)
            env.pop('TMUX', None)
            env.pop('TMUX_PANE', None)
            env['TERM'] = 'xterm-256color'

            def run(*args):
                result = subprocess.run([*cli, *args], env=env, text=True, capture_output=True, timeout=30)
                if result.returncode:
                    self.fail(f'{args[0]} failed: {result.stderr}\n{result.stdout}')
                return result.stdout

            def tmux(*args):
                return subprocess.run(['tmux', '-S', str(trial / 'socket'), *args], env=env,
                                      text=True, capture_output=True, check=True, timeout=15).stdout.strip()

            try:
                run('import', '--snapshot', str(fixture))
                run('boot')
                initial = json.loads(run('status'))
                self.assertEqual((initial['sessions'], initial['windows'], initial['pending_panes']), (2, 3, 2))
                pid = tmux('display-message', '-p', '-t', 'alpha:1', '#{pane_pid}')
                tmux('select-window', '-t', 'alpha:2')
                tmux('wait-for', 'lazy-visit-complete')
                self.assertEqual(json.loads(run('status'))['pending_panes'], 1)
                self.assertTrue((trial / 'focus.json').exists())
                self.assertEqual(tmux('display-message', '-p', '-t', 'alpha:1', '#{pane_pid}'), pid)
                tmux('rename-window', '-t', 'alpha:2', 'renamed')
                run('save')
                data = json.loads((trial / 'state.json').read_text())
                self.assertEqual(data['sessions'][0]['windows'][1]['name'], 'renamed')
                self.assertEqual(data['sessions'][1]['windows'][0]['panes'][0]['cwd'], {'home': 'one'})
                run('stop', '--yes')
                run('boot')
                self.assertEqual(json.loads(run('status'))['pending_panes'], 2)
                self.assertEqual(tmux('display-message', '-p', '-t', 'alpha:', '#{window_name}'), 'renamed',
                                 {'saved_focus': data['focus'], 'current_focus': json.loads((trial / 'focus.json').read_text()),
                                  'saved_windows': [(s['name'], s['uid'], [(w['name'], w['uid'], w['active']) for w in s['windows']]) for s in data['sessions']]})
                self.assertEqual(tmux('display-message', '-p', '-t', 'alpha:2', '#{pane_current_path}'), str(home / 'two'))
                self.assertEqual(tmux('show-option', '-gqv', '@continuum-restore'), 'off')
                bindings = tmux('list-keys', '-T', 'prefix').splitlines()
                self.assertTrue(any('C-s ' in line and 'lazy.py' in line for line in bindings), bindings)
                ready_fifo = root / 'render-ready'
                os.mkfifo(ready_fifo)
                shell = root / 'render-shell'
                shell.write_text('#!/bin/sh\n'
                                 'if [ "$1" != -l ]; then exec /bin/sh "$@"; fi\n'
                                 f'read ready < "{ready_fifo}"\n'
                                 'printf "\\nLAZY-RENDER-READY\\n"\nexec /bin/sh\n')
                shell.chmod(0o700)
                # Configure before attach: the explicit reload confirmation is
                # not part of the automatic activation being measured.
                run('--shell', str(shell), 'configure')
                # A real attached client exercises the same hook as the user's
                # terminal, including session switches rather than only next-window.
                master, slave = pty.openpty()
                client = subprocess.Popen(['tmux', '-S', str(trial / 'socket'), 'attach-session', '-t', 'alpha:2'],
                                          stdin=slave, stdout=slave, stderr=slave, env=env)
                os.close(slave)
                try:
                    tmux('wait-for', 'lazy-visit-complete')
                    # Let the attached terminal receive its first screen before
                    # switching, matching navigation rather than initial attach.
                    tmux('send-keys', '-t', 'alpha:2', '-l', 'printf "\\nBEFORE-SWITCH\\n"')
                    tmux('send-keys', '-t', 'alpha:2', 'Enter')
                    initial = b''
                    deadline = time.monotonic() + 2
                    while b'BEFORE-SWITCH' not in initial:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
                            break
                        initial += os.read(master, 65536)
                    self.assertIn(b'BEFORE-SWITCH', initial)
                    tmux('switch-client', '-t', 'beta:1')
                    tmux('wait-for', 'lazy-visit-complete')
                    self.assertEqual(json.loads(run('status'))['pending_panes'], 1)
                    self.assertEqual(tmux('display-message', '-p', '-t', 'beta:1', '#{pane_current_path}'), str(home / 'one'))
                    self.assertEqual(run('save', '--quiet'), '')
                    quiet_save = json.loads((trial / 'state.json').read_text())
                    self.assertEqual(quiet_save['sessions'][1]['windows'][0]['panes'][0]['cwd'], {'home': 'one'})
                    # A quiet save must not freeze redraw with a confirmation.
                    # Pane output must reach the real client without a keypress or
                    # waiting for a success message's five-second display timer.
                    # send-keys would itself dismiss the message and hide the
                    # regression. Unblock output without any terminal key event.
                    descriptor = os.open(ready_fifo, os.O_WRONLY | os.O_NONBLOCK)
                    os.write(descriptor, b'ready\n')
                    os.close(descriptor)
                    output = b''
                    deadline = time.monotonic() + 1.5
                    while b'LAZY-RENDER-READY' not in output:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
                            break
                        output += os.read(master, 65536)
                    self.assertIn(b'LAZY-RENDER-READY', output,
                                  'Activated pane output was hidden from the attached client')
                    tmux('detach-client', '-s', 'beta')
                    client.wait(timeout=10)
                    self.assertEqual(client.returncode, 0)
                    self.assertEqual(run('--quiet', 'save'), '')
                    self.assertTrue(json.loads(run('status', '--quiet'))['running'])
                    self.assertEqual(run('stop', '--yes', '--quiet'), '')
                    saved_bytes = (trial / 'state.json').read_bytes()
                    failed = subprocess.run([*cli, 'save', '--quiet'], env=env, text=True,
                                            capture_output=True, timeout=15)
                    self.assertNotEqual(failed.returncode, 0)
                    self.assertIn('No running tmux server to save', failed.stderr)
                    self.assertEqual(failed.stdout, '')
                    self.assertEqual((trial / 'state.json').read_bytes(), saved_bytes)
                    self.assertEqual(run('save', '--quiet', '--if-running'), '')
                    self.assertEqual((trial / 'state.json').read_bytes(), saved_bytes)
                    (trial / 'private-runtime').write_text('must stay local')
                    exported = root / 'exported'
                    self.assertEqual(run('export', str(exported), '--quiet'), '')
                    self.assertEqual([p.name for p in exported.iterdir()], ['state.json'])
                    self.assertEqual((exported / 'state.json').read_bytes(), saved_bytes)
                    self.assertEqual((exported / 'state.json').stat().st_mode & 0o777, 0o600)
                finally:
                    if client.poll() is None:
                        client.terminate()
                        client.wait(timeout=10)
                    os.close(master)
            finally:
                if (trial / 'socket').exists():
                    subprocess.run(['tmux', '-S', str(trial / 'socket'), 'kill-server'],
                                   env=env, capture_output=True, timeout=15)

    def test_layout_round_trip_remaps_home_and_missing_cwd_never_partially_activates(self):
        with tempfile.TemporaryDirectory(prefix='lazy-layout-') as temporary:
            root = Path(temporary).resolve()
            homes = [root / 'source', root / 'destination']
            project = 'project #{HOME} with spaces'
            for home in homes:
                (home / project).mkdir(parents=True)
                (home / 'dotfiles').symlink_to(REPO, target_is_directory=True)
            directory = root / 'state'
            directory.mkdir()
            socket = root / 'socket'
            state = {'version': 1, 'focus': {'session': 's', 'window': 'w1'}, 'sessions': [
                {'uid': 's', 'name': 'project', 'windows': [
                    {'uid': 'w1', 'index': 1, 'name': 'code', 'active': True, 'zoom': True, 'layout': '',
                     'panes': [{'cwd': {'home': project}, 'title': 'first', 'active': False},
                               {'cwd': {'home': '.'}, 'title': 'second', 'active': True}]},
                    {'uid': 'w2', 'index': 2, 'name': 'pending', 'active': False, 'zoom': False, 'layout': '',
                     'panes': [{'cwd': {'home': '.'}, 'title': 'valid', 'active': True},
                               {'cwd': {'home': 'missing'}, 'title': 'missing', 'active': False}]}]}]}
            snapshot = directory / 'state.json'
            snapshot.write_text(json.dumps(state))
            env = {**os.environ, 'HOME': str(homes[0])}
            for key in ('TMUX', 'TMUX_PANE', 'TMUX_LAZY_STATE_DIR'):
                env.pop(key, None)

            def cli(*args, home=None, success=True):
                result = subprocess.run([sys.executable, str(SCRIPT), '--state-dir', str(directory),
                                         '--socket', str(socket), '--home', str(home or homes[0]), '--shell', '/bin/sh', *args],
                                        env=env, text=True, capture_output=True, timeout=30)
                if success:
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0)
                return result

            def tmux(*args):
                return subprocess.run(['tmux', '-S', str(socket), *args], env=env, text=True,
                                      capture_output=True, check=True, timeout=15).stdout.strip()

            try:
                cli('boot')
                self.assertEqual(json.loads(cli('status').stdout)['pending_panes'], 2)
                old_generation = tmux('show-option', '-gqv', '@lazy_generation')
                tmux('select-window', '-t', 'project:2')
                tmux('wait-for', 'lazy-visit-complete')
                self.assertEqual(tmux('list-panes', '-t', 'project:2', '-F', '#{pane_pid}'), '0\n0')
                tmux('select-window', '-t', 'project:1')
                tmux('wait-for', 'lazy-visit-complete')
                cli('save', '--quiet')
                saved = json.loads(snapshot.read_text())
                self.assertTrue(saved['sessions'][0]['windows'][0]['zoom'])
                self.assertTrue(saved['sessions'][0]['windows'][0]['panes'][1]['active'])
                original_cwd = saved['sessions'][0]['windows'][0]['panes'][0]['cwd']
                self.assertEqual(original_cwd, {'home': project})
                cli('stop', '--yes', '--quiet')
                cli('boot', home=homes[1])
                self.assertEqual(tmux('list-panes', '-t', 'project:1', '-F', '#{pane_current_path}').splitlines(),
                                 [str(homes[1] / project), str(homes[1])])
                self.assertEqual(tmux('display-message', '-p', '-t', 'project:1', '#{window_zoomed_flag}'), '1')
                # Stale hooks from a previous server cannot update a new instance.
                before = (directory / 'focus.json').read_bytes()
                wid = tmux('display-message', '-p', '-t', 'project:2', '#{window_id}')
                sid = tmux('display-message', '-p', '-t', 'project:2', '#{session_id}')
                cli('visit', wid, sid, old_generation, home=homes[1])
                self.assertEqual((directory / 'focus.json').read_bytes(), before)
                self.assertEqual(tmux('list-panes', '-t', 'project:2', '-F', '#{pane_pid}'), '0\n0')
                cli('save', '--quiet', home=homes[1])
                again = json.loads(snapshot.read_text())
                def geometry(layout):
                    return re.sub(r'(\d+x\d+,\d+,\d+),\d+(?=[}\],]|$)', r'\1,P', layout.split(',', 1)[1])
                self.assertEqual(geometry(saved['sessions'][0]['windows'][0]['layout']),
                                 geometry(again['sessions'][0]['windows'][0]['layout']))
                cli('stop', '--yes', '--quiet', home=homes[1])
                again['unexpected'] = True
                snapshot.write_text(json.dumps(again))
                invalid_bytes = snapshot.read_bytes()
                cli('export', str(root / 'invalid-export'), '--quiet', success=False)
                self.assertFalse((root / 'invalid-export').exists())
                self.assertEqual(snapshot.read_bytes(), invalid_bytes)
            finally:
                if socket.exists():
                    subprocess.run(['tmux', '-S', str(socket), 'kill-server'], env=env, capture_output=True, timeout=15)

    def test_native_server_winning_startup_race_is_not_modified(self):
        with tempfile.TemporaryDirectory(prefix='lazy-race-') as temporary:
            root = Path(temporary).resolve()
            home = root / 'home'
            home.mkdir()
            (home / 'dotfiles').symlink_to(REPO, target_is_directory=True)
            socket = root / 'socket'
            real_tmux = shutil.which('tmux')
            binary_dir = root / 'bin'
            binary_dir.mkdir()
            wrapper = binary_dir / 'tmux'
            # The external tmux boundary deterministically lets a native creator
            # win after the lazy caller's absence check, before start-server.
            wrapper.write_text(f'#!{sys.executable}\n'
                               'import os, pathlib, subprocess, sys\n'
                               f'real={real_tmux!r}; socket={str(socket)!r}\n'
                               f'marker=pathlib.Path({str(root / "created")!r})\n'
                               'if "start-server" in sys.argv[1:] and not marker.exists():\n'
                               ' subprocess.run([real,"-S",socket,"-f","/dev/null","new-session","-d","-s","native-winner","/bin/sh"],check=True)\n'
                               ' subprocess.run([real,"-S",socket,"set-option","-g","history-limit","12345"],check=True)\n'
                               ' marker.write_text("created")\n'
                               'os.execv(real,[real,*sys.argv[1:]])\n')
            wrapper.chmod(0o700)
            env = {**os.environ, 'HOME': str(home), 'PATH': str(binary_dir) + os.pathsep + os.environ['PATH']}
            for key in ('TMUX', 'TMUX_PANE', 'TMUX_LAZY_STATE_DIR'):
                env.pop(key, None)
            try:
                result = subprocess.run([sys.executable, str(SCRIPT), '--socket', str(socket),
                                         '--state-dir', str(root / 'state'), '--home', str(home), '--shell', '/bin/sh', 'boot'],
                                        env=env, text=True, capture_output=True, timeout=30)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('concurrently', result.stderr)
                for args, expected in [(['list-sessions', '-F', '#{session_name}'], 'native-winner'),
                                       (['show-option', '-gqv', 'history-limit'], '12345'),
                                       (['show-option', '-gqv', '@lazy_state_dir'], '')]:
                    check = subprocess.run([real_tmux, '-S', str(socket), *args], env=env,
                                           text=True, capture_output=True, check=True, timeout=15)
                    self.assertEqual(check.stdout.strip(), expected)
                self.assertFalse((root / 'state/state.json').exists())
            finally:
                if socket.exists():
                    subprocess.run([real_tmux, '-S', str(socket), 'kill-server'], env=env, capture_output=True, timeout=15)


if __name__ == '__main__':
    unittest.main()
