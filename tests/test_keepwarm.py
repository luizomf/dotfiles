# Copyright (c) 2026 Otávio Miranda

import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
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

  def test_replaces_previous_worker_without_killing_its_own_launcher(self):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      home = root / "home"
      (home / "dotfiles" / "scripts").mkdir(parents=True)
      bin_dir = root / "bin"
      bin_dir.mkdir()
      marker = "keepwarm-fixture-" + uuid.uuid4().hex
      launcher = root / marker
      shutil.copyfile(REPOSITORY / "scripts" / "keepwarm", launcher)
      real_pkill = shutil.which("pkill")
      self.assertIsNotNone(real_pkill)

      # Preserve the real platform's pkill semantics but narrow its match
      # to this fixture. It must never select a user's keepwarm process.
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
      # Block before the first ping; group cleanup below ends this wait.
      sleep = bin_dir / "sleep"
      sleep.write_text("#!/bin/sh\nexec /bin/sleep 300\n", encoding="utf-8")
      sleep.chmod(0o755)
      sannux = bin_dir / "sannux"
      sannux.write_text(
        '#!/bin/sh\ntouch "$HOME/unexpected-runner-call"\nexit 1\n',
        encoding="utf-8",
      )
      sannux.chmod(0o755)
      # Safe: fixed Bash command and a fixture-only process label.
      previous = subprocess.Popen(  # noqa: S603
        ["/bin/bash", "-c", "read -r line", marker + "-previous"],
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
        self.assertEqual(previous.wait(timeout=5), -signal.SIGKILL)
        log = home / "dotfiles" / "scripts" / "keepwarm.log"
        self.assertIn("keepwarm started", log.read_text(encoding="utf-8"))
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


if __name__ == "__main__":
  unittest.main()
