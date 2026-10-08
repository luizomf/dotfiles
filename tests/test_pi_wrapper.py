# Copyright (c) 2026 Otávio Miranda

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]


class PiWrapperTests(unittest.TestCase):
  def test_headless_calls_skip_terminal_title_and_reach_pi(self):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      bin_dir = root / "bin"
      bin_dir.mkdir()
      real_pi = bin_dir / "pi"
      real_pi.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n", encoding="utf-8")
      real_pi.chmod(0o755)
      title = bin_dir / "title"
      title.write_text(
        '#!/bin/sh\ntouch "$HOME/title-was-called"\nexit 1\n', encoding="utf-8"
      )
      title.chmod(0o755)
      for name in ("", "named run"):
        with self.subTest(name=name):
          # Safe: real wrapper with fixture executables before the inherited PATH.
          result = subprocess.run(  # noqa: S603
            [str(REPOSITORY / "scripts/pi"), "-p", "hello"],
            env={
              **os.environ,
              "HOME": str(root),
              "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
              "t": name,
            },
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
          )
          self.assertEqual(result.returncode, 0, result.stderr)
          expected = ["--no-skills", "--skill", f"{root}/.pi/agent/skills"]
          if name:
            expected.extend(["--name", name])
          self.assertEqual(result.stdout.splitlines(), [*expected, "-p", "hello"])
          self.assertFalse((root / "title-was-called").exists())


if __name__ == "__main__":
  unittest.main()
