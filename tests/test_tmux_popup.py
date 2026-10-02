# Copyright (c) 2026 Luiz Otávio Miranda
"""Exercise the popup script with real clients on a private tmux socket."""

from __future__ import annotations

import contextlib
import fcntl
import os
import pty
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POPUP = REPO / "tmux/scripts/popup.sh"


class PopupTests(unittest.TestCase):
  def setUp(self):
    binary = shutil.which("tmux")
    if binary is None:
      self.skipTest("tmux is required")
    self.binary = binary
    self.temporary = tempfile.TemporaryDirectory(prefix="popup-test-")
    self.addCleanup(self.temporary.cleanup)
    self.root = Path(self.temporary.name).resolve()
    self.socket = self.root / "socket with space"
    self.env = dict(os.environ, HOME=str(self.root), TERM="xterm-256color")
    for key in ("TMUX", "TMUX_PANE", "ENV", "BASH_ENV"):
      self.env.pop(key, None)
    config = self.root / "tmux.conf"
    config.write_text("set -g default-shell /bin/sh\nset -g default-command ''\n")
    self.tmux("-f", str(config), "new-session", "-d", "-s", "outer")
    self.addCleanup(self.tmux, "kill-server")
    self.master, slave = pty.openpty()
    self.addCleanup(os.close, self.master)
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
    self.client = subprocess.Popen(  # noqa: S603
      [self.binary, "-S", str(self.socket), "attach-session", "-t", "=outer"],
      env=self.env,
      stdin=slave,
      stdout=slave,
      stderr=slave,
      start_new_session=True,
    )
    os.close(slave)
    self.addCleanup(self.stop_client)
    self.wait_for_clients("outer")
    self.log = self.root / "popup.log"
    self.result = self.root / "popup.result"

  def stop_client(self):
    self.client.kill()
    self.client.wait(timeout=5)

  def tmux(self, *args: str) -> str:
    return subprocess.run(  # noqa: S603
      [self.binary, "-S", str(self.socket), *args],
      env=self.env,
      capture_output=True,
      text=True,
      check=True,
      timeout=10,
    ).stdout.strip()

  def wait_for_clients(self, *sessions: str):
    deadline = time.monotonic() + 5
    attached: list[str] = []
    while time.monotonic() < deadline:
      attached = self.tmux("list-clients", "-F", "#{session_name}").splitlines()
      if sorted(attached) == sorted(sessions):
        return
      if hasattr(self, "result") and self.result.exists():
        self.fail(f"Popup exited {self.result.read_text()}: {self.log.read_text()}")
      # Drain terminal output so a full PTY buffer cannot block the fixture.
      with contextlib.suppress(BlockingIOError):
        os.set_blocking(self.master, False)
        os.read(self.master, 65536)
      time.sleep(0.02)
    self.fail(f"Expected clients {sessions}, got {attached}")

  def open_popup(self, directory: Path | None = None):
    self.result.unlink(missing_ok=True)
    args = [str(POPUP), "float", "term"]
    if directory is not None:
      args.append(str(directory))
    command = shlex.join(args)
    command += f" >{shlex.quote(str(self.log))} 2>&1"
    command += f"; printf '%s' \"$?\" >{shlex.quote(str(self.result))}"
    self.tmux("bind-key", "C-w", "run-shell", command)
    os.write(self.master, b"\x02\x17")
    self.wait_for_clients("outer", "float")

  def test_popup_attaches_with_inherited_tmux_and_a_retained_dead_pane(self):
    inherited = self.tmux("display-message", "-p", "#{socket_path},#{pid},0")
    self.tmux("set-environment", "-t", "outer", "TMUX", inherited)
    pane = self.tmux("display-message", "-p", "-t", "outer:", "#{pane_id}")
    self.tmux("set-environment", "-t", "outer", "TMUX_PANE", pane)
    directory = self.root / "project with space"
    directory.mkdir()
    self.tmux("new-session", "-d", "-s", "float", "-c", str(directory))
    self.tmux("new-window", "-d", "-t", "outer:", "-n", "sleeping")
    self.tmux("set-option", "-w", "-t", "outer:sleeping", "remain-on-exit", "on")
    self.tmux("send-keys", "-t", "outer:sleeping", "exit", "Enter")
    deadline = time.monotonic() + 5
    while (
      self.tmux("display-message", "-p", "-t", "outer:sleeping", "#{pane_dead}") != "1"
    ):
      self.assertLess(time.monotonic(), deadline, "Fixture pane did not exit")
      time.sleep(0.02)
    self.open_popup(directory)
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", "float:", "#{pane_current_path}"),
      str(directory),
    )

  def close_popup(self):
    self.tmux("bind-key", "C-w", "run-shell", shlex.join([str(POPUP)]))
    os.write(self.master, b"\x02\x17")
    deadline = time.monotonic() + 5
    while not self.result.exists():
      self.assertLess(time.monotonic(), deadline, "Popup did not detach")
      time.sleep(0.02)
    self.assertEqual(self.result.read_text(), "0", self.log.read_text())
    self.result.unlink()
    self.wait_for_clients("outer")

  def test_creates_in_current_directory_and_reopens_without_replacing_shell(self):
    directory = self.root / "current project"
    directory.mkdir()
    self.tmux("new-window", "-t", "outer:", "-c", str(directory))
    self.open_popup()
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", "float:", "#{pane_current_path}"),
      str(directory),
    )
    pid = self.tmux("display-message", "-p", "-t", "float:", "#{pane_pid}")
    self.close_popup()
    self.open_popup(self.root)
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", "float:", "#{pane_pid}"), pid
    )
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", "float:", "#{pane_current_path}"),
      str(directory),
    )
    self.close_popup()

  def test_creates_exact_session_when_only_a_prefix_match_exists(self):
    self.tmux("new-session", "-d", "-s", "float-other")
    other_pid = self.tmux("display-message", "-p", "-t", "=float-other:", "#{pane_pid}")
    self.open_popup(self.root)
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", "=float:", "#{session_name}"),
      "float",
    )
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", "=float-other:", "#{pane_pid}"),
      other_pid,
    )
    self.close_popup()

  def lazy(self, *args: str):
    subprocess.run(  # noqa: S603
      [
        sys.executable,
        str(REPO / "tmux/scripts/lazy.py"),
        "--socket",
        str(self.socket),
        "--state-dir",
        str(self.root / "state"),
        "--home",
        str(self.root),
        "--shell",
        "/bin/sh",
        *args,
      ],
      env=self.env,
      capture_output=True,
      text=True,
      check=True,
      timeout=15,
    )

  def test_attach_wakes_sleeping_float_through_lazy_hook(self):
    directory = self.root / "saved project"
    directory.mkdir()
    self.tmux("new-session", "-d", "-s", "float", "-c", str(directory))
    self.lazy("configure", "--quiet")
    wid = self.tmux("display-message", "-p", "-t", "float:", "#{window_id}")
    sid = self.tmux("display-message", "-p", "-t", "float:", "#{session_id}")
    generation = self.tmux("show-option", "-gqv", "@lazy_generation")
    self.lazy("sleep", wid, sid, generation, "--yes")
    self.assertEqual(self.tmux("show-option", "-wqv", "-t", wid, "@lazy_pending"), "1")
    self.open_popup(self.root)
    deadline = time.monotonic() + 5
    while self.tmux("show-option", "-wqv", "-t", wid, "@lazy_pending"):
      self.assertLess(time.monotonic(), deadline, "Lazy did not wake float")
      time.sleep(0.02)
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", "float:", "#{pane_dead}"), "0"
    )
    self.assertEqual(
      self.tmux("display-message", "-p", "-t", "float:", "#{pane_current_path}"),
      str(directory),
    )
    self.close_popup()


if __name__ == "__main__":
  unittest.main()
