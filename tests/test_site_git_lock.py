"""Exercise the sourced public lock functions against a disposable local repo."""
import os
from pathlib import Path
import platform
import select
import signal
import subprocess
import time
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / "scripts/site_git_automation_lock"


class SiteGitLockTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="site lock fixture ")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name).resolve() / "site"
        (self.repo / ".git").mkdir(parents=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("SITE_GIT_")}
        self.env["SITE_GIT_LOCK_TIMEOUT_SECONDS"] = "0"

    def execute(self, body, overrides=None):
        return subprocess.run(
            ["/bin/bash", "-c", 'set -eu; source "$1"; ' + body,
             "fixture", str(HELPER), str(self.repo)],
            env=self.env | (overrides or {}), capture_output=True, text=True,
            timeout=10,
        )

    def holder(self, body='printf "READY\\n"; IFS= read -r finish', timeout="0"):
        process = subprocess.Popen(
            ["/bin/bash", "-c", 'set -eu; source "$1"; site_git_lock_acquire "$2"; '
             'trap site_git_lock_release EXIT; ' + body,
             "fixture", str(HELPER), str(self.repo)],
            env=self.env | {"SITE_GIT_LOCK_TIMEOUT_SECONDS": timeout},
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=True,
        )
        self.addCleanup(self.stop, process)
        return process

    @staticmethod
    def stop(process):
        # Only the process group created for this individual test is signaled.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate(timeout=5)

    def ready(self, process):
        self.assertTrue(select.select([process.stdout], [], [], 5)[0], "No readiness message")
        line = process.stdout.readline().strip()
        self.assertTrue(line.startswith("READY"), line)
        return line

    def release(self, process):
        output, error = process.communicate("release\n", timeout=5)
        self.assertEqual(process.returncode, 0, output + error)

    def test_native_host_can_acquire_and_release(self):
        result = self.execute('site_git_lock_acquire "$2"; site_git_lock_release')
        self.assertEqual(result.returncode, 0, result.stderr)
        again = self.execute('site_git_lock_acquire "$2"; site_git_lock_release')
        self.assertEqual(again.returncode, 0, again.stderr)

    def test_competing_process_times_out_then_acquires_after_release(self):
        owner = self.holder()
        self.ready(owner)
        start = time.monotonic()
        blocked = self.execute('site_git_lock_acquire "$2"', {"SITE_GIT_LOCK_TIMEOUT_SECONDS": "1"})
        self.assertEqual(blocked.returncode, 75, blocked.stderr)
        self.assertGreaterEqual(time.monotonic() - start, 0.8)
        self.release(owner)
        self.assertEqual(self.execute('site_git_lock_acquire "$2"; site_git_lock_release').returncode, 0)

    def test_killed_owner_does_not_leave_permanent_lock(self):
        owner = self.holder()
        self.ready(owner)
        owner.kill()
        owner.wait(timeout=5)
        # shlock may remove a stale PID file on one attempt and acquire on the
        # next; preserve its existing retry behavior rather than rewriting it.
        result = self.execute('site_git_lock_acquire "$2"; site_git_lock_release',
                              {"SITE_GIT_LOCK_TIMEOUT_SECONDS": "3"})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_timeout_and_missing_tool_fail_closed(self):
        for timeout in ("-1", "1.5", "invalid"):
            result = self.execute('site_git_lock_acquire "$2"', {"SITE_GIT_LOCK_TIMEOUT_SECONDS": timeout})
            self.assertEqual(result.returncode, 64, result.stderr)
        variable = "SITE_GIT_FLOCK_BIN" if platform.system() == "Linux" else "SITE_GIT_SHLOCK_BIN"
        result = self.execute('site_git_lock_acquire "$2"', {variable: "/missing-lock-tool"})
        self.assertEqual(result.returncode, 69, result.stderr)
        self.assertEqual(list((self.repo / ".git").iterdir()), [])

    def test_repeated_acquire_does_not_abandon_existing_lock(self):
        owner = self.holder('if site_git_lock_acquire "$2"; then exit 90; fi; printf "READY\\n"; IFS= read -r finish')
        self.ready(owner)
        blocked = self.execute('site_git_lock_acquire "$2"')
        self.assertEqual(blocked.returncode, 75, blocked.stderr)
        self.release(owner)

    @unittest.skipUnless(platform.system() == "Linux", "Linux descriptor backend")
    def test_waiter_and_new_contender_use_same_persistent_inode(self):
        owner = self.holder()
        self.ready(owner)
        path = self.repo / ".git/om-site-automation.flock"
        inode = path.stat().st_ino
        waiter = self.holder(timeout="4")
        self.assertFalse(select.select([waiter.stdout], [], [], 0.2)[0])
        self.release(owner)
        self.ready(waiter)
        self.assertEqual(path.stat().st_ino, inode)
        self.assertEqual(self.execute('site_git_lock_acquire "$2"').returncode, 75)
        self.release(waiter)
        self.assertEqual(path.stat().st_ino, inode)
        self.assertEqual(self.execute('site_git_lock_acquire "$2"; site_git_lock_release').returncode, 0)
        self.assertEqual(path.stat().st_ino, inode)

    @unittest.skipUnless(platform.system() == "Linux", "Linux descriptor backend")
    def test_child_work_retains_lock_after_owner_crash(self):
        owner = self.holder('sleep 30 & printf "READY %s\\n" "$!"; IFS= read -r finish')
        child = int(self.ready(owner).split()[1])
        owner.kill()
        owner.wait(timeout=5)
        self.assertEqual(self.execute('site_git_lock_acquire "$2"').returncode, 75)
        os.kill(child, signal.SIGTERM)
        result = self.execute('site_git_lock_acquire "$2"; site_git_lock_release',
                              {"SITE_GIT_LOCK_TIMEOUT_SECONDS": "3"})
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(platform.system() == "Linux", "Linux descriptor backend")
    def test_failed_flock_and_legacy_state_are_not_accepted(self):
        failed = self.repo.parent / "failed-flock"
        failed.write_text('#!/bin/sh\nwhile [ "$#" -gt 1 ]; do shift; done\n'
                          '/usr/bin/flock -x "$1" || exit 91\nexit 42\n')
        failed.chmod(0o755)
        result = self.execute('site_git_lock_acquire "$2"', {"SITE_GIT_FLOCK_BIN": str(failed)})
        self.assertEqual(result.returncode, 42, result.stderr)
        # The failing tool acquired the inherited descriptor before returning an
        # error. Reacquire in the SAME shell to detect a leaked locked descriptor.
        result = self.execute('if site_git_lock_acquire "$2"; then exit 90; '
                              'else test "$?" -eq 42; fi; unset SITE_GIT_FLOCK_BIN; '
                              'site_git_lock_acquire "$2"; site_git_lock_release',
                              {"SITE_GIT_FLOCK_BIN": str(failed)})
        self.assertEqual(result.returncode, 0, result.stderr)
        wrong_backend = self.execute('site_git_lock_acquire "$2"',
                                     {"SITE_GIT_SHLOCK_BIN": str(failed)})
        self.assertEqual(wrong_backend.returncode, 64, wrong_backend.stderr)
        legacy = self.repo / ".git/om-site-automation.lock"
        legacy.write_text("12345\n")
        result = self.execute('site_git_lock_acquire "$2"')
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertEqual(legacy.read_text(), "12345\n")

    @unittest.skipUnless(platform.system() == "Linux", "Linux descriptor backend")
    def test_symlink_or_directory_is_not_a_flock_file(self):
        path = self.repo / ".git/om-site-automation.flock"
        other = self.repo.parent / "unrelated"
        other.write_text("preserve\n")
        path.symlink_to(other)
        self.assertEqual(self.execute('site_git_lock_acquire "$2"').returncode, 66)
        self.assertEqual(other.read_text(), "preserve\n")
        path.unlink()
        path.mkdir()
        self.assertEqual(self.execute('site_git_lock_acquire "$2"').returncode, 66)

    @unittest.skipUnless(platform.system() == "Darwin", "macOS legacy protocol")
    def test_macos_override_retains_pid_file_protocol(self):
        self.env["SITE_GIT_SHLOCK_BIN"] = "/usr/bin/shlock"
        owner = self.holder()
        self.ready(owner)
        path = self.repo / ".git/om-site-automation.lock"
        self.assertEqual(int(path.read_text()), owner.pid)
        self.release(owner)
        self.assertFalse(path.exists())

    def test_unknown_os_fails_without_lock_creation(self):
        bin_dir = self.repo.parent / "bin"
        bin_dir.mkdir()
        uname = bin_dir / "uname"
        uname.write_text("#!/bin/sh\nprintf 'UnknownOS\\n'\n")
        uname.chmod(0o755)
        result = self.execute('site_git_lock_acquire "$2"',
                              {"PATH": str(bin_dir) + ":/usr/bin:/bin"})
        self.assertEqual(result.returncode, 69, result.stderr)
        self.assertEqual(list((self.repo / ".git").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
