# Copyright (c) 2026 Otávio Miranda

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]


class TestModelsTests(unittest.TestCase):
  def test_nested_codex_failure_is_visible_and_does_not_skip_other_checks(self):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      home = root / "home"
      home.mkdir()
      scripts = root / "scripts"
      scripts.mkdir()
      projects = root / "projects"
      daily = projects / "daily-paper/runners/run-pi-ephemeral.sh"
      daily.parent.mkdir(parents=True)
      launcher = scripts / "test_models"
      shutil.copyfile(REPOSITORY / "scripts/test_models", launcher)
      paths = root / "paths.sh"
      paths.write_text(
        f"export PROJECTS_DIR='{projects}'\nexport LOCAL_MODEL=fixture-local\n",
        encoding="utf-8",
      )
      fake_agent = (
        "#!/bin/sh\n"
        'if [ "$1" = compose ] && [ "$2" = pi ]; then\n'
        '  printf "fixture nested Codex has no login\\n" >&2\n'
        "  exit 23\n"
        "fi\n"
        "printf 'OK\\n'\n"
      )
      for name in ("codex", "pi", "sannux", "sannux_ephemeral", "sannux_agy_stdin"):
        executable = scripts / name
        executable.write_text(fake_agent, encoding="utf-8")
        executable.chmod(0o755)
      daily.write_text(fake_agent, encoding="utf-8")
      daily.chmod(0o755)
      # Safe: copied launcher, synthetic HOME/config, all external runners fake.
      result = subprocess.run(  # noqa: S603
        ["/bin/bash", str(launcher)],
        env={
          **os.environ,
          "HOME": str(home),
          "OM_PATHS_FILE": str(paths),
          "PATH": f"{scripts}{os.pathsep}{os.environ['PATH']}",
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
      )
      self.assertNotEqual(result.returncode, 0)
      self.assertIn("FAIL: Codex inside Pi persistent home /", result.stdout)
      self.assertIn("(exit 23)", result.stdout)
      self.assertIn("PASS: Daily Pi ephemeral home /", result.stdout)
      self.assertIn("Failures: 3", result.stdout)


if __name__ == "__main__":
  unittest.main()
