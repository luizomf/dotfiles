import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('cleanup', str(ROOT / 'scripts/clear_sannux_transients'))
spec = importlib.util.spec_from_loader(loader.name, loader)
cleanup = importlib.util.module_from_spec(spec)
loader.exec_module(cleanup)


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve()
        self.root = self.home / 'sannux-data/agent-homes'
        self.run = self.root / 'pi.ephemeral-runs/run.ABC123'
        self.run.mkdir(parents=True)
        (self.run / '.auth').write_text('fixture')
        self.sessions = self.root / 'pi-daily-paper-sessions'
        self.sessions.mkdir()
        (self.sessions / '.hidden').write_text('fixture')
        (self.sessions / 'nested').mkdir()
        self.persistent = self.root / 'pi/auth.json'
        self.persistent.parent.mkdir()
        self.persistent.write_text('persistent fixture')

    def test_preview_and_apply_preserve_persistent_homes_and_parent(self):
        idle = lambda root: None
        cleanup.clean(self.home, idle_check=idle)
        self.assertTrue(self.run.exists())
        cleanup.clean(self.home, True, idle)
        self.assertFalse(self.run.exists())
        self.assertEqual(list(self.sessions.iterdir()), [])
        self.assertEqual(self.persistent.read_text(), 'persistent fixture')

    def test_symlink_child_removed_without_following_target(self):
        (self.sessions / 'link').symlink_to(self.persistent.parent, target_is_directory=True)
        cleanup.clean(self.home, True, lambda root: None)
        self.assertTrue(self.persistent.exists())

    def test_symlink_namespace_rejected_before_any_deletion(self):
        (self.root / 'codex.ephemeral-runs').symlink_to(self.persistent.parent)
        with self.assertRaises(RuntimeError):
            cleanup.clean(self.home, True, lambda root: None)
        self.assertTrue(self.run.exists())

    def test_symlink_session_root_rejected(self):
        shutil.rmtree(self.sessions)
        self.sessions.symlink_to(self.persistent.parent)
        with self.assertRaises(RuntimeError):
            cleanup.clean(self.home, True, lambda root: None)
        self.assertTrue(self.persistent.exists())

    def test_unknown_names_and_history_are_not_cleanup_targets(self):
        unknown = self.run.parent / 'run.too-long'
        unknown.mkdir()
        history = self.home / '.local/state/daily-paper-tts/attempt'
        history.mkdir(parents=True)
        entries, preserved = cleanup.clean(self.home, True, lambda root: None)
        self.assertIn(unknown, preserved)
        self.assertTrue(history.exists())
        self.assertTrue(unknown.exists())

    def test_busy_owner_aborts_without_deletion(self):
        def busy(root):
            raise RuntimeError('busy')
        with self.assertRaises(RuntimeError):
            cleanup.clean(self.home, True, busy)
        self.assertTrue(self.run.exists())

    def test_changed_parent_is_rejected_at_apply_boundary(self):
        calls = []
        def idle(root):
            calls.append(root)
            if len(calls) == 2:
                self.run.parent.rename(self.root / 'saved-fixture')
                (self.root / 'pi.ephemeral-runs').symlink_to(self.persistent.parent)
        with self.assertRaises(RuntimeError):
            cleanup.clean(self.home, True, idle)
        self.assertTrue(self.persistent.exists())
        self.assertTrue((self.sessions / '.hidden').exists())

    def test_foreign_owner_is_rejected(self):
        with patch.object(cleanup.os, 'getuid', return_value=os.getuid() + 10000):
            with self.assertRaises(RuntimeError):
                cleanup.clean(self.home, True, lambda root: None)
        self.assertTrue(self.run.exists())

    def test_mount_is_rejected_before_deletion(self):
        with patch.object(cleanup.os.path, 'ismount', return_value=True):
            with self.assertRaises(RuntimeError):
                cleanup.clean(self.home, True, lambda root: None)
        self.assertTrue(self.run.exists())

    def test_container_bind_and_remote_context_are_rejected(self):
        def fake(*args):
            if args[0] == 'ps':
                return ''
            if args[1] == 'context':
                return 'unix:///fixture.sock'
            if args[1] == 'ps':
                return 'fixture-container'
            return json.dumps([{'Mounts': [{'Source': str(self.run)}]}])
        with patch.object(cleanup, 'command', side_effect=fake):
            with self.assertRaisesRegex(RuntimeError, 'mounts agent homes'):
                cleanup.assert_idle(self.root)
        with patch.object(cleanup, 'command', side_effect=['', 'ssh://remote']):
            with self.assertRaisesRegex(RuntimeError, 'local Unix-socket'):
                cleanup.assert_idle(self.root)

    def test_unavailable_inspection_fails_closed(self):
        with patch.object(cleanup, 'command', side_effect=OSError('unavailable')):
            with self.assertRaises(OSError):
                cleanup.clean(self.home, True)
        self.assertTrue(self.run.exists())

    def test_apply_requires_operator_confirmation(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/clear_sannux_transients'), '--apply'],
                                env={**os.environ, 'HOME': str(self.home)}, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(self.run.exists())


class StopTests(unittest.TestCase):
    def scenario(self, mode):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            shutil.copy2(ROOT / 'scripts/stop_omnivoicetts', root / 'stop')
            fake = root / 'fake'
            fake.write_text(f'#!{sys.executable}\n' + '''import pathlib,sys,os
root=pathlib.Path(os.environ['FIXTURE'])
name=pathlib.Path(sys.argv[0]).name
with (root/'log').open('a') as f: f.write(name+' '+ ' '.join(sys.argv[1:])+'\\n')
mode=os.environ['MODE']
if name=='pgrep':
 if mode=='error': sys.exit(2)
 sys.exit(1 if (root/'stopped').exists() else 0)
if name=='pkill' and mode!='stuck':
 if mode=='graceful' or '-9' in sys.argv: (root/'stopped').touch()
''')
            fake.chmod(0o755)
            for name in ['pgrep', 'pkill', 'sleep', 'clear_tts_cache']:
                (root / name).symlink_to(fake)
            result = subprocess.run(['/bin/bash', str(root / 'stop')],
                                    env={**os.environ, 'FIXTURE': str(root), 'MODE': mode,
                                         'PATH': f'{root}:/usr/bin:/bin'},
                                    capture_output=True, text=True, timeout=10)
            return result.returncode, (root / 'log').read_text()

    def test_stop_precedes_clear(self):
        rc, log = self.scenario('graceful')
        self.assertEqual(rc, 0)
        self.assertLess(log.index('pkill -TERM'), log.index('clear_tts_cache'))
        self.assertNotIn('pkill -9', log)

    def test_escalation_is_bounded_and_preserves_match_scope(self):
        rc, log = self.scenario('escalate')
        self.assertEqual(rc, 0)
        self.assertIn('pkill -9 -f /[o]mnivoicetts', log)
        self.assertLess(log.index('pkill -9'), log.index('clear_tts_cache'))

    def test_stuck_or_uninspectable_workers_never_clear(self):
        for mode in ['stuck', 'error']:
            rc, log = self.scenario(mode)
            self.assertNotEqual(rc, 0)
            self.assertNotIn('clear_tts_cache', log)


if __name__ == '__main__':
    unittest.main()
