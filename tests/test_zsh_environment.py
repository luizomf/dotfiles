# Copyright (c) 2026 Otávio Miranda
"""Isolated Zsh startup checks; no private env or toolchain startup files."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ZSH = shutil.which("zsh")


@unittest.skipUnless(ZSH, "zsh is required")
class ZshEnvironmentTests(unittest.TestCase):
  def test_startup_modes_preserve_shared_paths_and_defaults(self):
    with tempfile.TemporaryDirectory() as temporary:
      home = Path(temporary)
      (home / "dotfiles").symlink_to(REPO, target_is_directory=True)
      (home / ".zshenv").write_text('source "$HOME/dotfiles/zsh/.zshenv"\n')
      (home / ".zshrc").write_text(
        "typeset -A ZSH_HIGHLIGHT_STYLES\n"
        "OSTYPE=test\n"
        "uname() { print Test; }\n"
        "pyenv() { return 0; }\n"
        'source "$HOME/dotfiles/zsh/config/exports"\n'
      )
      node = home / "inherited-node/node"
      node.parent.mkdir()
      node.write_text("#!/bin/sh\nexit 0\n")
      node.chmod(0o700)
      for mode in ("-dc", "-dic", "-dlc", "-dlic", "-c", "-ic", "-lc", "-lic"):
        # Disabled globals: simulate Alpine's reset. Otherwise exercise the
        # real system startup files, still with an isolated user home.
        reset = "PATH=/usr/bin:/bin\n" if "d" in mode else ""
        (home / ".zprofile").write_text(
          reset + 'source "$HOME/dotfiles/zsh/.zprofile"\n'
        )
        with self.subTest(mode=mode):
          # Only repository-owned startup files and synthetic inputs execute.
          result = subprocess.run(  # noqa: S603
            [
              str(ZSH),
              mode,
              "print -l -- $path; print -- ENV:$LOCAL_MODEL:$MODEL:$OLLAMA_TIMEOUT_MS",
            ],
            env={
              "HOME": str(home),
              "PATH": "/usr/bin:/bin",
              "TERM": "dumb",
              "NVM_BIN": str(node.parent),
              "LOCAL_MODEL": "test-model",
              "MODEL": "old-model",
              "OLLAMA_TIMEOUT_MS": "321",
            },
            text=True,
            capture_output=True,
            check=True,
          )
          paths = result.stdout.splitlines()
          self.assertEqual(paths[-1], "ENV:test-model:test-model:321")
          for directory in (
            "dotfiles/scripts",
            ".local/bin",
            ".docker/bin",
            ".cargo/bin",
          ):
            self.assertEqual(paths.count(str(home / directory)), 1)
          self.assertEqual(
            paths[0:3],
            [
              str(home / "dotfiles/scripts"),
              str(node.parent),
              str(home / ".local/bin"),
            ],
          )
          self.assertLess(
            paths.index(str(home / ".docker/bin")), paths.index("/usr/bin")
          )

  def test_initial_fallback_demotion_preserves_inherited_custom_paths(self):
    for phase in ("--initial", "--refresh"):
      for platform in ("darwin-test", "linux-test"):
        with self.subTest(phase=phase, platform=platform):
          result = subprocess.run(  # noqa: S603
            [
              str(ZSH),
              "-dfc",
              (
                f'OSTYPE={platform}; source "{REPO}/zsh/config/path" {phase}; '
                "print -l -- $path"
              ),
            ],
            env={
              "HOME": "/nonexistent",
              "PATH": (
                "/opt/homebrew/bin:/example/venv/bin:/usr/local/bin:/usr/bin:/bin"
              ),
            },
            capture_output=True,
            text=True,
            check=True,
          )
          paths = result.stdout.splitlines()
          if phase == "--initial":
            self.assertLess(paths.index("/usr/bin"), paths.index("/usr/local/bin"))
            if platform == "darwin-test":
              self.assertLess(
                paths.index("/example/venv/bin"), paths.index("/opt/homebrew/bin")
              )
          else:
            self.assertLess(paths.index("/usr/local/bin"), paths.index("/usr/bin"))
            self.assertLess(
              paths.index("/opt/homebrew/bin"), paths.index("/example/venv/bin")
            )

  def test_lfs_exports_keep_native_tools_ahead_of_brew_dependencies(self):
    with tempfile.TemporaryDirectory() as temporary:
      home = Path(temporary)
      (home / "dotfiles").symlink_to(REPO, target_is_directory=True)
      result = subprocess.run(  # noqa: S603
        [
          str(ZSH),
          "-dfc",
          """
          typeset -A ZSH_HIGHLIGHT_STYLES
          OSTYPE=linux-test
          uname() { print Test; }
          pyenv() { return 0; }
          test() {
            if [[ "$*" == '-r /etc/lfs-release' ]]; then return 0; fi
            builtin test "$@"
          }
          source "$HOME/dotfiles/zsh/config/exports"
          print -l -- $path
          """,
        ],
        env={
          "HOME": str(home),
          "PATH": "/fixture/brew/bin:/usr/bin:/bin",
        },
        capture_output=True,
        text=True,
        check=True,
      )
      paths = result.stdout.splitlines()
      self.assertLess(paths.index("/usr/bin"), paths.index("/fixture/brew/bin"))
      self.assertEqual(paths[0], str(home / "dotfiles/scripts"))

  def test_path_can_be_reapplied_without_duplicates(self):
    # The sourced path is the repository-owned config, not external input.
    result = subprocess.run(  # noqa: S603
      [
        str(ZSH),
        "-dfc",
        (
          f'source "{REPO}/zsh/config/path" && first=$PATH && '
          f'source "{REPO}/zsh/config/path" && [[ $first == $PATH ]]'
        ),
      ],
      env={"HOME": "/nonexistent", "PATH": "/usr/bin:/bin"},
      capture_output=True,
      text=True,
      check=False,
    )
    self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
  unittest.main()
