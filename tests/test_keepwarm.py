import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]


class KeepwarmTests(unittest.TestCase):
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
            previous = subprocess.Popen(
                ["/bin/bash", "-c", "read -r line", marker + "-previous"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            current = None
            try:
                current = subprocess.Popen(
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
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=5)
                if previous.stdin:
                    previous.stdin.close()


if __name__ == "__main__":
    unittest.main()
