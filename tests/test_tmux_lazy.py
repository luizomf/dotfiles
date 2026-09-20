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


class LazyTmuxTests(unittest.TestCase):
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


if __name__ == "__main__":
  unittest.main()
