import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]


class SyncHostsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synchosts fixture ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.home = self.root / "homes" / "m132"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "commands.jsonl"
        scripts = self.root / "checkout" / "scripts"
        (scripts / "lib").mkdir(parents=True)
        for name in ["synchosts", "run_all_hosts", "zsh_history_sync.py"]:
            shutil.copy2(REPOSITORY / "scripts" / name, scripts / name)
        shutil.copy2(
            REPOSITORY / "scripts/lib/prepare_tmux_resurrect.py",
            scripts / "lib/prepare_tmux_resurrect.py",
        )
        self.script = scripts / "synchosts"
        # Keep fixtures independent of the operator's editable default fleet.
        runner = scripts / "run_all_hosts"
        runner_text = runner.read_text()
        start = runner_text.index("hosts=(")
        end = runner_text.index(")", start) + 1
        runner.write_text(runner_text[:start] + "hosts=(m132 m4128 fedoraair)" + runner_text[end:])
        for host in ["m132", "m4128", "fedoraair", "extra"]:
            home = self.root / "homes" / host
            for directory in [
                "Desktop/tutoriais_e_cursos/project/.omnews-data",
                "sannux-data/backups/omnews",
                ".pi/agent",
                ".agents",
                ".ollama/service",
                ".config/omxterm",
                ".codex/automations",
                ".local/share/tmux/resurrect",
            ]:
                (home / directory).mkdir(parents=True)
            (home / ".zshrc").write_text("# isolated shell fixture\n")
            (home / ".zsh_history").write_text(": 100:0;echo fixture\n")
            (home / "sannux-data/backups/omnews" / f"{host}.db").write_text(host)
            (home / ".pi/agent" / f"{host}.txt").write_text(host)
            (home / "Desktop/tutoriais_e_cursos/project" / f"{host}.txt").write_text(host)
            (home / "Desktop/tutoriais_e_cursos/project/.omnews-data/local.db").write_text(host)
            (home / ".local/share/tmux/resurrect/.old-marker").write_text(host)
        (self.root / "tmp").mkdir()
        fake = self.bin / "fake-command"
        fake.write_text(
            f"#!{sys.executable}\n"
            "import json, os, pathlib, shutil, subprocess, sys\n"
            "name=pathlib.Path(sys.argv[0]).name; args=sys.argv[1:]\n"
            "root=pathlib.Path(os.environ['FIXTURE_ROOT'])\n"
            "with open(os.environ['COMMAND_LOG'],'a') as f: f.write(json.dumps([name,*args])+'\\n')\n"
            "if name==os.environ.get('FAIL_COMMAND'): sys.exit(17)\n"
            "if name=='hostname': print(os.environ.get('FAKE_HOST','m132')); sys.exit(0)\n"
            "if name in ['sleep','pullall','prline','stop_omnivoicetts']: sys.exit(0)\n"
            "if name=='gio':\n"
            " assert args[:2]==['trash','--']; args=args[2:]; name='trash'\n"
            "if name in ['trash','rm']:\n"
            " if os.environ.get('FAIL_TRASH') and name=='trash': sys.exit(9)\n"
            " store=root/'trash'; store.mkdir(exist_ok=True)\n"
            " for arg in args:\n"
            "  if arg.startswith('-'): continue\n"
            "  p=pathlib.Path(arg); assert p.is_absolute() and p.is_relative_to(root)\n"
            "  if p.exists() or p.is_symlink(): shutil.move(str(p),str(store/(str(len(list(store.iterdir())))+'-'+p.name)))\n"
            " sys.exit(0)\n"
            "if name=='ssh':\n"
            " host,command=args[-2:]; home=root/'homes'/host\n"
            " if 'scripts/clear_sannux_transients' in command: sys.exit(19 if os.environ.get('FAIL_IDLE') else 0)\n"
            " if 'scripts/stop_omnivoicetts' in command: sys.exit(0)\n"
            " if '.zsh_history' in command: print(': 100:0;echo fixture'); sys.exit(0)\n"
            " env={**os.environ,'HOME':str(home),'ZDOTDIR':str(home)}\n"
            " if host==os.environ.get('FAIL_REMOTE_TRASH') and 'trash' in command: env['FAIL_TRASH']='1'\n"
            " sys.exit(subprocess.call(['/bin/zsh','-fc',command],env=env))\n"
            "if name=='rsync':\n"
            " src,dst=args[-2:]\n"
            " if src.startswith(os.environ.get('FAIL_PULL','!')+':'): sys.exit(23)\n"
            " def local(value):\n"
            "  if ':~/' in value:\n"
            "   host,path=value.split(':~/',1); value=str(root/'homes'/host/path)+('/' if value.endswith('/') else '')\n"
            "  assert pathlib.Path(value).resolve().is_relative_to(root)\n"
            "  return value\n"
            " os.execv(os.environ['REAL_RSYNC'],[os.environ['REAL_RSYNC'],*args[:-2],local(src),local(dst)])\n"
            "raise SystemExit('Unexpected fixture command '+name)\n"
        )
        fake.chmod(0o755)
        for name in ["hostname", "sleep", "pullall", "prline", "ssh", "rsync", "trash", "gio", "rm", "stop_omnivoicetts"]:
            (self.bin / name).symlink_to(fake)
        for name in ["python3", "python3.14"]:
            (self.bin / name).symlink_to(sys.executable)
        save = self.home / ".tmux/plugins/tmux-resurrect/scripts/save.sh"
        save.parent.mkdir(parents=True)
        save.write_text(
            f"#!{sys.executable}\n"
            "import os,pathlib\n"
            "home=pathlib.Path(os.environ['HOME']); directory=home/'.local/share/tmux/resurrect'\n"
            "directory.mkdir(parents=True,exist_ok=True)\n"
            "counter=home/'save-count'; count=int(counter.read_text())+1 if counter.exists() else 1\n"
            "counter.write_text(str(count)); snapshot=directory/f'save-{count}.txt'\n"
            "snapshot.write_text('pane\\tfixture\\t1\\t:\\t0\\t:\\t:\\t:'+str(home)+'/project\\t:sh\\t:\\t:\\n')\n"
            "last=directory/'last'; last.unlink(missing_ok=True); last.symlink_to(snapshot.name)\n"
        )
        save.chmod(0o755)

    def run_sync(self, *args, extra_env=None):
        env = {
            **os.environ,
            "HOME": str(self.home),
            "ZDOTDIR": str(self.home),
            "HISTFILE": str(self.home / ".zsh_history"),
            "TMPDIR": str(self.root / "tmp"),
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "FIXTURE_ROOT": str(self.root),
            "COMMAND_LOG": str(self.log),
            "REAL_RSYNC": shutil.which("rsync"),
            **(extra_env or {}),
        }
        return subprocess.run(
            ["/bin/zsh", "-f", str(self.script), *args],
            cwd=self.root, env=env, capture_output=True, text=True, timeout=40,
        )

    def commands(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def test_new_files_from_each_peer_reach_every_host_in_one_run(self):
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in ["m132", "m4128", "fedoraair"]:
            home = self.root / "homes" / host
            for origin in ["m132", "m4128", "fedoraair"]:
                for directory, suffix in [
                    ("sannux-data/backups/omnews", ".db"),
                    (".pi/agent", ".txt"),
                    ("Desktop/tutoriais_e_cursos/project", ".txt"),
                ]:
                    self.assertEqual((home / directory / (origin + suffix)).read_text(), origin)
            self.assertEqual((home / "Desktop/tutoriais_e_cursos/project/.omnews-data/local.db").read_text(), host)
        copies = [c for c in self.commands() if c[0] == "rsync" and "--server" not in c]
        self.assertFalse(any("m132:~/" in arg for c in copies for arg in c))
        data_copies = [c for c in copies if "tmux/resurrect" not in c[-1]]
        phases = ["pull" if ":~/" in c[-2] else "push" for c in data_copies]
        self.assertEqual(phases, sorted(phases))

    def test_transient_data_is_not_copied_but_persistent_auth_and_resources_are(self):
        transient = [
            'Desktop/tutoriais_e_cursos/project/.scratch/evidence',
            'Desktop/tutoriais_e_cursos/project/.cache/data',
            '.codex/automations/daily/hooks/state/marker',
            '.pi/agent/sessions/conversation',
            'sannux-data/agent-homes/pi.ephemeral-runs/run.ABC123/auth',
            'sannux-data/agent-homes/pi-daily-paper-sessions/.hidden',
            'sannux-data/agent-homes/pi/.pi/agent/sessions/session',
            'sannux-data/workspaces/pi-daily-paper-node-modules/package',
        ]
        durable = ['sannux-data/agent-homes/pi/.pi/agent/auth.json',
                   'sannux-data/agent-homes/codex/.codex/auth.json',
                   'sannux-data/agent-homes/pi/.pi/agent/RESOURCE_SNAPSHOT',
                   'sannux-data/workspaces/user-project/code']
        origin = self.root / 'homes/m4128'
        for rel in transient + durable:
            f = origin / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text('fixture only')
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for rel in transient:
            self.assertTrue((origin / rel).exists())
            self.assertFalse((self.home / rel).exists(), rel)
        for rel in durable:
            self.assertTrue((self.home / rel).exists(), rel)

    def test_gio_fallback_uses_only_mocked_trash(self):
        # Force backend selection in this copied fixture script, never hide a
        # real tool and accidentally invoke the operator's desktop Trash.
        source = self.script.read_text()
        self.assertEqual(source.count('if command -v trash >/dev/null 2>&1; then'), 2)
        self.script.write_text(source.replace('if command -v trash >/dev/null 2>&1; then', 'if false; then'))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(c[0] == 'gio' for c in self.commands()))

    def test_idle_failure_stops_before_stop_or_copy(self):
        result = self.run_sync(extra_env={'FAIL_IDLE': '1'})
        self.assertEqual(result.returncode, 19, result.stderr)
        self.assertFalse(any(c[0] == 'rsync' or any('stop_omnivoicetts' in a for a in c)
                             for c in self.commands()))

    def test_additional_host_gets_idle_stop_and_apply_in_order(self):
        result = self.run_sync('--additional-hosts', 'extra')
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [c[-1] for c in self.commands() if c[0] == 'ssh' and c[-2] == 'extra']
        relevant = [c for c in calls if 'scripts/clear_sannux_transients' in c or 'scripts/stop_omnivoicetts' in c]
        self.assertEqual(len(relevant), 3)
        self.assertNotIn('--apply', relevant[0])
        self.assertIn('stop_omnivoicetts', relevant[1])
        self.assertIn('--apply --idle-confirmed', relevant[2])

    def test_newest_file_is_collected_before_distribution(self):
        for host, text, timestamp in [("m132", "old", 100), ("m4128", "middle", 200), ("fedoraair", "newest", 300)]:
            file = self.root / "homes" / host / ".agents/version"
            file.write_text(text)
            os.utime(file, (timestamp, timestamp))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in ["m132", "m4128", "fedoraair"]:
            self.assertEqual((self.root / "homes" / host / ".agents/version").read_text(), "newest")

    def test_fedora_can_be_the_caller_without_copying_to_itself(self):
        original_save = self.home / ".tmux/plugins/tmux-resurrect/scripts/save.sh"
        self.home = self.root / "homes/fedoraair"
        save = self.home / ".tmux/plugins/tmux-resurrect/scripts/save.sh"
        save.parent.mkdir(parents=True)
        shutil.copy2(original_save, save)
        result = self.run_sync(extra_env={"FAKE_HOST": "fedoraair"})
        self.assertEqual(result.returncode, 0, result.stderr)
        copies = [c for c in self.commands() if c[0] == "rsync" and "--server" not in c]
        self.assertFalse(any("fedoraair:~/" in arg for c in copies for arg in c))
        for host in ["m132", "m4128", "fedoraair"]:
            for origin in ["m132", "m4128", "fedoraair"]:
                self.assertEqual((self.root / "homes" / host / "sannux-data/backups/omnews" / (origin + ".db")).read_text(), origin)

    def test_nonzero_prerequisite_status_stops_before_copying(self):
        result = self.run_sync(extra_env={"FAIL_COMMAND": "pullall"})
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertFalse(any(c[0] == "rsync" for c in self.commands()))

    def test_failed_collection_does_not_distribute_partial_data(self):
        result = self.run_sync(extra_env={"FAIL_PULL": "fedoraair"})
        self.assertEqual(result.returncode, 23, result.stderr)
        copies = [c for c in self.commands() if c[0] == "rsync" and "--server" not in c]
        self.assertTrue(copies)
        self.assertTrue(all(":~/" in c[-2] for c in copies))

    def test_failed_local_trash_stops_before_copying(self):
        result = self.run_sync(extra_env={"FAIL_TRASH": "1"})
        self.assertEqual(result.returncode, 9, result.stderr)
        self.assertFalse(any(c[0] == "rsync" for c in self.commands()))
        self.assertTrue((self.home / ".local/share/tmux/resurrect/.old-marker").exists())

    def test_nonzero_profile_status_does_not_block_available_trash(self):
        (self.root / "homes/fedoraair/.zshrc").write_text("false\n")
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "homes/fedoraair/.local/share/tmux/resurrect/.old-marker").exists())

    def test_failed_remote_trash_preserves_that_snapshot(self):
        result = self.run_sync(extra_env={"FAIL_REMOTE_TRASH": "fedoraair"})
        self.assertEqual(result.returncode, 9, result.stderr)
        self.assertTrue((self.root / "homes/fedoraair/.local/share/tmux/resurrect/.old-marker").exists())
        self.assertFalse(any(c[0] == "rsync" and c[-1] == "fedoraair:~/.local/share/tmux/resurrect/" for c in self.commands()))

    def test_help_and_invalid_arguments_have_no_operational_effects(self):
        self.assertEqual(self.run_sync("--help").returncode, 0)
        self.assertEqual(self.run_sync("--invalid").returncode, 2)
        self.assertEqual(self.commands(), [])

    def test_an_empty_additional_host_receives_the_collected_files(self):
        shutil.rmtree(self.root / "homes/extra")
        result = self.run_sync("--additional-hosts", "extra")
        self.assertEqual(result.returncode, 0, result.stderr)
        for origin in ["m132", "m4128", "fedoraair"]:
            backup = self.root / "homes/extra/sannux-data/backups/omnews" / (origin + ".db")
            self.assertEqual(backup.read_text(), origin)
        self.assertTrue((self.root / "homes/extra/.local/share/tmux/resurrect/last").exists())

    def test_tmux_replacement_uses_trash_without_permanent_deletion(self):
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.commands()
        self.assertFalse(any(c[0] == "rm" for c in commands))
        self.assertFalse(any("--delete" in c for c in commands if c[0] == "rsync"))
        markers = list((self.root / "trash").glob("*-.old-marker"))
        self.assertEqual({p.read_text() for p in markers}, {"m132", "m4128", "fedoraair"})
        self.assertTrue(list((self.root / "trash").glob("*-synchosts-resurrect.*")))
        for host in ["m4128", "fedoraair"]:
            snapshot = self.root / "homes" / host / ".local/share/tmux/resurrect"
            self.assertFalse((snapshot / ".old-marker").exists())
            self.assertIn(":#{HOME}/project", (snapshot / "last").read_text())


if __name__ == "__main__":
    unittest.main()
