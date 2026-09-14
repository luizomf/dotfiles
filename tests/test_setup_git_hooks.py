# Copyright (c) 2026 Luiz Otávio Miranda

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SetupGitHooksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.repo = self.root / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        self.env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        self.env.update(
            {
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": str(self.root / "global.gitconfig"),
                "GIT_CONFIG_COUNT": "0",
            }
        )
        self.git("init", "-q")
        shutil.copy2(
            PROJECT_ROOT / "scripts" / "setup_git_hooks",
            self.repo / "scripts" / "setup_git_hooks",
        )
        (self.repo / ".githooks").mkdir()
        for name in (".githooks/pre-commit", "scripts/check_staged"):
            path = self.repo / name
            path.write_text("#!/bin/sh\nexit 0\n")
            path.chmod(0o755)

    def run_command(self, *args: str) -> subprocess.CompletedProcess[str]:
        # Only fixture-controlled executables and arguments are accepted here.
        return subprocess.run(  # noqa: S603
            args,
            cwd=self.repo,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return self.run_command("/usr/bin/git", *args)

    def setup_hooks(self) -> subprocess.CompletedProcess[str]:
        return self.run_command("/bin/bash", "scripts/setup_git_hooks")

    def test_new_checkout_gets_a_local_hook_and_reruns_are_safe(self) -> None:
        for _ in range(2):
            result = self.setup_hooks()
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(
                ".githooks\n",
                self.git("config", "--local", "--get", "core.hooksPath").stdout,
            )
        self.assertFalse((self.root / "global.gitconfig").exists())

    def test_existing_local_or_global_hook_configuration_is_preserved(self) -> None:
        for scope in ("--global", "--local"):
            with self.subTest(scope=scope):
                self.git("config", scope, "core.hooksPath", "custom-hooks")

                result = self.setup_hooks()

                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn("preserved", result.stdout)
                self.assertEqual(
                    "custom-hooks\n",
                    self.git("config", "--get", "core.hooksPath").stdout,
                )
                if scope == "--global":
                    self.assertEqual(
                        1,
                        self.git(
                            "config", "--local", "--get", "core.hooksPath"
                        ).returncode,
                    )
                self.git("config", scope, "--unset", "core.hooksPath")

    def test_existing_default_hook_is_not_disabled(self) -> None:
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 23\n")
        hook.chmod(0o755)

        result = self.setup_hooks()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("preserved", result.stdout)
        self.assertEqual(1, self.git("config", "--get", "core.hooksPath").returncode)
        self.assertEqual("#!/bin/sh\nexit 23\n", hook.read_text())


if __name__ == "__main__":
    unittest.main()
