# Copyright (c) 2026 Luiz Otávio Miranda

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

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
        self.script = scripts / "synchosts"
        real_rsync = shutil.which("rsync")
        if real_rsync is None:
            self.fail("rsync is required")
        self.real_rsync = real_rsync
        # Keep fixtures independent of the operator's editable default fleet.
        runner = scripts / "run_all_hosts"
        runner_text, replacements = re.subn(
            r"(?m)^hosts=\([^)]*\)$",
            "hosts=(m132 m4128 fedoraair)",
            runner.read_text(),
        )
        self.assertEqual(replacements, 1)
        runner.write_text(runner_text)
        for host in ["m132", "m4128", "fedoraair", "extra"]:
            home = self.root / "homes" / host
            for directory in [
                "Desktop/tutoriais_e_cursos/project/.omnews-data",
                "sannux-data/backups/omnews",
                ".pi/agent",
                ".agents/skills",
                ".ollama/service",
                ".config/omxterm",
                ".codex/automations",
                ".local/share/tmux/lazy",
            ]:
                (home / directory).mkdir(parents=True)
            (home / ".zshrc").write_text("# isolated shell fixture\n")
            (home / ".zsh_history").write_text(": 100:0;echo fixture\n")
            (home / "sannux-data/backups/omnews" / f"{host}.db").write_text(host)
            (home / ".pi/agent" / f"{host}.txt").write_text(host)
            (home / "Desktop/tutoriais_e_cursos/project" / f"{host}.txt").write_text(
                host
            )
            (
                home / "Desktop/tutoriais_e_cursos/project/.omnews-data/local.db"
            ).write_text(host)
            (home / ".local/share/tmux/lazy/state.json").write_text(
                '{"version": 1, "sessions": [{"name": "fixture"}]}\n'
            )
        (self.root / "tmp").mkdir()
        fake = self.bin / "fake-command"
        fake.write_text(
            f"#!{sys.executable}\n"
            "import json, os, pathlib, shutil, subprocess, sys\n"
            "name=pathlib.Path(sys.argv[0]).name; args=sys.argv[1:]\n"
            "root=pathlib.Path(os.environ['FIXTURE_ROOT'])\n"
            "with open(os.environ['COMMAND_LOG'],'a') as f: "
            "f.write(json.dumps([name,*args])+'\\n')\n"
            "if name==os.environ.get('FAIL_COMMAND'): sys.exit(17)\n"
            "if name=='hostname': "
            "print(os.environ.get('FAKE_HOST','m132')); sys.exit(0)\n"
            "if name in ['sleep','pullall','prline','stop_omnivoicetts']: sys.exit(0)\n"
            "if name=='gio':\n"
            " assert args[:2]==['trash','--']; args=args[2:]; name='trash'\n"
            "if name in ['trash','rm']:\n"
            " if os.environ.get('FAIL_TRASH') and name=='trash': sys.exit(9)\n"
            " store=root/'trash'; store.mkdir(exist_ok=True)\n"
            " for arg in args:\n"
            "  if arg.startswith('-'): continue\n"
            "  p=pathlib.Path(arg); assert p.is_absolute() and p.is_relative_to(root)\n"
            "  if p.exists() or p.is_symlink(): "
            "shutil.move(str(p),str(store/(str(len(list(store.iterdir())))+'-'+p.name)))\n"
            " sys.exit(0)\n"
            "if name=='ssh':\n"
            " host,command=args[-2:]; home=root/'homes'/host\n"
            " if 'scripts/clear_sannux_transients' in command: "
            "sys.exit(19 if os.environ.get('FAIL_IDLE') else 0)\n"
            " if 'scripts/stop_omnivoicetts' in command: sys.exit(0)\n"
            " if '.zsh_history' in command: "
            "print(': 100:0;echo fixture'); sys.exit(0)\n"
            " env={**os.environ,'HOME':str(home),'ZDOTDIR':str(home)}\n"
            " if host==os.environ.get('FAIL_REMOTE_TRASH') and 'trash' in command: "
            "env['FAIL_TRASH']='1'\n"
            " sys.exit(subprocess.call(['/bin/zsh','-fc',command],env=env))\n"
            "if name=='rsync':\n"
            " src,dst=args[-2:]\n"
            " if src.startswith(os.environ.get('FAIL_PULL','!')+':'): sys.exit(23)\n"
            " if dst.startswith(os.environ.get('FAIL_PUSH','!')+':'): sys.exit(23)\n"
            " def local(value):\n"
            "  if ':~/' in value:\n"
            "   host,path=value.split(':~/',1); "
            "value=str(root/'homes'/host/path)+('/' if value.endswith('/') else '')\n"
            "  assert pathlib.Path(value).resolve().is_relative_to(root)\n"
            "  return value\n"
            " os.execv(os.environ['REAL_RSYNC'],"
            "[os.environ['REAL_RSYNC'],*args[:-2],local(src),local(dst)])\n"
            "raise SystemExit('Unexpected fixture command '+name)\n"
        )
        fake.chmod(0o755)
        for name in [
            "hostname",
            "sleep",
            "pullall",
            "prline",
            "ssh",
            "rsync",
            "trash",
            "gio",
            "rm",
            "stop_omnivoicetts",
        ]:
            (self.bin / name).symlink_to(fake)
        for name in ["python3", "python3.14"]:
            (self.bin / name).symlink_to(sys.executable)
        cli = scripts / "tmux-lazy"
        cli.write_text(
            f"#!{sys.executable}\n"
            "import json, os, pathlib, shutil, sys\n"
            "assert 'TMUX' not in os.environ and 'TMUX_PANE' not in os.environ\n"
            "source=pathlib.Path(os.environ['HOME'])/'.local/share/tmux/lazy/state.json'\n"
            "if sys.argv[1:]==['save','--quiet','--if-running']:\n"
            " sys.exit(18 if os.environ.get('FAIL_SAVE') else 0)\n"
            "assert sys.argv[1]=='export' and len(sys.argv)==3\n"
            "if os.environ.get('FAIL_EXPORT'): sys.exit(19)\n"
            "json.loads(source.read_text())\n"
            "destination=pathlib.Path(sys.argv[2]); destination.mkdir()\n"
            "shutil.copy2(source,destination/'state.json')\n"
        )
        cli.chmod(0o755)

    def run_sync(
        self, *args: str, extra_env: Mapping[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "HOME": str(self.home),
            "ZDOTDIR": str(self.home),
            "HISTFILE": str(self.home / ".zsh_history"),
            "TMPDIR": str(self.root / "tmp"),
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "FIXTURE_ROOT": str(self.root),
            "COMMAND_LOG": str(self.log),
            "PROJECTS_DIR": "",
            "REAL_RSYNC": self.real_rsync,
            "RSYNC_BIN": str(self.bin / "rsync"),
            **(extra_env or {}),
        }
        # Fixed interpreter, fixture-owned script/argv and fake external commands.
        return subprocess.run(  # noqa: S603
            ["/bin/zsh", "-f", str(self.script), *args],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            timeout=40,
            check=False,
        )

    def commands(self) -> list[list[str]]:
        return (
            [json.loads(line) for line in self.log.read_text().splitlines()]
            if self.log.exists()
            else []
        )

    def test_explicit_snapshot_replaces_newer_peer_state_without_touching_runtime(self):
        expected = '{"version": 1, "sessions": [{"name": "fixture"}]}\n'
        for host in ["m132", "m4128", "fedoraair"]:
            directory = self.root / "homes" / host / ".local/share/tmux/lazy"
            (directory / "state.json").write_text(
                expected if host == "m132" else "old peer state\n"
            )
            timestamp = 100 if host == "m132" else 2000000000
            os.utime(directory / "state.json", (timestamp, timestamp))
            for name in ["focus.json", "lazy.lock", "runtime.json", "socket-marker"]:
                (directory / name).write_text(host)
        result = self.run_sync(
            extra_env={"TMUX": "/fixture/custom,12,0", "TMUX_PANE": "%0"}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in ["m132", "m4128", "fedoraair"]:
            directory = self.root / "homes" / host / ".local/share/tmux/lazy"
            self.assertEqual((directory / "state.json").read_text(), expected)
            for name in ["focus.json", "lazy.lock", "runtime.json", "socket-marker"]:
                self.assertEqual((directory / name).read_text(), host)

    def test_new_files_from_each_peer_reach_every_host_in_one_run(self):
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in ["m132", "m4128", "fedoraair"]:
            home = self.root / "homes" / host
            for origin in ["m132", "m4128", "fedoraair"]:
                for directory, suffix in [
                    ("Desktop/tutoriais_e_cursos/project", ".txt"),
                ]:
                    self.assertEqual(
                        (home / directory / (origin + suffix)).read_text(), origin
                    )
            self.assertEqual(
                (
                    home / "Desktop/tutoriais_e_cursos/project/.omnews-data/local.db"
                ).read_text(),
                host,
            )
        copies = [c for c in self.commands() if c[0] == "rsync" and "--server" not in c]
        self.assertFalse(any("m132:~/" in arg for c in copies for arg in c))
        data_copies = [c for c in copies if "tmux/lazy" not in c[-1]]
        phases = ["pull" if ":~/" in c[-2] else "push" for c in data_copies]
        self.assertEqual(phases, sorted(phases))

    def test_whole_ollama_service_travels_with_shared_exclusions(self):
        portable = [
            "ollama_models.json",
            "CATALOGS.md",
            "sync-model-catalogs.py",
            "homebrew.mxcl.ollama.plist",
            "patches/runner.go",
            "bin/ollama-hotfix",
            "backups/previous.env",
            "server.log",
            "daemon.pid",
            "daemon.lock",
        ]
        local_only = [
            "local.sqlite-wal",
            ".git/config",
        ]
        origin = self.root / "homes/m4128/.ollama/service"
        for relative in portable + local_only:
            path = origin / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic fixture")
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in ["m132", "fedoraair"]:
            destination = self.root / "homes" / host / ".ollama/service"
            for relative in portable:
                self.assertTrue((destination / relative).is_file(), relative)
            for relative in local_only:
                self.assertFalse((destination / relative).exists(), relative)
        for relative in local_only:
            self.assertTrue((origin / relative).is_file(), relative)

    def test_whole_private_roots_travel_with_only_shared_exclusions(self):
        portable = [
            ".config/omxterm/config.json",
            ".config/omxterm/snippets.json",
            ".config/omxterm/themes/custom.json",
            ".config/omxterm/assets/icon.svg",
            ".config/omxterm/runtime.json",
            ".pi/agent/models.json",
            "sannux-data/agent-homes/pi/.pi/agent/models.json",
            "sannux-data/agent-homes/pi/.pi/agent/settings.json",
            "sannux-data/agent-homes/pi/.pi/agent/extensions/example/index.ts",
            "sannux-data/agent-homes/pi/.pi/agent/skills/example/SKILL.md",
            "sannux-data/agent-homes/pi/.local/bin/codex_search",
            "sannux-data/agent-homes/codex/.codex/config.toml",
            "sannux-data/agent-homes/codex/.codex/rules/personal.rules",
            ".pi/agent/trust.json",
            ".pi/new-directory/unlisted-file.txt",
            "sannux-data/new-private-directory/unlisted-file.txt",
            "sannux-data/agent-homes/pi/.pi/agent/models-store.json",
            "sannux-data/agent-homes/pi/.pi/agent/private/runtime.json",
            "sannux-data/agent-homes/codex/.codex/hooks/state/lock",
            "sannux-data/agent-homes/codex/.codex/skills/.system/generated",
            "sannux-data/agent-homes/codex/.ssh/id_ed25519",
            "sannux-data/backups/omnews/export.db",
        ]
        local_only = [
            "sannux-data/agent-homes/pi/.pi/agent/extensions/example/node_modules/native.node",
            "sannux-data/agent-homes/pi/.local/node_modules/native.node",
            "sannux-data/agent-homes/codex.ephemeral-runs/run.ABC/.codex/config.toml",
            "sannux-data/worktrees/project/.git",
            "sannux-data/worktrees/project/.codex/config.toml",
            "sannux-data/live/queue.sqlite3",
            "sannux-data/backups/omnews/export.db-wal",
        ]
        origin = self.root / "homes/m4128"
        for relative in portable + local_only:
            path = origin / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic fixture")
        link_path = Path(".pi/agent/extensions/shared")
        relative_target = "../../new-directory/unlisted-file.txt"
        (origin / link_path).parent.mkdir(parents=True, exist_ok=True)
        (origin / link_path).symlink_to(relative_target)
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in ["m132", "fedoraair"]:
            destination = self.root / "homes" / host
            self.assertTrue((destination / link_path).is_symlink())
            self.assertEqual(
                (destination / link_path).readlink(), Path(relative_target)
            )
            self.assertEqual((destination / link_path).read_text(), "synthetic fixture")
            for relative in portable:
                self.assertTrue((destination / relative).is_file(), relative)
            for relative in local_only:
                self.assertFalse((destination / relative).exists(), relative)

    def test_known_auth_and_ephemeral_runs_stay_out_of_normal_data_sync(self):
        transient = [
            "Desktop/tutoriais_e_cursos/project/.cache/data",
            "Desktop/tutoriais_e_cursos/edgetts/.cache/edgetts/chunk.mp3",
            ".codex/automations/daily/hooks/state/marker",
            ".codex/auth.json",
            ".pi/agent/auth.json",
            "sannux-data/agent-homes/pi.ephemeral-runs/run.ABC123/auth",
            "sannux-data/agent-homes/pi/.pi/agent/auth.json",
            "sannux-data/agent-homes/codex/.codex/auth.json",
            "sannux-data/workspaces/pi-daily-paper-node-modules/package",
            "sannux-data/workspaces/user-project/code",
            "Desktop/tutoriais_e_cursos/omxterm-issue-278/source.txt",
        ]
        durable = [
            "Desktop/tutoriais_e_cursos/project/.scratch/evidence",
            "sannux-data/.scratch/handoff.md",
            ".pi/.scratch/notes.md",
            "Desktop/tutoriais_e_cursos/omnivoicetts/samples/reference.wav",
            "Desktop/tutoriais_e_cursos/loudterm/assets/reference.wav",
            ".agents/skills/example/SKILL.md",
            ".pi/agent/sessions/conversation",
            "sannux-data/agent-homes/pi-daily-paper-sessions/.hidden",
            "sannux-data/agent-homes/pi/.pi/agent/sessions/session",
            "sannux-data/agent-homes/pi/.pi/agent/RESOURCE_SNAPSHOT",
        ]
        origin = self.root / "homes/m4128"
        for rel in transient + durable:
            f = origin / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("fixture only")
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for rel in transient:
            self.assertTrue((origin / rel).exists())
            self.assertFalse((self.home / rel).exists(), rel)
        for rel in durable:
            self.assertTrue((self.home / rel).exists(), rel)

    def test_auth_sync_uses_caller_not_newer_peer_credentials(self):
        paths = [
            ".codex/auth.json",
            ".pi/agent/auth.json",
            "sannux-data/agent-homes/codex/.codex/auth.json",
            "sannux-data/agent-homes/pi/.pi/agent/auth.json",
        ]
        for host in ["m132", "m4128", "fedoraair"]:
            for relative in paths:
                path = self.root / "homes" / host / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic-" + host)
                path.chmod(0o644)
                timestamp = 100 if host == "m132" else 300
                os.utime(path, (timestamp, timestamp))
        result = self.run_sync("--sync-auth")
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in ["m132", "m4128", "fedoraair"]:
            for relative in paths:
                path = self.root / "homes" / host / relative
                self.assertEqual(path.read_text(), "synthetic-m132")
                if host != "m132":
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_auth_sync_uses_selected_rsync_when_path_finds_an_old_one(self):
        legacy_bin = self.root / "legacy-bin"
        legacy_bin.mkdir()
        legacy_rsync = legacy_bin / "rsync"
        legacy_rsync.write_text(
            "#!/bin/sh\nprintf 'old system rsync selected\\n' >&2\nexit 1\n"
        )
        legacy_rsync.chmod(0o755)
        source = self.home / ".codex/auth.json"
        source.write_text("synthetic caller credentials")
        source.chmod(0o644)
        result = self.run_sync(
            "--sync-auth",
            extra_env={
                "PATH": f"{legacy_bin}:{self.bin}:{os.environ['PATH']}",
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(source.stat().st_mode & 0o777, 0o644)
        for host in ["m4128", "fedoraair"]:
            target = self.root / "homes" / host / ".codex/auth.json"
            self.assertEqual(target.read_text(), "synthetic caller credentials")
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_auth_sync_keeps_machine_identity_and_absent_or_failed_auth(self):
        identity_paths = [
            ".codex/installation-id",
            ".codex/config.toml",
            ".codex/state.sqlite3",
            ".codex/sessions/conversation.jsonl",
        ]
        for host in ["m132", "m4128", "fedoraair"]:
            home = self.root / "homes" / host
            for relative in identity_paths:
                path = home / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(host)
            (home / ".codex/auth.json").write_text("synthetic-" + host)
            if host != "m132":
                (home / ".pi/agent/auth.json").write_text("synthetic-" + host)
        result = self.run_sync("--sync-auth", extra_env={"FAIL_PUSH": "m4128"})
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAILED: auth push m4128", result.stdout)
        for host in ["m132", "m4128", "fedoraair"]:
            home = self.root / "homes" / host
            for relative in identity_paths:
                self.assertEqual((home / relative).read_text(), host, relative)
            expected = "m4128" if host == "m4128" else "m132"
            self.assertEqual(
                (home / ".codex/auth.json").read_text(), "synthetic-" + expected
            )
            if host != "m132":
                self.assertEqual(
                    (home / ".pi/agent/auth.json").read_text(), "synthetic-" + host
                )

    def test_git_metadata_stays_on_its_host_including_worktree_files(self):
        for host in ["m132", "m4128", "fedoraair"]:
            project = self.root / "homes" / host / "Desktop/tutoriais_e_cursos/project"
            pack = project / ".git/objects/pack" / (host + ".pack")
            pack.parent.mkdir(parents=True)
            pack.write_text(host)
            worktree = project / host
            worktree.mkdir()
            (worktree / ".git").write_text("gitdir: /host-local/fixture")
            (worktree / "source.txt").write_text(host)
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in ["m132", "m4128", "fedoraair"]:
            project = self.root / "homes" / host / "Desktop/tutoriais_e_cursos/project"
            self.assertEqual(
                [p.name for p in (project / ".git/objects/pack").iterdir()],
                [host + ".pack"],
            )
            for origin in ["m132", "m4128", "fedoraair"]:
                self.assertEqual((project / origin / "source.txt").read_text(), origin)
                self.assertEqual((project / origin / ".git").exists(), origin == host)

    def test_gio_fallback_uses_only_mocked_trash(self):
        # Force backend selection in this copied fixture script, never hide a
        # real tool and accidentally invoke the operator's desktop Trash.
        source = self.script.read_text()
        self.assertEqual(source.count("if command -v trash >/dev/null 2>&1; then"), 1)
        self.script.write_text(
            source.replace(
                "if command -v trash >/dev/null 2>&1; then", "if false; then"
            )
        )
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(c[0] == "gio" for c in self.commands()))

    def test_live_services_need_no_maintenance_and_keep_their_state_local(self):
        live = [
            ".pi/agent/auth.json",
            "sannux-data/agent-homes/pi/.pi/agent/auth.json",
            "sannux-data/live/current.db",
            ".codex/automations/daily/automation.toml",
            ".agents/runtime.json",
            "Desktop/tutoriais_e_cursos/omnivoicetts/data/job.json",
            "Desktop/tutoriais_e_cursos/omnivoicetts/outputs/audio.wav",
            "Desktop/tutoriais_e_cursos/loudterm/output/audio.wav",
            "Desktop/tutoriais_e_cursos/project/local.db-wal",
            "Desktop/tutoriais_e_cursos/project/.pi/session.json",
            "sannux-data/workspaces/user-project/code",
            "sannux-data/worktrees/user-project/feature/code",
            "Desktop/tutoriais_e_cursos/omxterm-issue-278/source.txt",
        ]
        for host in ["m132", "m4128", "fedoraair"]:
            for rel in live:
                target = self.root / "homes" / host / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(host)
                timestamp = 100 if host == "m132" else 200
                os.utime(target, (timestamp, timestamp))
        result = self.run_sync(extra_env={"FAIL_IDLE": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(
            any(
                any(
                    token in arg
                    for token in [
                        "clear_sannux_transients",
                        "stop_omnivoicetts",
                        "tts-media-",
                    ]
                )
                for call in self.commands()
                for arg in call
            )
        )
        for host in ["m132", "m4128", "fedoraair"]:
            for rel in live:
                self.assertEqual(
                    (self.root / "homes" / host / rel).read_text(), host, rel
                )

    def test_additional_host_does_not_trigger_idle_maintenance(self):
        result = self.run_sync("--additional-hosts", "extra")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [c[-1] for c in self.commands() if c[0] == "ssh" and c[-2] == "extra"]
        relevant = [
            c
            for c in calls
            if "scripts/clear_sannux_transients" in c
            or "scripts/stop_omnivoicetts" in c
        ]
        self.assertEqual(relevant, [])

    def test_newest_file_is_collected_before_distribution(self):
        for host, text, timestamp in [
            ("m132", "old", 100),
            ("m4128", "middle", 200),
            ("fedoraair", "newest", 300),
        ]:
            file = self.root / "homes" / host / ".agents/skills/version"
            file.write_text(text)
            os.utime(file, (timestamp, timestamp))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in ["m132", "m4128", "fedoraair"]:
            self.assertEqual(
                (self.root / "homes" / host / ".agents/skills/version").read_text(),
                "newest",
            )

    def test_fedora_can_be_the_caller_without_copying_to_itself(self):
        self.home = self.root / "homes/fedoraair"
        result = self.run_sync(extra_env={"FAKE_HOST": "fedoraair"})
        self.assertEqual(result.returncode, 0, result.stderr)
        copies = [c for c in self.commands() if c[0] == "rsync" and "--server" not in c]
        self.assertFalse(any("fedoraair:~/" in arg for c in copies for arg in c))
        for host in ["m132", "m4128", "fedoraair"]:
            for origin in ["m132", "m4128", "fedoraair"]:
                self.assertEqual(
                    (
                        self.root
                        / "homes"
                        / host
                        / "Desktop/tutoriais_e_cursos/project"
                        / (origin + ".txt")
                    ).read_text(),
                    origin,
                )

    def test_pullall_failure_warns_and_continues_copying(self):
        result = self.run_sync(extra_env={"FAIL_COMMAND": "pullall"})
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAILED: pullall", result.stdout)
        self.assertTrue(any(c[0] == "rsync" for c in self.commands()))

    def test_failed_collection_does_not_distribute_partial_data(self):
        (self.home / ".codex/auth.json").write_text("synthetic-caller")
        result = self.run_sync("--sync-auth", extra_env={"FAIL_PULL": "fedoraair"})
        self.assertEqual(result.returncode, 1, result.stderr)
        copies = [
            c
            for c in self.commands()
            if c[0] == "rsync" and "--server" not in c and "tmux/lazy" not in c[-1]
        ]
        self.assertTrue(all(":~/" in c[-2] for c in copies))
        self.assertTrue(any(".agents/" in c[-2] for c in copies))
        self.assertIn("synchosts summary", result.stdout)
        self.assertIn("FAILED: pull fedoraair", result.stdout)
        self.assertIn("BLOCKED: data publication", result.stdout)

    def test_failed_prerequisites_and_pushes_report_and_continue_independent_work(self):
        result = self.run_sync(
            extra_env={
                "FAIL_SAVE": "1",
                "FAIL_COMMAND": "pullall",
                "FAIL_PUSH": "m4128",
            }
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("synchosts summary", result.stdout)
        for failure in ["tmux save", "pullall", "push m4128"]:
            self.assertIn("FAILED: " + failure, result.stdout)
        self.assertIn("BLOCKED: tmux publication", result.stdout)
        self.assertFalse(
            any(c[0] == "rsync" and "tmux/lazy" in c[-1] for c in self.commands())
        )
        self.assertTrue(
            (
                self.root
                / "homes/fedoraair/Desktop/tutoriais_e_cursos/project/m132.txt"
            ).exists()
        )

    def test_failed_export_does_not_publish_snapshot_but_keeps_data_sync(self):
        peer_state = self.root / "homes/fedoraair/.local/share/tmux/lazy/state.json"
        peer_state.write_text("previous peer snapshot\n")
        result = self.run_sync(extra_env={"FAIL_EXPORT": "1"})
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("BLOCKED: tmux publication", result.stdout)
        self.assertEqual(peer_state.read_text(), "previous peer snapshot\n")
        self.assertFalse(
            any(c[0] == "rsync" and "tmux/lazy" in c[-1] for c in self.commands())
        )
        self.assertTrue(
            (
                self.root
                / "homes/fedoraair/Desktop/tutoriais_e_cursos/project/m132.txt"
            ).exists()
        )

    def test_failed_tmux_push_does_not_block_other_peers(self):
        peer = self.root / "homes/fedoraair/.local/share/tmux/lazy/state.json"
        peer.write_text("old peer snapshot")
        result = self.run_sync(extra_env={"FAIL_PUSH": "m4128"})
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAILED: tmux push m4128", result.stdout)
        self.assertEqual(
            peer.read_text(),
            (self.home / ".local/share/tmux/lazy/state.json").read_text(),
        )

    def test_failed_staging_keeps_independent_data_sync(self):
        result = self.run_sync(extra_env={"TMPDIR": str(self.root / "missing")})
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAILED: tmux staging directory", result.stdout)
        self.assertIn("BLOCKED: tmux publication", result.stdout)
        self.assertTrue(
            (
                self.root
                / "homes/fedoraair/Desktop/tutoriais_e_cursos/project/m132.txt"
            ).exists()
        )

    def test_failed_stage_cleanup_reports_failure_after_publication(self):
        result = self.run_sync(extra_env={"FAIL_TRASH": "1"})
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAILED: tmux stage cleanup", result.stdout)
        self.assertTrue(
            any(c[0] == "rsync" and "tmux/lazy" in c[-1] for c in self.commands())
        )

    def test_help_and_invalid_arguments_have_no_operational_effects(self):
        self.assertEqual(self.run_sync("--help").returncode, 0)
        self.assertEqual(self.run_sync("--sync-auth", "--help").returncode, 0)
        self.assertEqual(self.run_sync("--invalid").returncode, 2)
        self.assertEqual(self.commands(), [])

    def test_an_empty_additional_host_receives_the_collected_files(self):
        shutil.rmtree(self.root / "homes/extra")
        result = self.run_sync("--additional-hosts", "extra")
        self.assertEqual(result.returncode, 0, result.stderr)
        for origin in ["m132", "m4128", "fedoraair"]:
            source = (
                self.root
                / "homes/extra/Desktop/tutoriais_e_cursos/project"
                / (origin + ".txt")
            )
            self.assertEqual(source.read_text(), origin)
        self.assertTrue(
            (self.root / "homes/extra/.local/share/tmux/lazy/state.json").exists()
        )

    def test_only_disposable_stage_is_trashed(self):
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.commands()
        self.assertFalse(any(c[0] == "rm" for c in commands))
        self.assertFalse(any("--delete" in c for c in commands if c[0] == "rsync"))
        trashed = list((self.root / "trash").iterdir())
        self.assertEqual(len(trashed), 1)
        self.assertIn("-synchosts-tmux-lazy.", trashed[0].name)
        self.assertEqual(
            [p.name for p in (trashed[0] / "snapshot").iterdir()], ["state.json"]
        )


if __name__ == "__main__":
    unittest.main()
