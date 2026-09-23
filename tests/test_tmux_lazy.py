# Copyright (c) 2026 Luiz Otávio Miranda
"""Real tmux integration on private sockets; never touch an existing server."""

from __future__ import annotations

import json
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
  from typing_extensions import TypeGuard

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tmux/scripts/lazy.py"
TMUX = shutil.which("tmux")


def is_object_mapping(value: object) -> TypeGuard[dict[object, object]]:
  return isinstance(value, dict)


class TmuxTestCase(unittest.TestCase):
  tmux_binary: str

  @classmethod
  def setUpClass(cls) -> None:
    if TMUX is None:
      reason = "tmux is required"
      raise unittest.SkipTest(reason)
    cls.tmux_binary = TMUX

  def setUp(self) -> None:
    # Error notifications otherwise inherit TMUX and can reach the user's server.
    # Shell startup files must not run from the caller's ENV/BASH_ENV either.
    environment = dict(os.environ)
    for key in ("TMUX", "TMUX_PANE", "TMUX_LAZY_STATE_DIR", "ENV", "BASH_ENV"):
      environment.pop(key, None)
    cleanup = patch.dict(os.environ, environment, clear=True)
    cleanup.start()
    self.addCleanup(cleanup.stop)


class LazyTmuxTests(TmuxTestCase):
  def test_activated_pane_linefeeds_preserve_cursor_column(self):
    with tempfile.TemporaryDirectory(prefix="lazy-linefeed-test-") as temporary:
      root = Path(temporary).resolve()
      home = root / "home"
      home.mkdir()
      (home / "dotfiles").symlink_to(REPO, target_is_directory=True)
      socket = root / "socket"
      shell = root / "shell"
      shell.write_text(
        "#!/bin/sh\n"
        'if [ "$1" != -l ]; then exec /bin/sh "$@"; fi\n'
        # Like a TUI, disable the tty driver's output transformations. A plain
        # LF moves down one row, keeping the column after the preceding text.
        "stty -opost\n"
        "printf '\\033[2J\\033[H\\033[3;9Hfirst\\nsecond'\n"
        '"$TEST_TMUX" -S "$TEST_SOCKET" wait-for -S rendered\n'
        "exec /bin/sh\n"
      )
      shell.chmod(0o700)
      fixture = root / "snapshot.txt"
      fixture.write_text(
        "pane\ttrial\t1\t1\t:*\t1\tcode\t:~\t1\tzsh\t:\n"
        "window\ttrial\t1\t:code\t1\t:*\t\t:\n"
        "state\ttrial\ttrial\n"
      )
      env = dict(os.environ, TEST_TMUX=self.tmux_binary, TEST_SOCKET=str(socket))
      cli = [
        sys.executable,
        str(SCRIPT),
        "--socket",
        str(socket),
        "--state-dir",
        str(root / "state"),
        "--home",
        str(home),
        "--shell",
        str(shell),
      ]

      def tmux(*args: str) -> str:
        # Only the test-owned socket, with literal tmux arguments.
        return subprocess.run(  # noqa: S603
          [self.tmux_binary, "-S", str(socket), "-N", *args],
          env=env,
          capture_output=True,
          text=True,
          check=True,
          timeout=15,
        ).stdout

      try:
        for args in (("import", "--snapshot", str(fixture)), ("boot",)):
          # Public lazy CLI and its supported shell/socket/home overrides.
          subprocess.run(  # noqa: S603
            [*cli, *args], env=env, capture_output=True, check=True, timeout=30
          )
        tmux("wait-for", "rendered")
        lines = tmux("capture-pane", "-p", "-t", "trial:1").splitlines()
        self.assertEqual(lines[2], "        first")
        self.assertTrue(lines[3].startswith("             second"), lines[3])
      finally:
        subprocess.run(  # noqa: S603
          [self.tmux_binary, "-S", str(socket), "-N", "kill-server"],
          capture_output=True,
          check=False,
          timeout=15,
        )

  def test_sleep_preserves_window_structure_and_reopens_fresh_shells(self):  # noqa: PLR0915
    with tempfile.TemporaryDirectory(prefix="lazy-sleep-test-") as temporary:
      root = Path(temporary).resolve()
      home = root / "home"
      (home / "project").mkdir(parents=True)
      (home / "dotfiles").symlink_to(REPO, target_is_directory=True)
      socket = root / "socket"
      cli = [
        sys.executable,
        str(SCRIPT),
        "--socket",
        str(socket),
        "--state-dir",
        str(root / "state"),
        "--home",
        str(home),
        "--shell",
        "/bin/sh",
      ]

      def run(*args: str, success: bool = True) -> str:
        # Public lazy CLI with an isolated home/socket and no personal shell rc.
        result = subprocess.run(  # noqa: S603
          [*cli, *args], capture_output=True, text=True, check=False, timeout=30
        )
        self.assertEqual(result.returncode == 0, success, result.stderr)
        return result.stdout

      def tmux(*args: str) -> str:
        # Fixed test-owned socket, never the default server.
        return subprocess.run(  # noqa: S603
          [self.tmux_binary, "-S", str(socket), "-N", *args],
          capture_output=True,
          text=True,
          check=True,
          timeout=15,
        ).stdout.strip()

      try:
        run("boot")
        sid = tmux("display-message", "-p", "#{session_id}")
        wid = tmux("display-message", "-p", "#{window_id}")
        generation = tmux("show-option", "-gqv", "@lazy_generation")
        original = tmux("list-panes", "-t", wid, "-F", "#{pane_pid}")
        # No implicit/destructive fallback when this is the session's only window.
        run("sleep", wid, sid, generation, "--yes", success=False)
        self.assertEqual(tmux("list-panes", "-t", wid, "-F", "#{pane_pid}"), original)
        other = tmux(
          "new-window", "-d", "-t", sid, "-n", "other", "-P", "-F", "#{window_id}"
        )
        other_pid = tmux("list-panes", "-t", other, "-F", "#{pane_pid}")
        pane = tmux(
          "split-window",
          "-h",
          "-t",
          wid,
          "-c",
          str(home / "project"),
          "-P",
          "-F",
          "#{pane_id}",
        )
        tmux("select-pane", "-t", pane, "-T", "project title")
        tmux("set-option", "-p", "-t", pane, "remain-on-exit", "failed")
        tmux("resize-pane", "-Z", "-t", pane)
        master, slave = pty.openpty()
        # Exercise the real prefix-x confirmation, not just its CLI payload.
        client = subprocess.Popen(  # noqa: S603
          [self.tmux_binary, "-S", str(socket), "attach-session", "-t", sid],
          stdin=slave,
          stdout=slave,
          stderr=slave,
          env={**os.environ, "TERM": "xterm-256color"},
        )
        os.close(slave)
        self.addCleanup(os.close, master)
        self.addCleanup(client.wait, timeout=5)
        self.addCleanup(client.terminate)
        tmux("wait-for", "lazy-visit-complete")

        def confirm_prompt() -> None:
          os.write(master, b"\x02x")
          output = b""
          deadline = time.monotonic() + 5
          while b"End ALL pane processes" not in output:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
              break
            output += os.read(master, 65536)
          self.assertIn(b"End ALL pane processes", output)

        geometry = tmux("display-message", "-p", "-t", wid, "#{window_layout}")
        details = "#{pane_id}\t#{pane_title}\t#{pane_active}"
        before = tmux("list-panes", "-t", wid, "-F", details)
        pids = tmux("list-panes", "-t", wid, "-F", "#{pane_pid}")
        cwds = tmux("list-panes", "-t", wid, "-F", "#{pane_current_path}")
        # Confirmation and a current generation are required before destruction.
        run("sleep", wid, sid, generation, success=False)
        run("sleep", wid, sid, "stale", "--yes", success=False)
        self.assertEqual(tmux("list-panes", "-t", wid, "-F", "#{pane_pid}"), pids)
        confirm_prompt()
        os.write(master, b"n")
        confirm_prompt()
        self.assertEqual(tmux("list-panes", "-t", wid, "-F", "#{pane_pid}"), pids)
        os.write(master, b"y")
        try:
          tmux("wait-for", "lazy-sleep-complete")
        except subprocess.TimeoutExpired as exc:
          raise AssertionError(tmux("show-messages")) from exc
        tmux("wait-for", "lazy-visit-complete")
        self.assertEqual(tmux("list-panes", "-t", wid, "-F", details), before)
        self.assertEqual(
          tmux("display-message", "-p", "-t", wid, "#{window_layout}"), geometry
        )
        self.assertEqual(
          tmux("display-message", "-p", "-t", wid, "#{window_zoomed_flag}"), "1"
        )
        self.assertEqual(
          tmux("display-message", "-p", "-t", sid, "#{window_id}"), other
        )
        self.assertEqual(json.loads(run("status"))["pending_panes"], 2)
        self.assertEqual(json.loads(run("status"))["process_free_panes"], 2)
        self.assertEqual(
          tmux("list-panes", "-t", other, "-F", "#{pane_pid}"), other_pid
        )
        # A delayed visit from before sleeping must not immediately wake it.
        run("visit", wid, sid, generation)
        self.assertEqual(json.loads(run("status"))["pending_panes"], 2)
        run("save", "--quiet")
        saved = json.loads((root / "state/state.json").read_text())
        sleeping = saved["sessions"][0]["windows"][0]
        self.assertEqual(sleeping["panes"][1]["cwd"], {"home": "project"})
        tmux("select-window", "-t", wid)
        tmux("wait-for", "lazy-visit-complete")
        self.assertEqual(json.loads(run("status"))["pending_panes"], 0)
        self.assertEqual(
          tmux("list-panes", "-t", wid, "-F", "#{pane_current_path}"), cwds
        )
        self.assertNotEqual(tmux("list-panes", "-t", wid, "-F", "#{pane_pid}"), pids)
        self.assertEqual(
          tmux("show-option", "-pqv", "-t", pane, "remain-on-exit"), "failed"
        )
        self.assertEqual(
          tmux("list-panes", "-t", other, "-F", "#{pane_pid}"), other_pid
        )
      finally:
        subprocess.run(  # noqa: S603
          [self.tmux_binary, "-S", str(socket), "-N", "kill-server"],
          capture_output=True,
          check=False,
          timeout=15,
        )

  # One continuous lifecycle proves that running panes survive activation/restart
  # and that quiet saves do not hide output from the same attached client.
  def test_import_visit_save_and_restart_preserve_pending_and_running_windows(  # noqa: PLR0915
    self,
  ):
    with tempfile.TemporaryDirectory(prefix="lazy-demo-test-") as temporary:
      root = Path(temporary).resolve()
      home = root / "home"
      (home / "one").mkdir(parents=True)
      (home / "two").mkdir()
      (home / "dotfiles").symlink_to(REPO, target_is_directory=True)
      trial = root / "trial"
      fixture = root / "snapshot.txt"
      fixture.write_text(
        "\n".join(
          [
            f"pane\talpha\t1\t1\t:*\t1\tfirst\t:{home}/one\t1\tzsh\t:",
            f"pane\talpha\t2\t0\t:\t1\tsecond\t:{home}/two\t1\tzsh\t:",
            f"pane\tbeta\t1\t1\t:*\t1\tthird\t:{home}/one\t1\tzsh\t:",
            "window\talpha\t1\t:code\t1\t:*\t\t:",
            "window\talpha\t2\t:terminal\t0\t:\t\t:",
            "window\tbeta\t1\t:code\t1\t:*\t\t:",
            "state\talpha\tbeta",
          ]
        )
        + "\n"
      )
      cli = [
        sys.executable,
        str(SCRIPT),
        "--state-dir",
        str(trial),
        "--socket",
        str(trial / "socket"),
        "--home",
        str(home),
        "--shell",
        "/bin/sh",
      ]
      env = dict(os.environ)
      env.pop("TMUX", None)
      env.pop("TMUX_PANE", None)
      env["TERM"] = "xterm-256color"

      def run(*args: str) -> str:
        # Repository CLI, private state/socket and fixture arguments; no shell.
        result = subprocess.run(  # noqa: S603
          [*cli, *args],
          env=env,
          text=True,
          capture_output=True,
          timeout=30,
          check=False,
        )
        if result.returncode:
          self.fail(f"{args[0]} failed: {result.stderr}\n{result.stdout}")
        return result.stdout

      def tmux(*args: str) -> str:
        # Resolved tmux with explicit private socket and test-authored argv.
        return subprocess.run(  # noqa: S603
          [self.tmux_binary, "-S", str(trial / "socket"), *args],
          env=env,
          text=True,
          capture_output=True,
          check=True,
          timeout=15,
        ).stdout.strip()

      try:
        run("import", "--snapshot", str(fixture))
        run("boot")
        initial = json.loads(run("status"))
        self.assertEqual(
          (initial["sessions"], initial["windows"], initial["pending_panes"]),
          (2, 3, 2),
        )
        pid = tmux("display-message", "-p", "-t", "alpha:1", "#{pane_pid}")
        tmux("select-window", "-t", "alpha:2")
        tmux("wait-for", "lazy-visit-complete")
        self.assertEqual(json.loads(run("status"))["pending_panes"], 1)
        self.assertTrue((trial / "focus.json").exists())
        self.assertEqual(
          tmux("display-message", "-p", "-t", "alpha:1", "#{pane_pid}"), pid
        )
        tmux("rename-window", "-t", "alpha:2", "renamed")
        run("save")
        data = json.loads((trial / "state.json").read_text())
        self.assertEqual(data["sessions"][0]["windows"][1]["name"], "renamed")
        self.assertEqual(
          data["sessions"][1]["windows"][0]["panes"][0]["cwd"],
          {"home": "one"},
        )
        run("stop", "--yes")
        run("boot")
        self.assertEqual(json.loads(run("status"))["pending_panes"], 2)
        self.assertEqual(
          tmux("display-message", "-p", "-t", "alpha:", "#{window_name}"),
          "renamed",
          {
            "saved_focus": data["focus"],
            "current_focus": json.loads((trial / "focus.json").read_text()),
            "saved_windows": [
              (
                s["name"],
                s["uid"],
                [(w["name"], w["uid"], w["active"]) for w in s["windows"]],
              )
              for s in data["sessions"]
            ],
          },
        )
        self.assertEqual(
          tmux("display-message", "-p", "-t", "alpha:2", "#{pane_current_path}"),
          str(home / "two"),
        )
        bindings = tmux("list-keys", "-T", "prefix").splitlines()
        self.assertTrue(
          any("C-s " in line and "lazy.py" in line for line in bindings),
          bindings,
        )
        ready_fifo = root / "render-ready"
        os.mkfifo(ready_fifo)
        shell = root / "render-shell"
        shell.write_text(
          "#!/bin/sh\n"
          'if [ "$1" != -l ]; then exec /bin/sh "$@"; fi\n'
          f'read ready < "{ready_fifo}"\n'
          'printf "\\nLAZY-RENDER-READY\\n"\nexec /bin/sh\n'
        )
        shell.chmod(0o700)
        # Configure before attach: the explicit reload confirmation is
        # not part of the automatic activation being measured.
        run("--shell", str(shell), "configure")
        # A real attached client exercises the same hook as the user's
        # terminal, including session switches rather than only next-window.
        master, slave = pty.openpty()
        # Only attach to this test's private server, without shell interpretation.
        client = subprocess.Popen(  # noqa: S603
          [
            self.tmux_binary,
            "-S",
            str(trial / "socket"),
            "attach-session",
            "-t",
            "alpha:2",
          ],
          stdin=slave,
          stdout=slave,
          stderr=slave,
          env=env,
        )
        os.close(slave)
        try:
          tmux("wait-for", "lazy-visit-complete")
          # Let the attached terminal receive its first screen before
          # switching, matching navigation rather than initial attach.
          tmux(
            "send-keys",
            "-t",
            "alpha:2",
            "-l",
            'printf "\\nBEFORE-SWITCH\\n"',
          )
          tmux("send-keys", "-t", "alpha:2", "Enter")
          initial = b""
          deadline = time.monotonic() + 2
          while b"BEFORE-SWITCH" not in initial:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
              break
            initial += os.read(master, 65536)
          self.assertIn(b"BEFORE-SWITCH", initial)
          tmux("switch-client", "-t", "beta:1")
          tmux("wait-for", "lazy-visit-complete")
          self.assertEqual(json.loads(run("status"))["pending_panes"], 1)
          self.assertEqual(
            tmux(
              "display-message",
              "-p",
              "-t",
              "beta:1",
              "#{pane_current_path}",
            ),
            str(home / "one"),
          )
          self.assertEqual(run("save", "--quiet"), "")
          quiet_save = json.loads((trial / "state.json").read_text())
          self.assertEqual(
            quiet_save["sessions"][1]["windows"][0]["panes"][0]["cwd"],
            {"home": "one"},
          )
          # A quiet save must not freeze redraw with a confirmation.
          # Pane output must reach the real client without a keypress or
          # waiting for a success message's five-second display timer.
          # send-keys would itself dismiss the message and hide the
          # regression. Unblock output without any terminal key event.
          descriptor = os.open(ready_fifo, os.O_WRONLY | os.O_NONBLOCK)
          os.write(descriptor, b"ready\n")
          os.close(descriptor)
          output = b""
          deadline = time.monotonic() + 1.5
          while b"LAZY-RENDER-READY" not in output:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
              break
            output += os.read(master, 65536)
          self.assertIn(
            b"LAZY-RENDER-READY",
            output,
            "Activated pane output was hidden from the attached client",
          )
          tmux("detach-client", "-s", "beta")
          client.wait(timeout=10)
          self.assertEqual(client.returncode, 0)
          self.assertEqual(run("--quiet", "save"), "")
          self.assertTrue(json.loads(run("status", "--quiet"))["running"])
          self.assertEqual(run("stop", "--yes", "--quiet"), "")
          saved_bytes = (trial / "state.json").read_bytes()
          # Fixed CLI arguments target the private stopped server, without a shell.
          failed = subprocess.run(  # noqa: S603
            [*cli, "save", "--quiet"],
            env=env,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
          )
          self.assertNotEqual(failed.returncode, 0)
          self.assertIn("No running tmux server to save", failed.stderr)
          self.assertEqual(failed.stdout, "")
          self.assertEqual((trial / "state.json").read_bytes(), saved_bytes)
          self.assertEqual(run("save", "--quiet", "--if-running"), "")
          self.assertEqual((trial / "state.json").read_bytes(), saved_bytes)
          (trial / "private-runtime").write_text("must stay local")
          exported = root / "exported"
          self.assertEqual(run("export", str(exported), "--quiet"), "")
          self.assertEqual([p.name for p in exported.iterdir()], ["state.json"])
          self.assertEqual((exported / "state.json").read_bytes(), saved_bytes)
          self.assertEqual((exported / "state.json").stat().st_mode & 0o777, 0o600)
        finally:
          if client.poll() is None:
            client.terminate()
            client.wait(timeout=10)
          os.close(master)
      finally:
        if (trial / "socket").exists():
          # Cleanup is restricted to this test's explicit private socket.
          subprocess.run(  # noqa: S603
            [self.tmux_binary, "-S", str(trial / "socket"), "kill-server"],
            env=env,
            capture_output=True,
            timeout=15,
            check=False,
          )

  def test_snapshot_boundaries_preserve_compatible_values_and_reject_bad_records(
    self,
  ):
    with tempfile.TemporaryDirectory(prefix="lazy-validation-") as temporary:
      root = Path(temporary)
      state_dir = root / "state"
      state_dir.mkdir()
      state_file = state_dir / "state.json"
      cli = [
        sys.executable,
        str(SCRIPT),
        "--state-dir",
        str(state_dir),
        "--socket",
        str(root / "socket"),
        "--home",
        str(root),
        "--shell",
        "/bin/sh",
        "export",
      ]

      def snapshot(
        version: object,
        *,
        session_value: object = None,
        window_value: object = None,
        pane_value: object = None,
      ) -> dict[str, object]:
        pane = pane_value or {
          "cwd": {"home": "."},
          "title": "shell",
          "active": True,
        }
        window = window_value or {
          "uid": "window",
          "index": 1,
          "name": "code",
          "active": True,
          "zoom": False,
          "layout": "",
          "panes": [pane],
        }
        session = session_value or {
          "uid": "session",
          "name": "project",
          "windows": [window],
        }
        return {
          "version": version,
          "focus": {"session": ["legacy"], "window": None},
          "sessions": [session],
        }

      for version in (True, 1.0):
        with self.subTest(version=version):
          state = snapshot(version)
          state_file.write_text(json.dumps(state))
          destination = root / f"export-{type(version).__name__}"
          # Shell-free export to a fixture directory, with an explicit private socket.
          result = subprocess.run(  # noqa: S603
            [*cli, str(destination), "--quiet"],
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
          )
          self.assertEqual(result.returncode, 0, result.stderr)
          exported_value: object = json.loads((destination / "state.json").read_text())
          if not is_object_mapping(exported_value):
            self.fail("Exported snapshot is not a JSON object")
          self.assertEqual(exported_value["focus"], state["focus"])
          self.assertIs(type(exported_value["version"]), type(version))
          self.assertEqual(exported_value["version"], version)

      malformed = ["not", "a", "record"]
      malformed_records = {
        "session": snapshot(1, session_value=malformed),
        "window": snapshot(1, window_value=malformed),
        "pane": snapshot(1, pane_value=malformed),
      }
      for level, invalid in malformed_records.items():
        with self.subTest(level=level):
          state_file.write_text(json.dumps(invalid))
          destination = root / f"invalid-{level}"
          # Invalid data is read from JSON, not interpolated into a shell command.
          result = subprocess.run(  # noqa: S603
            [*cli, str(destination), "--quiet"],
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
          )
          self.assertNotEqual(result.returncode, 0)
          self.assertFalse(destination.exists())

  # Keep the source/destination round trip together: the second boot must consume
  # the first server's actual saved layout, focus and pending-pane state.
  def test_layout_round_trip_remaps_home_and_missing_cwd_never_partially_activates(  # noqa: PLR0915
    self,
  ):
    with tempfile.TemporaryDirectory(prefix="lazy-layout-") as temporary:
      root = Path(temporary).resolve()
      homes = [root / "source", root / "destination"]
      project = "project #{HOME} with spaces"
      for home in homes:
        (home / project).mkdir(parents=True)
        (home / "dotfiles").symlink_to(REPO, target_is_directory=True)
      directory = root / "state"
      directory.mkdir()
      socket = root / "socket"
      state = {
        "version": 1,
        "focus": {"session": "s", "window": "w1"},
        "sessions": [
          {
            "uid": "s",
            "name": "project",
            "windows": [
              {
                "uid": "w1",
                "index": 1,
                "name": "code",
                "active": True,
                "zoom": True,
                "layout": "",
                "panes": [
                  {
                    "cwd": {"home": project},
                    "title": "first",
                    "active": False,
                  },
                  {
                    "cwd": {"home": "."},
                    "title": "second",
                    "active": True,
                  },
                ],
              },
              {
                "uid": "w2",
                "index": 2,
                "name": "pending",
                "active": False,
                "zoom": False,
                "layout": "",
                "panes": [
                  {
                    "cwd": {"home": "."},
                    "title": "valid",
                    "active": True,
                  },
                  {
                    "cwd": {"home": "missing"},
                    "title": "missing",
                    "active": False,
                  },
                ],
              },
            ],
          }
        ],
      }
      snapshot = directory / "state.json"
      snapshot.write_text(json.dumps(state))
      env = {**os.environ, "HOME": str(homes[0])}
      for key in ("TMUX", "TMUX_PANE", "TMUX_LAZY_STATE_DIR"):
        env.pop(key, None)

      def cli(
        *args: str, home: Path | None = None, success: bool = True
      ) -> subprocess.CompletedProcess[str]:
        # Repository CLI with private fixture paths and separate argv, no shell.
        result = subprocess.run(  # noqa: S603
          [
            sys.executable,
            str(SCRIPT),
            "--state-dir",
            str(directory),
            "--socket",
            str(socket),
            "--home",
            str(home or homes[0]),
            "--shell",
            "/bin/sh",
            *args,
          ],
          env=env,
          text=True,
          capture_output=True,
          timeout=30,
          check=False,
        )
        if success:
          self.assertEqual(result.returncode, 0, result.stderr)
        else:
          self.assertNotEqual(result.returncode, 0)
        return result

      def tmux(*args: str) -> str:
        # Test-authored argv and the explicit private socket, no shell.
        return subprocess.run(  # noqa: S603
          [self.tmux_binary, "-S", str(socket), *args],
          env=env,
          text=True,
          capture_output=True,
          check=True,
          timeout=15,
        ).stdout.strip()

      try:
        cli("boot")
        self.assertEqual(json.loads(cli("status").stdout)["pending_panes"], 2)
        old_generation = tmux("show-option", "-gqv", "@lazy_generation")
        tmux("select-window", "-t", "project:2")
        tmux("wait-for", "lazy-visit-complete")
        self.assertEqual(
          tmux("list-panes", "-t", "project:2", "-F", "#{pane_pid}"), "0\n0"
        )
        pane_ids = tmux(
          "list-panes", "-t", "project:2", "-F", "#{pane_id}"
        ).splitlines()
        tmux("select-window", "-t", "project:1")
        tmux("wait-for", "lazy-visit-complete")
        tmux(
          "set-option",
          "-p",
          "-t",
          pane_ids[1],
          "@lazy_cwd",
          json.dumps({"home": 7}),
        )
        checkpoint = snapshot.read_bytes()
        tmux("select-window", "-t", "project:2")
        tmux("wait-for", "lazy-visit-complete")
        self.assertEqual(
          tmux("list-panes", "-t", "project:2", "-F", "#{pane_pid}"), "0\n0"
        )
        cli("save", "--quiet", success=False)
        self.assertEqual(snapshot.read_bytes(), checkpoint)
        tmux(
          "set-option",
          "-p",
          "-t",
          pane_ids[1],
          "@lazy_cwd",
          json.dumps({"home": "missing"}),
        )
        tmux("select-window", "-t", "project:1")
        tmux("wait-for", "lazy-visit-complete")
        cli("save", "--quiet")
        saved = json.loads(snapshot.read_text())
        self.assertTrue(saved["sessions"][0]["windows"][0]["zoom"])
        self.assertTrue(saved["sessions"][0]["windows"][0]["panes"][1]["active"])
        original_cwd = saved["sessions"][0]["windows"][0]["panes"][0]["cwd"]
        self.assertEqual(original_cwd, {"home": project})
        cli("stop", "--yes", "--quiet")
        cli("boot", home=homes[1])
        self.assertEqual(
          tmux(
            "list-panes", "-t", "project:1", "-F", "#{pane_current_path}"
          ).splitlines(),
          [str(homes[1] / project), str(homes[1])],
        )
        self.assertEqual(
          tmux(
            "display-message",
            "-p",
            "-t",
            "project:1",
            "#{window_zoomed_flag}",
          ),
          "1",
        )
        # Stale hooks from a previous server cannot update a new instance.
        before = (directory / "focus.json").read_bytes()
        wid = tmux("display-message", "-p", "-t", "project:2", "#{window_id}")
        sid = tmux("display-message", "-p", "-t", "project:2", "#{session_id}")
        cli("visit", wid, sid, old_generation, home=homes[1])
        self.assertEqual((directory / "focus.json").read_bytes(), before)
        self.assertEqual(
          tmux("list-panes", "-t", "project:2", "-F", "#{pane_pid}"), "0\n0"
        )
        cli("save", "--quiet", home=homes[1])
        again = json.loads(snapshot.read_text())

        def geometry(layout: str) -> str:
          return re.sub(
            r"(\d+x\d+,\d+,\d+),\d+(?=[}\],]|$)",
            r"\1,P",
            layout.split(",", 1)[1],
          )

        self.assertEqual(
          geometry(saved["sessions"][0]["windows"][0]["layout"]),
          geometry(again["sessions"][0]["windows"][0]["layout"]),
        )
        cli("stop", "--yes", "--quiet", home=homes[1])
        again["unexpected"] = True
        snapshot.write_text(json.dumps(again))
        invalid_bytes = snapshot.read_bytes()
        cli("export", str(root / "invalid-export"), "--quiet", success=False)
        self.assertFalse((root / "invalid-export").exists())
        self.assertEqual(snapshot.read_bytes(), invalid_bytes)
      finally:
        if socket.exists():
          # Never kill a default/inherited server: this socket belongs to the test.
          subprocess.run(  # noqa: S603
            [self.tmux_binary, "-S", str(socket), "kill-server"],
            env=env,
            capture_output=True,
            timeout=15,
            check=False,
          )

  def test_native_server_winning_startup_race_is_not_modified(self):
    with tempfile.TemporaryDirectory(prefix="lazy-race-") as temporary:
      root = Path(temporary).resolve()
      home = root / "home"
      home.mkdir()
      (home / "dotfiles").symlink_to(REPO, target_is_directory=True)
      socket = root / "socket"
      real_tmux = self.tmux_binary
      binary_dir = root / "bin"
      binary_dir.mkdir()
      wrapper = binary_dir / "tmux"
      # The external tmux boundary deterministically lets a native creator
      # win after the lazy caller's absence check, before start-server.
      wrapper.write_text(
        f"#!{sys.executable}\n"
        "import os, pathlib, subprocess, sys\n"
        f"real={real_tmux!r}; socket={str(socket)!r}\n"
        f"marker=pathlib.Path({str(root / 'created')!r})\n"
        'if "start-server" in sys.argv[1:] and not marker.exists():\n'
        ' subprocess.run([real,"-S",socket,"-f","/dev/null",\n'
        '  "new-session","-d","-s","native-winner","/bin/sh"],check=True)\n'
        ' subprocess.run([real,"-S",socket,"set-option","-g",\n'
        '  "history-limit","12345"],check=True)\n'
        ' marker.write_text("created")\n'
        "os.execv(real,[real,*sys.argv[1:]])\n"
      )
      wrapper.chmod(0o700)
      env = {
        **os.environ,
        "HOME": str(home),
        "PATH": str(binary_dir) + os.pathsep + os.environ["PATH"],
      }
      for key in ("TMUX", "TMUX_PANE", "TMUX_LAZY_STATE_DIR"):
        env.pop(key, None)
      try:
        # The test-owned wrapper injects a race on the private socket, without a shell.
        result = subprocess.run(  # noqa: S603
          [
            sys.executable,
            str(SCRIPT),
            "--socket",
            str(socket),
            "--state-dir",
            str(root / "state"),
            "--home",
            str(home),
            "--shell",
            "/bin/sh",
            "boot",
          ],
          env=env,
          text=True,
          capture_output=True,
          timeout=30,
          check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("concurrently", result.stderr)
        for args, expected in [
          (["list-sessions", "-F", "#{session_name}"], "native-winner"),
          (["show-option", "-gqv", "history-limit"], "12345"),
          (["show-option", "-gqv", "@lazy_state_dir"], ""),
        ]:
          # Inspect only the test's private server, using literal argv.
          check = subprocess.run(  # noqa: S603
            [real_tmux, "-S", str(socket), *args],
            env=env,
            text=True,
            capture_output=True,
            check=True,
            timeout=15,
          )
          self.assertEqual(check.stdout.strip(), expected)
        self.assertFalse((root / "state/state.json").exists())
      finally:
        if socket.exists():
          # The resolved real tmux cleans up only this test-owned socket.
          subprocess.run(  # noqa: S603
            [real_tmux, "-S", str(socket), "kill-server"],
            env=env,
            capture_output=True,
            timeout=15,
            check=False,
          )


class SleepNavigationTests(TmuxTestCase):
  def setUp(self) -> None:
    super().setUp()
    temporary = tempfile.TemporaryDirectory(prefix="lazy-navigation-")
    self.addCleanup(temporary.cleanup)
    self.root = Path(temporary.name).resolve()
    home = self.root / "home"
    home.mkdir()
    (home / "dotfiles").symlink_to(REPO, target_is_directory=True)
    self.socket = self.root / "socket"
    self.cli = [
      sys.executable,
      str(SCRIPT),
      "--socket",
      str(self.socket),
      "--state-dir",
      str(self.root / "state"),
      "--home",
      str(home),
      "--shell",
      "/bin/sh",
    ]
    self.addCleanup(self.stop_server)
    fixture = self.root / "snapshot.txt"
    records: list[str] = []
    for session in ("alpha", "beta"):
      for index in range(1, 5):
        active = int(index == (2 if session == "alpha" else 1))
        records.extend(
          [
            f"pane\t{session}\t{index}\t{active}\t:\t1\tshell\t:~\t1\tsh\t:",
            f"window\t{session}\t{index}\t:window-{index}\t{active}\t:\t\t:",
          ]
        )
    fixture.write_text("\n".join([*records, "state\talpha\talpha", ""]))
    self.lazy("import", "--snapshot", str(fixture))
    self.lazy("boot")
    self.generation = self.tmux("show-option", "-gqv", "@lazy_generation")
    self.session = self.tmux("display-message", "-p", "-t", "alpha:", "#{session_id}")

  def stop_server(self) -> None:
    # Cleanup is restricted to this fixture's private socket, including failures.
    subprocess.run(  # noqa: S603
      [self.tmux_binary, "-S", str(self.socket), "-N", "kill-server"],
      capture_output=True,
      check=False,
      timeout=15,
    )

  def lazy(self, *args: str, success: bool = True) -> subprocess.CompletedProcess[str]:
    # Exercise the same CLI as the binding, with an isolated home and socket.
    result = subprocess.run(  # noqa: S603
      [*self.cli, *args], capture_output=True, text=True, check=False, timeout=30
    )
    self.assertEqual(result.returncode == 0, success, result.stderr)
    return result

  def tmux(self, *args: str) -> str:
    # Literal arguments and an explicit private socket, never the user's server.
    return subprocess.run(  # noqa: S603
      [self.tmux_binary, "-S", str(self.socket), "-N", *args],
      capture_output=True,
      text=True,
      check=True,
      timeout=15,
    ).stdout.strip()

  def select_window(self, target: str) -> None:
    self.tmux("select-window", "-t", target)
    self.tmux("wait-for", "lazy-visit-complete")

  def attach_client(self, target: str) -> tuple[int, str]:
    master, slave = pty.openpty()
    tty = os.ttyname(slave)
    # A real client on a fixture PTY exercises the production binding and hooks.
    client = subprocess.Popen(  # noqa: S603
      [self.tmux_binary, "-S", str(self.socket), "attach-session", "-t", target],
      stdin=slave,
      stdout=slave,
      stderr=slave,
      env={**os.environ, "TERM": "xterm-256color"},
    )
    os.close(slave)
    self.addCleanup(os.close, master)
    self.addCleanup(client.wait, timeout=5)
    self.addCleanup(client.terminate)
    self.tmux("wait-for", "lazy-visit-complete")
    return master, tty

  def confirm_sleep(self, master: int) -> None:
    os.write(master, b"\x02x")
    output = b""
    deadline = time.monotonic() + 5
    while b"End ALL pane processes" not in output:
      remaining = deadline - time.monotonic()
      if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
        break
      output += os.read(master, 65536)
    self.assertIn(b"End ALL pane processes", output)
    os.write(master, b"y")
    try:
      self.tmux("wait-for", "lazy-sleep-complete")
    except subprocess.TimeoutExpired as exc:
      messages = "\n".join(self.tmux("show-messages").splitlines()[:15])
      raise AssertionError(messages) from exc

  def test_sleep_selects_next_awake_window_and_wraps_without_waking_others(self):
    # Local awake windows win even over an alphabetically earlier live session.
    self.tmux("new-session", "-d", "-s", "aardvark", "/bin/sh")
    self.select_window("alpha:4")
    self.select_window("alpha:3")
    self.select_window("alpha:2")
    destination_pid = self.tmux("list-panes", "-t", "alpha:3", "-F", "#{pane_pid}")
    for source, destination in (("alpha:2", "3"), ("alpha:3", "4")):
      wid = self.tmux("display-message", "-p", "-t", source, "#{window_id}")
      self.lazy("sleep", wid, self.session, self.generation, "--yes")
      self.tmux("wait-for", "lazy-visit-complete")
      self.assertEqual(
        self.tmux("display-message", "-p", "-t", "alpha:", "#{window_index}"),
        destination,
      )
      if destination == "3":
        self.assertEqual(
          self.tmux("list-panes", "-t", "alpha:3", "-F", "#{pane_pid}"),
          destination_pid,
        )
        self.assertEqual(json.loads(self.lazy("status").stdout)["pending_panes"], 6)
    self.select_window("alpha:1")
    self.select_window("alpha:4")
    wid = self.tmux("display-message", "-p", "-t", "alpha:4", "#{window_id}")
    self.lazy("sleep", wid, self.session, self.generation, "--yes")
    self.tmux("wait-for", "lazy-visit-complete")
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", "alpha:", "#{window_index}"), "1"
    )
    self.assertEqual(json.loads(self.lazy("status").stdout)["pending_panes"], 7)

  def test_sleep_switches_source_clients_to_an_awake_window_in_another_session(self):
    # beta's selected window remains pending. Entering beta without targeting
    # its awake window would start a shell the user never asked to wake.
    destination = self.tmux(
      "new-window", "-d", "-t", "beta:5", "-P", "-F", "#{window_id}"
    )
    destination_pid = self.tmux("list-panes", "-t", destination, "-F", "#{pane_pid}")
    # An empty active pane does not make the whole window asleep: its other pane
    # still has a shell. The destination must be decided from all its panes.
    self.tmux("split-window", "-h", "-t", destination, "")
    self.tmux("new-session", "-d", "-s", "gamma", "/bin/sh")
    _, unrelated = self.attach_client("gamma:")
    master, first = self.attach_client("alpha:2")
    _, second = self.attach_client("alpha:2")
    source = self.tmux("display-message", "-p", "-t", "alpha:2", "#{window_id}")
    self.confirm_sleep(master)
    self.tmux("wait-for", "lazy-visit-complete")
    locations = dict(
      row.split("\t")
      for row in self.tmux(
        "list-clients", "-F", "#{client_tty}\t#{session_name}:#{window_index}"
      ).splitlines()
    )
    self.assertEqual(
      locations, {first: "beta:5", second: "beta:5", unrelated: "gamma:1"}
    )
    self.assertEqual(
      self.tmux("list-panes", "-t", destination, "-F", "#{pane_pid}"),
      destination_pid + "\n0",
    )
    # Replaying a visit queued before sleep must not revive the source, even
    # though its detached session still selects that same (now sleeping) window.
    self.lazy("visit", source, self.session, self.generation)
    self.assertEqual(json.loads(self.lazy("status").stdout)["pending_panes"], 8)
    self.assertEqual(self.tmux("list-panes", "-t", source, "-F", "#{pane_dead}"), "1")
    self.tmux("switch-client", "-c", first, "-t", "alpha:2")
    self.tmux("wait-for", "lazy-visit-complete")
    self.assertEqual(json.loads(self.lazy("status").stdout)["pending_panes"], 7)
    self.assertEqual(self.tmux("list-panes", "-t", source, "-F", "#{pane_dead}"), "0")

  def test_prefix_sleep_refusal_only_displays_status_without_opening_output_mode(self):
    master, client = self.attach_client("alpha:2")
    self.attach_client("alpha:2")
    source = self.tmux("display-message", "-p", "-t", "alpha:2", "#{window_id}")
    before = self.tmux("capture-pane", "-p", "-t", source)
    pid = self.tmux("list-panes", "-t", source, "-F", "#{pane_pid}")
    self.confirm_sleep(master)
    output = b""
    deadline = time.monotonic() + 5
    while b"No other supported awake window" not in output:
      remaining = deadline - time.monotonic()
      if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
        break
      output += os.read(master, 65536)
    self.assertIn(b"No other supported awake window", output)
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", source, "#{pane_in_mode}"), "0"
    )
    self.assertEqual(self.tmux("capture-pane", "-p", "-t", source), before)
    self.assertEqual(self.tmux("list-panes", "-t", source, "-F", "#{pane_pid}"), pid)
    # The binding's notification mode must also emit no stdout/stderr and exit
    # successfully, or run-shell opens output mode after the status message.
    result = self.lazy(
      "sleep", source, self.session, self.generation, "--yes", "--client", client
    )
    self.assertEqual((result.stdout, result.stderr), ("", ""))
    failed = self.lazy(
      "sleep", source, self.session, "stale", "--yes", "--client", client, success=False
    )
    self.assertIn("Stale sleep request", failed.stderr)

  def test_sleep_refuses_last_awake_window_without_changing_processes_or_focus(self):
    # Retained dead panes can have nonzero PIDs. They are not valid destinations,
    # any more than the process-free restored windows elsewhere in the server.
    self.tmux("set-option", "-g", "remain-on-exit", "on")
    self.tmux("set-hook", "-g", "pane-died[300]", "wait-for -S dead-ready")
    dead = self.tmux(
      "new-window", "-d", "-t", "beta:5", "-P", "-F", "#{window_id}", "exit 0"
    )
    self.tmux("wait-for", "dead-ready")
    self.assertNotEqual(self.tmux("list-panes", "-t", dead, "-F", "#{pane_pid}"), "0")
    wid = self.tmux("display-message", "-p", "-t", "alpha:2", "#{window_id}")
    details = "#{pane_id}\t#{pane_pid}\t#{pane_dead}\t#{@lazy_cwd}\t#{remain-on-exit}"
    before = self.tmux("list-panes", "-a", "-F", details)
    status = self.lazy("status").stdout
    result = self.lazy(
      "sleep", wid, self.session, self.generation, "--yes", success=False
    )
    self.assertIn("awake window", result.stderr)
    self.assertEqual(self.tmux("list-panes", "-a", "-F", details), before)
    self.assertEqual(self.lazy("status").stdout, status)
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", "alpha:", "#{window_id}"), wid
    )

  def test_destination_exiting_before_navigation_leaves_source_clients_and_processes(
    self,
  ):
    destination = self.tmux(
      "new-window", "-d", "-t", "beta:5", "-P", "-F", "#{session_id}:#{window_id}"
    )
    self.tmux("set-option", "-p", "-t", destination, "remain-on-exit", "on")
    self.tmux("set-hook", "-g", "pane-died[300]", "wait-for -S destination-exited")
    self.attach_client("alpha:2")
    source = self.tmux("display-message", "-p", "-t", "alpha:2", "#{window_id}")
    details = "#{pane_pid}\t#{pane_dead}\t#{@lazy_cwd}\t#{remain-on-exit}"
    panes = self.tmux("list-panes", "-t", source, "-F", details)
    clients = self.tmux(
      "list-clients", "-F", "#{client_name}\t#{session_id}:#{window_id}"
    )
    windows = self.tmux("list-windows", "-a", "-F", "#{window_id}\t#{window_active}")
    binary_dir = self.root / "bin"
    binary_dir.mkdir()
    wrapper = binary_dir / "tmux"
    # Let the destination exit at the actual external navigation boundary, after
    # discovery/preflight but before tmux evaluates the focus-changing command.
    wrapper.write_text(
      f"#!{sys.executable}\n"
      "import os, pathlib, subprocess, sys\n"
      f"real={self.tmux_binary!r}; socket={str(self.socket)!r}\n"
      f"target={destination!r}; marker=pathlib.Path({str(self.root / 'exited')!r})\n"
      "if target in sys.argv and not marker.exists() and any(\n"
      " action in sys.argv for action in ('select-window', 'if-shell')):\n"
      " marker.touch()\n"
      " subprocess.run([real,'-S',socket,'send-keys','-t',target,'exit','Enter'],\n"
      "  check=True,timeout=5)\n"
      " subprocess.run([real,'-S',socket,'wait-for','destination-exited'],\n"
      "  check=True,timeout=5)\n"
      "os.execv(real,[real,*sys.argv[1:]])\n"
    )
    wrapper.chmod(0o700)
    with patch.dict(
      os.environ, {"PATH": str(binary_dir) + os.pathsep + os.environ["PATH"]}
    ):
      result = self.lazy(
        "sleep", source, self.session, self.generation, "--yes", success=False
      )
    self.assertIn("Destination is no longer awake", result.stderr)
    self.assertEqual(
      self.tmux("list-clients", "-F", "#{client_name}\t#{session_id}:#{window_id}"),
      clients,
    )
    self.assertEqual(
      self.tmux("list-windows", "-a", "-F", "#{window_id}\t#{window_active}"), windows
    )
    self.assertEqual(self.tmux("list-panes", "-t", source, "-F", details), panes)

  def test_sleep_only_window_preserves_cross_session_focus_without_attached_clients(
    self,
  ):
    source = self.tmux("display-message", "-p", "-t", "alpha:2", "#{window_id}")
    for target in ("alpha:4", "alpha:3", "alpha:1"):
      self.tmux("kill-window", "-t", target)
    self.select_window("beta:3")
    self.lazy("visit", source, self.session, self.generation)
    self.lazy("sleep", source, self.session, self.generation, "--yes")
    # beta:3 was already selected and there are no clients to switch, so no
    # navigation hook will record this focus on sleep's behalf.
    self.lazy("save", "--quiet")
    self.lazy("stop", "--yes", "--quiet")
    self.lazy("boot")
    self.assertEqual(self.tmux("list-panes", "-t", "alpha:1", "-F", "#{pane_pid}"), "0")
    self.assertNotEqual(
      self.tmux("list-panes", "-t", "beta:3", "-F", "#{pane_pid}"), "0"
    )
    self.assertEqual(json.loads(self.lazy("status").stdout)["pending_panes"], 4)


if __name__ == "__main__":
  unittest.main()
