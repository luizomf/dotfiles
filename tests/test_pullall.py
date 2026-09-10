"""Exercise pullall through its command-line interface without network access."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/pullall"


class PullAllTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pullall fixture ")
        self.root = Path(self.temporary.name)
        self.home = self.root / "home with spaces"
        self.projects = self.home / "projects with spaces"
        self.dotfiles = self.home / "dotfiles"
        self.project = self.projects / "example project"
        self.non_repository = self.projects / "not a repository"
        for directory in (self.dotfiles, self.project, self.non_repository):
            directory.mkdir(parents=True)
        for repository in (self.dotfiles, self.project):
            (repository / ".fake-git").touch()

        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        self.log = self.root / "git-pulls"
        git = fake_bin / "git"
        git.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
repository=$PWD
if [[ ${1:-} == -C ]]; then
  repository=$2
  shift 2
fi
case ${1:-} in
  status) [[ -f $repository/.fake-git ]] ;;
  pull)
    printf '%s\\n' "$repository" >> "$GIT_LOG"
    [[ ${FAIL_PULL:-} != "$repository" ]]
    ;;
  *) exit 2 ;;
esac
"""
        )
        git.chmod(0o755)
        prline = fake_bin / "prline"
        prline.write_text("#!/usr/bin/env bash\nexit 0\n")
        prline.chmod(0o755)

        self.environment = os.environ.copy()
        self.environment.update(
            HOME=str(self.home),
            PROJECTS_DIR=str(self.projects),
            GIT_LOG=str(self.log),
            PATH=f"{fake_bin}{os.pathsep}{self.environment['PATH']}",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def run_pullall(self):
        return subprocess.run(
            ["bash", str(SCRIPT)],
            text=True,
            capture_output=True,
            env=self.environment,
            timeout=5,
        )

    def test_pulls_home_dotfiles_and_each_project_with_space_safe_paths(self):
        result = self.run_pullall()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.log.read_text().splitlines(),
            [str(self.dotfiles), str(self.project)],
        )

    def test_project_enumeration_failure_is_reported(self):
        self.environment["PROJECTS_DIR"] = str(self.home / "missing projects")

        result = self.run_pullall()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing projects", result.stderr)

    def test_individual_pull_failure_stops_the_command(self):
        self.environment["FAIL_PULL"] = str(self.project)

        result = self.run_pullall()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            self.log.read_text().splitlines(),
            [str(self.dotfiles), str(self.project)],
        )


if __name__ == "__main__":
    unittest.main()
