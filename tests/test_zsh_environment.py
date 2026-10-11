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

  def test_missing_locale_gets_utf8_in_every_startup_mode(self):
    available = subprocess.run(
      ["locale", "-a"],  # noqa: S607 - resolved through the isolated system PATH
      env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
      text=True,
      capture_output=True,
      check=True,
    ).stdout.splitlines()
    if not set(available).intersection(
      {"C.UTF-8", "C.utf8", "en_US.UTF-8", "en_US.utf8"}
    ):
      self.skipTest("No supported UTF-8 fallback is installed")
    for mode in ("-dc", "-dic", "-dlc", "-dlic"):
      with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary)
        (home / "dotfiles").symlink_to(REPO, target_is_directory=True)
        (home / ".zshenv").write_text('source "$HOME/dotfiles/zsh/.zshenv"\n')
        result = subprocess.run(  # noqa: S603
          [str(ZSH), mode, 'locale charmap; s="é"; print -- ${#s}:${LC_ALL-unset}'],
          env={"HOME": str(home), "PATH": "/usr/bin:/bin", "TERM": "dumb"},
          text=True,
          capture_output=True,
          check=True,
        )
        self.assertEqual(result.stdout.splitlines(), ["UTF-8", "1:unset"])

  def test_locale_fallback_preserves_choices_and_requires_installed_locale(self):
    cases: tuple[tuple[dict[str, str], str, str], ...] = (
      ({}, "C\\nen_US.utf8\\nC.utf8", "C.utf8||"),
      ({}, "C\\nen_US.UTF-8", "en_US.UTF-8||"),
      ({}, "C\\nPOSIX", "||"),
      ({"LANG": "C"}, "C\\nC.utf8", "C||"),
      ({"LANG": "pt_BR.UTF-8"}, "C\\nC.utf8", "pt_BR.UTF-8||"),
      ({"LC_ALL": "C"}, "C\\nC.utf8", "|C|"),
      ({"LC_CTYPE": "UTF-8"}, "C\\nC.utf8", "||UTF-8"),
      ({"LANG": "", "LC_ALL": ""}, "C\\nC.utf8", "C.utf8||"),
    )
    for overrides, available, expected in cases:
      with self.subTest(overrides=overrides, available=available):
        result = subprocess.run(  # noqa: S603
          [
            str(ZSH),
            "-dfc",
            (
              'locale() { [[ "$1" == -a ]] && printf "%b\\n" "$AVAILABLE"; }; '
              f'source "{REPO}/zsh/config/env"; '
              'print -r -- "$LANG|$LC_ALL|$LC_CTYPE"'
            ),
          ],
          env={
            "HOME": str(REPO.parent),
            "PATH": "/usr/bin:/bin",
            "AVAILABLE": available,
            **overrides,
          },
          capture_output=True,
          text=True,
          check=True,
        )
        self.assertEqual(result.stdout.strip(), expected)

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
