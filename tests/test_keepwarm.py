# Copyright (c) 2026 Otávio Miranda

import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from contextlib import suppress
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]


class KeepwarmTests(unittest.TestCase):
  def test_once_checks_all_fifteen_ssh_targets_without_replacing_a_worker(self):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      home = root / "home"
      (home / "dotfiles/scripts").mkdir(parents=True)
      bin_dir = root / "bin"
      bin_dir.mkdir()
      state_file = home / ".cache/keepwarm/current"
      state_file.parent.mkdir(parents=True)
      state_file.write_text("existing-worker-token\n")
      ssh_log = root / "ssh.jsonl"
      ssh = bin_dir / "ssh"
      ssh.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "record = {'args': sys.argv[1:], 'prompt': sys.stdin.read()}\n"
        f"with open({str(ssh_log)!r}, 'a') as output:\n"
        "    output.write(json.dumps(record) + '\\n')\n"
        "if sys.argv[-2] == os.environ.get('FAIL_HOST'):\n"
        "    print('fixture missing login', file=sys.stderr)\n"
        "    sys.exit(23)\n"
        "print('Oi')\n",
        encoding="utf-8",
      )
      ssh.chmod(0o755)
      for name, body in (
        ("pkill", 'touch "$HOME/unexpected-kill"'),
        ("sleep", "exec /bin/sleep 300"),
        ("codex", "exit 91"),
        ("pi", "exit 92"),
        ("sannux", "exit 93"),
      ):
        command = bin_dir / name
        command.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        command.chmod(0o755)
      for failed_host in ("", "m4128"):
        with self.subTest(failed_host=failed_host):
          ssh_log.write_text("", encoding="utf-8")
          with (root / "output").open("w+", encoding="utf-8") as output:
            # Safe: all SSH/agent/process-replacement commands are fixture-only.
            process = subprocess.Popen(  # noqa: S603
              ["/bin/bash", str(REPOSITORY / "scripts/keepwarm"), "--once"],
              env={
                **os.environ,
                "HOME": str(home),
                "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                "FAIL_HOST": failed_host,
              },
              stdin=subprocess.DEVNULL,
              stdout=output,
              stderr=output,
              start_new_session=True,
            )
            try:
              status = process.wait(timeout=10)
            finally:
              with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
              process.wait(timeout=5)
            output.seek(0)
            stdout = output.read()
          records = [json.loads(line) for line in ssh_log.read_text().splitlines()]
          self.assertEqual(len(records), 15)
          self.assertFalse((home / "unexpected-kill").exists())
          self.assertEqual(state_file.read_text(), "existing-worker-token\n")
          self.assertEqual(status, int(bool(failed_host)))
          for index, host in enumerate(("m132", "m4128", "fedoraair")):
            host_records = records[index * 5 : (index + 1) * 5]
            self.assertTrue(all(row["args"][-2] == host for row in host_records))
            for row in host_records:
              self.assertEqual(
                row["prompt"], "Reply with exactly: Oi. Do not use tools.\n"
              )
              self.assertIn("BatchMode=yes", row["args"])
              self.assertIn("ConnectTimeout=10", row["args"])
              shell = shlex.split(row["args"][-1])
              self.assertEqual(shell[:5], ["zsh", "-l", "-i", "+m", "-c"])
            nested = shlex.split(shlex.split(host_records[-1]["args"][-1])[-1])
            self.assertEqual(
              nested[:9],
              [
                "sannux",
                "compose",
                "pi",
                "run",
                "--rm",
                "-T",
                "--entrypoint",
                "codex",
                "agent",
              ],
            )
            self.assertIn(f"{host}/codex-in-pi ping", stdout)
          self.assertIn(
            "10 successful, 5 failed" if failed_host else "15 successful, 0 failed",
            stdout,
          )

  def prepare_replacement_fixture(self, root: Path) -> tuple[Path, Path]:
    bin_dir = root / "bin"
    bin_dir.mkdir()
    marker = "keepwarm-fixture-" + uuid.uuid4().hex
    launcher = root / marker
    shutil.copyfile(REPOSITORY / "scripts" / "keepwarm", launcher)
    real_pkill = shutil.which("pkill")
    self.assertIsNotNone(real_pkill)

    # Preserve original-code reproduction, but ONLY match this unique fixture.
    pkill = bin_dir / "pkill"
    pkill.write_text(
      f"#!{sys.executable}\n"
      "import os, sys\n"
      "args = sys.argv[1:]\n"
      "assert args[-1] == '[k]eepwarm'\n"
      f"args[-1] = '[k]' + {marker[1:]!r}\n"
      f"os.execv({real_pkill!r}, [{real_pkill!r}, *args])\n",
      encoding="utf-8",
    )
    pkill.chmod(0o755)
    # Accelerate only waits, never run a real network request.
    commands = {
      "sleep": 'printf "%s\\n" "$PPID" >> "$HOME/workers"\nexec /bin/sleep 0.05',
      "ssh": "exit 0",
      "sannux": 'touch "$HOME/unexpected-runner-call"; exit 1',
    }
    for name, body in commands.items():
      command = bin_dir / name
      command.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
      command.chmod(0o755)
    return bin_dir, launcher

  def assert_worker_stopped(self, pid: str) -> None:
    deadline = time.monotonic() + 5
    while True:
      # Read only the known fixture PID; an unreaped zombie is also done.
      status = subprocess.run(  # noqa: S603
        ["/bin/ps", "-p", pid, "-o", "stat="],
        capture_output=True,
        text=True,
        check=False,
      )
      if status.returncode or status.stdout.strip().startswith("Z"):
        return
      self.assertLess(time.monotonic(), deadline, "old worker still alive")
      time.sleep(0.02)

  def test_replacement_preserves_unrelated_editor_observer_and_caller(self):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      home = root / "home"
      (home / "dotfiles" / "scripts").mkdir(parents=True)
      bin_dir, launcher = self.prepare_replacement_fixture(root)
      # Safe: fixed Bash command and a fixture-only process label.
      previous = subprocess.Popen(  # noqa: S603
        ["/bin/bash", "-c", "read -r line", "nvim", str(launcher)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
      )
      current = None
      try:
        # Safe: execute only the copied repository script with fixture PATH/HOME.
        current = subprocess.Popen(  # noqa: S603
          ["/bin/bash", str(launcher)],
          env={
            **os.environ,
            "HOME": str(home),
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
          },
          stdin=subprocess.DEVNULL,
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL,
          start_new_session=True,
        )
        self.assertEqual(current.wait(timeout=5), 0)
        self.assertIsNone(previous.poll(), "unrelated editor must survive startup")
        log = home / "dotfiles" / "scripts" / "keepwarm.log"
        self.assertIn("keepwarm started", log.read_text(encoding="utf-8"))
        deadline = time.monotonic() + 5
        while not (home / "workers").exists():
          self.assertLess(time.monotonic(), deadline)
          time.sleep(0.02)
        old_worker = (home / "workers").read_text().splitlines()[0]
        # Reuse a caller whose command line also contains the script path.
        replacement = subprocess.Popen(  # noqa: S603
          ["/bin/bash", "-c", 'bash "$1"; read -r line', "observer", str(launcher)],
          env={
            **os.environ,
            "HOME": str(home),
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
          },
          stdin=subprocess.PIPE,
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL,
          start_new_session=True,
        )
        try:
          deadline = time.monotonic() + 5
          while "worker replaced, exiting" not in log.read_text(encoding="utf-8"):
            self.assertLess(time.monotonic(), deadline, "old worker did not retire")
            time.sleep(0.02)
          self.assertIsNone(previous.poll())
          self.assertIsNone(replacement.poll(), "observer/caller must survive")
          self.assertEqual(log.read_text().count("keepwarm started"), 2)
          self.assert_worker_stopped(old_worker)
          self.assertIsNone(replacement.poll())
        finally:
          with suppress(ProcessLookupError):
            os.killpg(replacement.pid, signal.SIGKILL)
          replacement.wait(timeout=5)
          if replacement.stdin:
            replacement.stdin.close()
        self.assertFalse((home / "unexpected-runner-call").exists())
      finally:
        for process in (current, previous):
          if process is None:
            continue
          with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
          process.wait(timeout=5)
        if previous.stdin:
          previous.stdin.close()

  def test_concurrent_launches_replace_stale_state_and_leave_one_worker(self):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      home = root / "home"
      (home / "dotfiles/scripts").mkdir(parents=True)
      state = home / ".cache/keepwarm/current"
      state.parent.mkdir(parents=True)
      state.write_text("stale-or-malformed-token\n")
      bin_dir, launcher = self.prepare_replacement_fixture(root)
      processes: list[subprocess.Popen[bytes]] = []
      try:
        for _ in range(5):
          # Keep each accepted PID for cleanup even if a later spawn fails.
          processes.append(  # noqa: PERF401
            subprocess.Popen(  # noqa: S603
              ["/bin/bash", str(launcher)],
              env={
                **os.environ,
                "HOME": str(home),
                "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
              },
              stdin=subprocess.DEVNULL,
              stdout=subprocess.DEVNULL,
              stderr=subprocess.DEVNULL,
              start_new_session=True,
            )
          )
        for process in processes:
          self.assertEqual(process.wait(timeout=5), 0)
        log = home / "dotfiles/scripts/keepwarm.log"
        deadline = time.monotonic() + 5
        while log.read_text().count("worker replaced, exiting") != len(processes) - 1:
          self.assertLess(time.monotonic(), deadline, "losing workers did not retire")
          time.sleep(0.02)
        self.assertEqual(log.read_text().count("keepwarm started"), 5)
        # A continuing wait from the winner proves it did not retire as well.
        waits = home / "workers"
        before = waits.read_text() if waits.exists() else ""
        deadline = time.monotonic() + 5
        while not waits.exists() or waits.read_text() == before:
          self.assertLess(time.monotonic(), deadline, "winning worker stopped")
          time.sleep(0.02)
        self.assertNotEqual(state.read_text(), "stale-or-malformed-token\n")
      finally:
        for process in processes:
          with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
          process.wait(timeout=5)

  def test_replacement_finishes_inflight_request_but_starts_no_more_old_requests(self):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      home = root / "home"
      (home / "dotfiles/scripts").mkdir(parents=True)
      bin_dir = root / "bin"
      bin_dir.mkdir()
      commands = {
        "sleep": "exec /bin/sleep 0.01",
        "pkill": 'touch "$HOME/unexpected-kill"; exit 1',
        "ssh": (
          'printf "%s\\n" "$FIXTURE_WORKER" >> "$HOME/requests"\n'
          'if [ "$FIXTURE_WORKER" = old ]; then\n'
          '  while [ ! -f "$HOME/release" ]; do /bin/sleep 0.01; done\n'
          "fi\n"
          "printf 'Oi\\n'"
        ),
      }
      for name, body in commands.items():
        command = bin_dir / name
        command.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        command.chmod(0o755)
      processes: list[subprocess.Popen[bytes]] = []
      try:
        for worker in ("old", "new"):
          process = subprocess.Popen(  # noqa: S603
            ["/bin/bash", str(REPOSITORY / "scripts/keepwarm")],
            env={
              **os.environ,
              "HOME": str(home),
              "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
              "FIXTURE_WORKER": worker,
            },
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
          )
          processes.append(process)
          self.assertEqual(process.wait(timeout=5), 0)
          deadline = time.monotonic() + 5
          requests = home / "requests"
          while (
            not requests.exists() or worker not in requests.read_text().splitlines()
          ):
            self.assertLess(time.monotonic(), deadline, "fixture request not reached")
            time.sleep(0.02)
        log = home / "dotfiles/scripts/keepwarm.log"
        self.assertNotIn("worker replaced, exiting", log.read_text())
        (home / "release").touch()
        deadline = time.monotonic() + 5
        while "worker replaced, exiting" not in log.read_text():
          self.assertLess(time.monotonic(), deadline, "inflight worker did not retire")
          time.sleep(0.02)
        self.assertEqual((home / "requests").read_text().splitlines().count("old"), 1)
        self.assertIn("m132/codex-host ping ok: Oi", log.read_text())
        self.assertFalse((home / "unexpected-kill").exists())
      finally:
        for process in processes:
          with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
          process.wait(timeout=5)


if __name__ == "__main__":
  unittest.main()
