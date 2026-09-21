# Copyright (c) 2026 Luiz Otávio Miranda

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ClearProjectsTests(unittest.TestCase):
  def setUp(self) -> None:
    self.temp = tempfile.TemporaryDirectory()
    self.addCleanup(self.temp.cleanup)
    self.root = Path(self.temp.name)
    self.home = self.root / "home"
    self.projects = self.root / "projects"
    self.home.mkdir()
    self.projects.mkdir()
    # Even a broken root guard must not send real host paths to rm in tests.
    bin_dir = self.root / "bin"
    bin_dir.mkdir()
    guarded_rm = bin_dir / "rm"
    guarded_rm.write_text(
      "#!/bin/bash\n"
      'for arg in "$@"; do\n'
      '  case "$arg" in\n'
      "    -rf|--) ;;\n"
      "    */../*|*/..) printf 'OUTSIDE FIXTURE\\n' >&2; exit 77 ;;\n"
      f"    {shlex.quote(str(self.root.resolve()))}/*) ;;\n"
      "    *) printf 'OUTSIDE FIXTURE: %s\\n' \"$arg\" >&2; exit 77 ;;\n"
      "  esac\n"
      "done\n"
      'exec /bin/rm "$@"\n',
    )
    guarded_rm.chmod(0o755)
    self.env = {
      "PATH": str(bin_dir) + os.pathsep + os.defpath,
      "HOME": str(self.home),
      "PROJECTS_DIR": str(self.projects),
      "GIT_CONFIG_NOSYSTEM": "1",
      "GIT_CONFIG_GLOBAL": os.devnull,
    }

  def command(self, *args: str) -> subprocess.CompletedProcess[str]:
    # All paths and the environment belong to the isolated fixture.
    return subprocess.run(  # noqa: S603
      args,
      cwd=self.root,
      env=self.env,
      capture_output=True,
      text=True,
      check=False,
      timeout=30,
    )

  def cleanup_projects(self, *args: str) -> subprocess.CompletedProcess[str]:
    result = self.command(
      "/bin/bash",
      str(PROJECT_ROOT / "scripts/clear_projects"),
      *args,
    )
    self.assertNotIn("OUTSIDE FIXTURE", result.stderr)
    return result

  def file(self, relative: str) -> Path:
    path = self.root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("must survive unless explicitly targeted\n")
    return path

  def test_only_cleanup_contents_are_removed_including_hidden_entries(self) -> None:
    sentinels = [
      self.file("outside/keep"),
      self.file("outside/.scratch/keep"),
      self.file("outside/release/keep"),
      self.file("projects/one/src/keep"),
      self.file("projects/loose-file"),
      self.file("projects/.hidden-project/.scratch/keep"),
      self.file("home/dotfiles/config/keep"),
    ]
    targets: list[Path] = []
    for project in ("projects/one", "home/dotfiles"):
      for name in (".scratch", "release"):
        for entry in ("plain", ".hidden", "with spaces", "-option", "nested/deep/file"):
          self.file(f"{project}/{name}/{entry}")
        target = self.root / project / name
        (target / "empty").mkdir()
        (target / "outside-link").symlink_to(self.root / "outside")
        targets.append(target)
    (self.projects / "linked-project").symlink_to(self.root / "outside")
    (self.projects / "two").mkdir()
    (self.projects / "two/.scratch").symlink_to(self.root / "outside")
    before = {path: path.read_bytes() for path in sentinels}

    for _ in range(2):
      result = self.cleanup_projects()
      self.assertEqual(0, result.returncode, result.stderr)
      for target in targets:
        self.assertTrue(target.is_dir())
        self.assertEqual([], list(target.iterdir()))
      for path, content in before.items():
        self.assertEqual(content, path.read_bytes())
      self.assertTrue((self.projects / "two/.scratch").is_symlink())
      self.assertTrue((self.projects / "linked-project").is_symlink())

  def test_dry_run_preserves_all_contents(self) -> None:
    contents = [
      self.file("projects/one/.scratch/nested/.hidden"),
      self.file("projects/one/release/artifact"),
      self.file("home/dotfiles/.scratch/notes"),
    ]
    result = self.cleanup_projects("--dry-run")
    self.assertEqual(0, result.returncode, result.stderr)
    self.assertIn("Would remove:", result.stdout)
    for path in contents:
      self.assertTrue(path.is_file())

  def test_invalid_roots_fail_before_deleting_dotfiles_contents(self) -> None:
    sentinel = self.file("home/dotfiles/.scratch/keep")
    link = self.root / "linked-root"
    link.symlink_to(self.projects)
    for root in (
      None,
      "",
      "/",
      "/../",
      str(self.home),
      str(link) + "/",
      str(sentinel),
      str(self.root / "missing"),
    ):
      with self.subTest(root=root):
        if root is None:
          self.env.pop("PROJECTS_DIR", None)
        else:
          self.env["PROJECTS_DIR"] = root
        result = self.cleanup_projects()
        self.assertNotEqual(0, result.returncode)
        self.assertTrue(sentinel.is_file())

  def test_empty_projects_and_missing_cleanup_directories_are_noops(self) -> None:
    result = self.cleanup_projects()
    self.assertEqual(0, result.returncode, result.stderr)
    self.file("projects/one/keep")
    result = self.cleanup_projects()
    self.assertEqual(0, result.returncode, result.stderr)

  def test_hook_blocks_a_commit_when_cleanup_regression_fails(self) -> None:
    result = self.command("/usr/bin/git", "init", "-q")
    self.assertEqual(0, result.returncode, result.stderr)
    hook = self.root / ".githooks/pre-commit"
    hook.parent.mkdir()
    shutil.copy2(PROJECT_ROOT / ".githooks/pre-commit", hook)
    checker = self.file("scripts/check_staged")
    checker.write_text("#!/bin/sh\nexit 0\n")
    checker.chmod(0o755)
    self.file("scripts/clear_projects")
    self.file("tests/__init__.py").write_text("")
    self.file("tests/test_clear_projects.py").write_text(
      "import unittest\n"
      "class Regression(unittest.TestCase):\n"
      "  def test_safety(self):\n"
      "    self.fail('cleanup safety regression')\n",
    )
    result = self.command("/usr/bin/git", "add", ".")
    self.assertEqual(0, result.returncode, result.stderr)
    result = self.command("/bin/bash", str(hook))
    self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
    self.assertIn("cleanup safety regression", result.stderr)


if __name__ == "__main__":
  unittest.main()
