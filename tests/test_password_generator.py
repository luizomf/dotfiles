# Copyright (c) 2026 Luiz Otávio Miranda
"""Exercise password character selection through the CLI."""

import string
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/password_generator"


class PasswordGeneratorTests(unittest.TestCase):
  def run_generator(self, *arguments: str) -> subprocess.CompletedProcess[str]:
    # Absolute interpreter and repository script; arguments are fixed test cases.
    return subprocess.run(  # noqa: S603
      [sys.executable, str(SCRIPT), *arguments],
      text=True,
      capture_output=True,
      check=False,
      timeout=5,
    )

  def test_punctuation_can_be_disabled(self):
    result = self.run_generator("--no-punctuation")
    self.assertEqual(result.returncode, 0, result.stderr)
    password = result.stdout.rstrip("\n")
    self.assertEqual(len(password), 24)
    self.assertTrue(set(password) <= set(string.ascii_letters + string.digits))
    self.assertEqual(result.stderr, "")

  def test_disabling_every_character_group_reports_usage_error(self):
    result = self.run_generator(
      "--no-punctuation", "--no-lower", "--no-upper", "--no-digits"
    )
    self.assertEqual(result.returncode, 2)
    self.assertIn("enable at least one character group", result.stderr)
    self.assertNotIn("Traceback", result.stderr)
    self.assertEqual(result.stdout, "")


if __name__ == "__main__":
  unittest.main()
