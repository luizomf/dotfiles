"""MRU regression tests using a disposable tmux server, never the user's server."""

import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
TMUX = shutil.which("tmux")


@unittest.skipUnless(TMUX and shutil.which("fzf"), "tmux and fzf are required")
class WindowMRUTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tmux-mru-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.socket = str(self.path / "socket")
        self.env = {key: value for key, value in os.environ.items() if key != "TMUX"}
        self.server = subprocess.Popen(
            [TMUX, "-D", "-S", self.socket, "-f", "/dev/null"],
            env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        self.addCleanup(self.stop_server)
        # A bounded readiness wait belongs to this disposable test fixture.
        for _ in range(100):
            if (self.path / "socket").exists():
                break
            if self.server.poll() is not None:
                self.fail(self.server.stderr.read().decode())
            time.sleep(0.01)
        self.tmux("new-session", "-d", "-s", "alpha", "-n", "first", "sleep 300")
        self.tmux("new-window", "-d", "-t", "alpha:", "-n", "second", "sleep 300")
        self.tmux("new-window", "-d", "-t", "alpha:", "-n", "third", "sleep 300")
        self.tmux("new-session", "-d", "-s", "beta", "-n", "other", "sleep 300")
        self.hooks = ROOT / "tmux/window-mru.conf"
        if self.hooks.exists():
            self.tmux("source-file", str(self.hooks))

    def stop_server(self):
        self.server.terminate()
        try:
            self.server.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            self.server.kill()
            self.server.communicate(timeout=5)

    def tmux(self, *args):
        return subprocess.check_output(
            [TMUX, "-S", self.socket, *args], env=self.env, text=True, timeout=5,
        ).strip()

    def rank(self, target):
        value = self.tmux("show-options", "-wqv", "-t", target, "@window_mru")
        return int(value or 0)

    def rows(self):
        # Replace only the popup with a capture, leaving actual tmux formatting
        # and the production list/sort pipeline intact.
        wrapper = self.path / "tmux"
        wrapper.write_text(
            "#!/bin/sh\nexec " + shlex.quote(TMUX) + " -S "
            + shlex.quote(self.socket) + ' "$@"\n'
        )
        wrapper.chmod(0o755)
        popup = self.path / "fzf"
        popup.write_text('#!/bin/sh\ncat > "$CAPTURE"\n')
        popup.chmod(0o755)
        capture = self.path / "rows"
        env = dict(self.env, PATH=str(self.path) + os.pathsep + self.env["PATH"],
                   CAPTURE=str(capture))
        subprocess.run(["bash", str(ROOT / "tmux/scripts/fzf.sh")],
                       env=env, check=True, timeout=5)
        return [line.split("\t", 1)[0] for line in capture.read_text().splitlines()]

    def test_unvisited_windows_have_stable_order(self):
        self.assertEqual(self.rows(), ["alpha:0", "alpha:1", "alpha:2", "beta:0"])

    def test_visits_sort_newest_first_even_within_one_second(self):
        self.tmux("select-window", "-t", "alpha:2")
        self.tmux("select-window", "-t", "alpha:1")
        self.assertGreater(self.rank("alpha:1"), self.rank("alpha:2"))
        self.assertEqual(self.rows(), ["alpha:1", "alpha:2", "alpha:0", "beta:0"])

    def test_next_previous_and_last_window_are_tracked(self):
        self.tmux("next-window", "-t", "alpha")
        first = self.rank("alpha:1")
        self.tmux("previous-window", "-t", "alpha")
        second = self.rank("alpha:0")
        self.tmux("last-window", "-t", "alpha")
        self.assertGreater(first, 0)
        self.assertGreater(second, first)
        self.assertGreater(self.rank("alpha:1"), second)

    def test_reload_preserves_history_and_does_not_duplicate_hooks(self):
        self.tmux("select-window", "-t", "alpha:2")
        before = self.rank("alpha:2")
        self.tmux("source-file", str(self.hooks))
        self.tmux("select-window", "-t", "alpha:1")
        self.assertEqual(self.rank("alpha:1"), before + 1)
        self.assertEqual(self.rank("alpha:2"), before)

    def test_client_hooks_update_the_target_session_window(self):
        # Exercise the real hook bodies without attaching an interactive client.
        self.tmux("set-hook", "-R", "-t", "alpha:0", "client-attached")
        before = self.rank("alpha:0")
        self.tmux("set-hook", "-R", "-t", "beta:0", "client-session-changed")
        self.assertGreater(before, 0)
        self.assertGreater(self.rank("beta:0"), before)
        self.assertEqual(self.rows()[0], "beta:0")

    def test_real_client_attach_and_session_switch(self):
        subprocess.run(
            [TMUX, "-S", self.socket, "-C", "attach-session", "-t", "alpha"],
            input="switch-client -t beta\ndetach-client\n", text=True,
            capture_output=True, env=self.env, check=True, timeout=5,
        )
        self.assertGreater(self.rank("alpha:0"), 0)
        self.assertGreater(self.rank("beta:0"), self.rank("alpha:0"))
        self.assertEqual(self.rows()[0], "beta:0")

    def test_renaming_and_renumbering_preserve_history(self):
        self.tmux("select-window", "-t", "alpha:2")
        before = self.rank("alpha:2")
        self.tmux("rename-window", "-t", "alpha:2", "renamed")
        self.assertEqual(self.rank("alpha:2"), before)
        self.tmux("select-window", "-t", "alpha:1")
        self.tmux("move-window", "-d", "-s", "alpha:2", "-t", "alpha:8")
        self.assertEqual(self.rank("alpha:8"), before)
        self.assertEqual(self.rows()[:2], ["alpha:1", "alpha:8"])

    def test_search_still_ranks_by_relevance(self):
        self.tmux("rename-window", "-t", "alpha:0", "needle")
        self.tmux("select-window", "-t", "alpha:2")
        self.rows()
        result = subprocess.run(
            [shutil.which("fzf"), "--filter=needle", "--algo=v2", "--tiebreak=length"],
            input=(self.path / "rows").read_text(), text=True,
            capture_output=True, env=self.env, check=True, timeout=5,
        )
        self.assertEqual(result.stdout.split("\t", 1)[0], "alpha:0")

    def test_output_does_not_count_as_a_visit(self):
        self.tmux("select-window", "-t", "alpha:1")
        before = self.rank("alpha:1")
        self.tmux("respawn-pane", "-k", "-t", "alpha:2", "printf noise; sleep 300")
        self.assertEqual(self.rank("alpha:2"), 0)
        self.assertEqual(self.rank("alpha:1"), before)


if __name__ == "__main__":
    unittest.main()
