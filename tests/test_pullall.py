import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PullAllTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pullall fixture ")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.projects = self.home / "projects"
        self.projects.mkdir()
        self.bin = self.home / "bin"
        self.bin.mkdir()
        for name in ["mktemp", "find", "rm"]:
            executable = shutil.which(name)
            self.assertIsNotNone(executable)
            (self.bin / name).symlink_to(str(executable))
        self.git = shutil.which("git")
        self.assertIsNotNone(self.git)
        self.timeout = shutil.which("gtimeout") or shutil.which("timeout")
        self.assertIsNotNone(self.timeout, "GNU coreutils timeout is required")
        timeout = self.bin / "timeout"
        timeout.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            "# Scale only the production deadline/grace, not process supervision.\n"
            "args = [{'60s': '0.5s', '--kill-after=5s': '--kill-after=0.2s'}.get(a, a) for a in sys.argv[1:]]\n"
            f"os.execv({self.timeout!r}, [{self.timeout!r}, *args])\n"
        )
        timeout.chmod(0o755)
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "PROJECTS_DIR": str(self.projects),
            "PATH": str(self.bin),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "TMPDIR": str(self.home),
        }
        shim = self.bin / "git"
        shim.write_text(
            f"#!{sys.executable}\n"
            "import os, pathlib, signal, sys, time\n"
            "args = sys.argv[1:]\n"
            "if args[2] == 'pull':\n"
            " with (pathlib.Path(os.environ['HOME']) / 'pulls').open('a') as log:\n"
            "  log.write(pathlib.Path(args[1]).name + '\\n')\n"
            " if pathlib.Path(args[1]).name == os.environ.get('STALLED_REPO'):\n"
            "  if os.environ.get('IGNORE_TERM'):\n"
            "   signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            "   child = os.fork()\n"
            "   role = 'parent' if child else 'child'\n"
            "   (pathlib.Path(os.environ['HOME']) / (role + '.pid')).write_text(str(os.getpid()))\n"
            "  time.sleep(2)  # Bounded even before timeout support exists.\n"
            " sys.exit(17 if pathlib.Path(args[1]).name == 'failed' else 0)\n"
            f"os.execv({self.git!r}, [{self.git!r}, *args])\n"
        )
        shim.chmod(0o755)
        prline = self.bin / "prline"
        prline.write_text("#!/bin/sh\nexit 0\n")
        prline.chmod(0o755)
        self.repository(self.home / "dotfiles")

    def repository(self, path):
        subprocess.run(
            [str(self.git), "init", "-q", str(path)],
            env=self.env,
            check=True,
            capture_output=True,
        )
        return path

    def run_pullall(self, **env):
        return subprocess.run(
            ["/bin/bash", str(ROOT / "scripts/pullall")],
            cwd=self.home,
            env={**self.env, **env},
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_mixed_outcomes_are_reported_without_stopping_other_repositories(self):
        self.repository(self.projects / "failed")
        self.repository(self.projects / "updated")
        dirty = self.repository(self.projects / "dirty")
        (dirty / "work.txt").write_text("uncommitted work")
        (self.projects / "ordinary directory").mkdir()
        broken = self.projects / "broken"
        broken.mkdir()
        (broken / ".git").write_text("gitdir: /nonexistent-fixture-git")
        result = self.run_pullall()
        self.assertEqual(result.returncode, 1, result.stderr)
        summary = result.stdout.split("pullall summary:")[-1]
        self.assertIn("2 updated, 1 dirty, 1 non-repository, 2 failed", summary)
        for reason in ["pull", "inspection"]:
            self.assertIn("FAILED: " + reason, summary)
        self.assertIn(str(broken), summary)
        self.assertEqual(
            set((self.home / "pulls").read_text().splitlines()),
            {"dotfiles", "failed", "updated"},
        )
        self.assertEqual((dirty / "work.txt").read_text(), "uncommitted work")

    def test_timed_out_pull_is_reported_and_remaining_repositories_continue(self):
        self.repository(self.projects / "updated")
        result = self.run_pullall(STALLED_REPO="dotfiles")
        self.assertEqual(result.returncode, 1, result.stderr)
        summary = result.stdout.split("pullall summary:")[-1]
        self.assertIn("1 updated, 0 dirty, 0 non-repository, 1 failed", summary)
        self.assertIn("FAILED: pull timeout", summary)
        self.assertIn(str(self.home / "dotfiles"), summary)
        self.assertIn("exit 124", summary)
        self.assertEqual(
            (self.home / "pulls").read_text().splitlines(), ["dotfiles", "updated"]
        )

    def test_stuck_pull_and_child_are_killed_before_continuing(self):
        self.repository(self.projects / "updated")
        result = self.run_pullall(STALLED_REPO="dotfiles", IGNORE_TERM="1")
        self.assertEqual(result.returncode, 1, result.stderr)
        summary = result.stdout.split("pullall summary:")[-1]
        self.assertIn("FAILED: pull timeout or SIGKILL", summary)
        self.assertIn(str(self.home / "dotfiles"), summary)
        self.assertIn("exit 137", summary)
        self.assertEqual(
            (self.home / "pulls").read_text().splitlines(), ["dotfiles", "updated"]
        )
        for role in ["parent", "child"]:
            pid = (self.home / (role + ".pid")).read_text()
            process = subprocess.run(
                ["/bin/ps", "-p", pid, "-o", "stat="],
                capture_output=True,
                text=True,
                timeout=5,
            )
            self.assertIn(process.returncode, [0, 1], process.stderr)
            # An orphan zombie may briefly await OS reaping; it cannot run.
            self.assertTrue(
                not process.stdout.strip() or process.stdout.strip().startswith("Z"),
                process.stdout,
            )

    def test_gtimeout_fallback_keeps_deadline_when_timeout_is_incompatible(self):
        (self.bin / "timeout").rename(self.bin / "gtimeout")
        incompatible = self.bin / "timeout"
        incompatible.write_text("#!/bin/sh\nprintf 'not a GNU utility\\n'\nexit 0\n")
        incompatible.chmod(0o755)
        result = self.run_pullall(STALLED_REPO="dotfiles")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAILED: pull timeout after 60s", result.stdout)
        self.assertIn("exit 124", result.stdout)

    def test_missing_timeout_refuses_pulls_with_a_dependency_failure_summary(self):
        (self.bin / "timeout").unlink()
        result = self.run_pullall()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAILED: GNU timeout/gtimeout required", result.stdout)
        self.assertFalse((self.home / "pulls").exists())

    def test_clean_run_and_dirty_skips_are_successful(self):
        dirty = self.repository(self.projects / "dirty")
        (dirty / "work.txt").write_text("keep me")
        result = self.run_pullall()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 updated, 1 dirty, 0 non-repository, 0 failed", result.stdout)

    def test_partial_enumeration_is_not_treated_as_a_complete_project_list(self):
        self.repository(self.projects / "unlisted")
        find = self.bin / "find"
        find.unlink()
        find.write_text(
            "#!/bin/sh\nprintf '%s\\0' \"$PROJECTS_DIR/unlisted\"\nexit 22\n"
        )
        find.chmod(0o755)
        result = self.run_pullall()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAILED: project enumeration", result.stdout)
        self.assertEqual((self.home / "pulls").read_text().splitlines(), ["dotfiles"])

    def test_setup_failures_still_summarize_completed_dotfiles_update(self):
        for env, failure in [
            ({"PROJECTS_DIR": ""}, "projects directory unavailable"),
            ({"TMPDIR": str(self.home / "missing")}, "repository list creation"),
        ]:
            with self.subTest(env=env):
                result = self.run_pullall(**env)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("pullall summary: 1 updated", result.stdout)
                self.assertIn("FAILED: " + failure, result.stdout)


if __name__ == "__main__":
    unittest.main()
