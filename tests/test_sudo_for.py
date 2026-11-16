# Copyright (c) 2026 Otávio Miranda

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sudo_for"
USER = "tester"


class SudoForTests(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp.cleanup)
    base = Path(self.tmp.name).resolve()
    self.dir = base / "sudoers.d"
    self.dir.mkdir()
    self.own = self.dir / USER
    self.own.write_text(f"{USER} ALL=(ALL) NOPASSWD: /usr/bin/true\n")
    bin_dir = base / "bin"
    bin_dir.mkdir()
    # Fake sudo runs the command as the caller; fake visudo can be told to fail.
    (bin_dir / "sudo").write_text('#!/bin/sh\nexec "$@"\n')
    (bin_dir / "visudo").write_text(
      '#!/bin/sh\n[ -n "$FAKE_VISUDO_FAIL" ] && exit 1\nexit 0\n'
    )
    for name in ("sudo", "visudo"):
      (bin_dir / name).chmod(0o755)
    self.env = {
      **os.environ,
      "PATH": f"{bin_dir}:{os.environ['PATH']}",
      "SUDO_FOR_DIR": str(self.dir),
      "SUDO_FOR_OWNER": f"{os.getuid()}:{os.getgid()}",
      "USER": USER,
    }
    self.grant = self.dir / f"zz-sudo-for-{USER}"

  def run_script(self, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
      [str(SCRIPT), *args],
      env={**self.env, **env},
      capture_output=True,
      text=True,
      check=False,
    )

  def wait_gone(self, path: Path, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
      if not path.exists():
        return True
      time.sleep(0.1)
    return not path.exists()

  def test_grants_then_expires_without_touching_own_file(self):
    result = self.run_script("1s")
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn(f"{USER} ALL=(ALL) NOPASSWD: ALL", self.grant.read_text())
    self.assertTrue(self.wait_gone(self.grant, 5))
    self.assertEqual(
      self.own.read_text(), f"{USER} ALL=(ALL) NOPASSWD: /usr/bin/true\n"
    )

  def test_rerun_extends_and_old_timer_does_not_cut_it(self):
    self.assertEqual(self.run_script("1s").returncode, 0)
    self.assertEqual(self.run_script("4s").returncode, 0)
    time.sleep(2)
    self.assertTrue(self.grant.exists())
    self.assertTrue(self.wait_gone(self.grant, 5))

  def test_revoke_removes_now(self):
    self.assertEqual(self.run_script("1m").returncode, 0)
    result = self.run_script("--revoke")
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse(self.grant.exists())
    self.assertTrue(self.own.exists())

  def test_invalid_validation_installs_nothing(self):
    result = self.run_script("1m", FAKE_VISUDO_FAIL="1")
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(sorted(p.name for p in self.dir.iterdir()), [USER])

  def test_rejects_bad_duration(self):
    for bad in ("", "abc", "0", "5x", "-3m"):
      result = self.run_script(bad)
      self.assertNotEqual(result.returncode, 0, bad)
    self.assertFalse(self.grant.exists())

  def test_status_reports_grant(self):
    self.assertEqual(self.run_script("--status").stdout.strip(), "No temporary grant.")
    self.run_script("1m")
    self.assertIn("expires", self.run_script("--status").stdout)
    self.run_script("--revoke")


if __name__ == "__main__":
  unittest.main()
