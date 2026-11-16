# Copyright (c) 2026 Otávio Miranda

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/clear_tts_cache"


class ClearTtsCacheWorkRootTests(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp.cleanup)
    base = Path(self.tmp.name).resolve()
    self.work_root = base / "daily-paper-tts"
    self.work_root.mkdir()
    self.noop = base / "noop"
    self.noop.write_text("#!/bin/sh\nexit 0\n")
    self.noop.chmod(0o755)
    self.env = {
      **os.environ,
      "PROJECTS_DIR": str(base / "projects"),
      "OMNIVOICE_CLEAR_BIN": str(self.noop),
      "LOUDTERM_OUTPUT_DIR": str(base / "missing-loudterm"),
      "EDGETTS_DIR": str(base / "missing-edgetts"),
      "EDGETTS_BIN": str(self.noop),
      "DAILY_PAPER_TTS_WORK_ROOT": str(self.work_root),
    }
    self.env.pop("OM_PATHS_FILE", None)

  def job(self, name: str, *, completed: bool) -> Path:
    job = self.work_root / name
    (job / "cache").mkdir(parents=True)
    (job / "cache/chunk_0001_abc.wav").write_bytes(b"RIFF")
    (job / "worker.wav").write_bytes(b"RIFF")
    if completed:
      (job / "completed").write_text("")
    return job

  def run_script(self) -> None:
    subprocess.run([str(SCRIPT)], env=self.env, check=True)  # noqa: S603

  def test_removes_completed_jobs_and_keeps_root(self):
    done = self.job("token-a", completed=True)
    self.run_script()
    self.assertFalse(done.exists())
    self.assertTrue(self.work_root.is_dir())

  def test_keeps_jobs_without_completed_marker(self):
    running = self.job("token-b", completed=False)
    self.run_script()
    self.assertTrue((running / "worker.wav").exists())

  def test_does_not_follow_symlinked_job(self):
    outside = Path(self.tmp.name) / "outside"
    (outside / "keep").mkdir(parents=True)
    (outside / "completed").write_text("")
    (self.work_root / "link").symlink_to(outside, target_is_directory=True)
    self.run_script()
    self.assertTrue((outside / "keep").exists())

  def test_missing_work_root_is_fine(self):
    self.work_root.rmdir()
    self.run_script()
    self.assertFalse(self.work_root.exists())


if __name__ == "__main__":
  unittest.main()
