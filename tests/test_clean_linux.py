# Copyright (c) 2026 Otávio Miranda
"""Cleanup safety checks with disposable caches and intercepted system commands."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class CleanLinuxTests(unittest.TestCase):
  def test_cleanup_modes_and_boundaries(self):
    for arguments, external_cache, mounted_cache in (
      ((), "", ""),
      (("--apply",), "", ""),
      (("--system", "--trim"), "", ""),
      (("--apply", "--system", "--trim"), "", ""),
      (("--apply",), "xdg", ""),
      (("--apply",), "brew", ""),
      (("--apply",), "symlink", ""),
      (("--apply",), "ancestor", ""),
      (("--apply",), "", ".cache/Homebrew"),
      (("--apply",), "", ".cache/Homebrew/nested"),
      (("--apply",), "", ".cache/uv/nested"),
    ):
      with (
        self.subTest(
          arguments=arguments, external=external_cache, mounted=mounted_cache
        ),
        tempfile.TemporaryDirectory() as temporary,
      ):
        root = Path(temporary)
        home = root / "home"
        home.mkdir()
        binaries = root / "bin"
        binaries.mkdir()
        calls = root / "calls"
        fixtures = {
          "uname": "printf 'Linux\\n'\n",
          "id": "printf '1000\\n'\n",
          "brew": (
            'printf "brew %s\\n" "$*" >> "$CALLS"\n'
            '/bin/rm -f -- "$HOMEBREW_CACHE/data"\n'
          ),
          "sudo": 'printf "sudo %s\\n" "$*" >> "$CALLS"\n',
          "journalctl": "exit 99\n",
          "systemd-tmpfiles": "exit 99\n",
          "fstrim": "exit 99\n",
          "findmnt": 'printf "/\\n"; [ -z "$MOUNTED" ] || printf "%s\\n" "$MOUNTED"\n',
          # macOS rm lacks --one-file-system. Only the deletion primitive is
          # adapted; production path selection still executes unchanged.
          "rm": (
            '[ "$1" = -rf ] && [ "$2" = --one-file-system ] || exit 99\n'
            '[ "$3" = -- ] || exit 99\n'
            'exec /bin/rm -rf -- "$4"\n'
          ),
        }
        for name, body in fixtures.items():
          executable = binaries / name
          executable.write_text("#!/bin/sh\n" + body)
          executable.chmod(0o700)
        disposable = (
          ".npm/_cacache",
          ".npm/_logs",
          ".cache/Homebrew",
          ".cache/uv",
          ".cache/nvim",
        )
        for relative in disposable:
          directory = home / relative
          directory.mkdir(parents=True)
          (directory / "data").write_text("cache")
        protected = (
          ".cache/keepwarm/current",
          ".cache/unknown/data",
          ".npm/npmrc",
          ".ssh/key",
          ".zsh_history",
          ".local/share/nvim/plugin",
          ".dotfiles-backups/config",
        )
        for relative in protected:
          target = home / relative
          target.parent.mkdir(parents=True, exist_ok=True)
          target.write_text("keep")
        outside = root / "outside"
        outside.mkdir()
        (outside / "data").write_text("keep")
        (home / ".cache/pip").symlink_to(outside, target_is_directory=True)
        (home / ".cache/uv/link").symlink_to(outside, target_is_directory=True)
        if external_cache == "symlink":
          (home / ".cache/Homebrew").rename(root / "moved-brew")
          (home / ".cache/Homebrew").symlink_to(outside, target_is_directory=True)
        if external_cache == "ancestor":
          (home / ".cache").rename(root / "moved-cache")
          (home / ".cache").symlink_to(root / "moved-cache", target_is_directory=True)
        result = subprocess.run(  # noqa: S603
          ["/bin/bash", str(REPO / "scripts/clean_linux"), *arguments],
          env={
            "HOME": str(home),
            "PATH": f"{binaries}:/usr/bin:/bin",
            "CALLS": str(calls),
            "XDG_CACHE_HOME": str(
              outside if external_cache == "xdg" else home / ".cache"
            ),
            "HOMEBREW_CACHE": str(outside) if external_cache == "brew" else "",
            "MOUNTED": str((home / mounted_cache).resolve()) if mounted_cache else "",
          },
          capture_output=True,
          text=True,
          check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        applying = "--apply" in arguments
        for relative in disposable:
          skipped = (
            (external_cache in {"xdg", "ancestor"} and relative.startswith(".cache/"))
            or (mounted_cache == relative or mounted_cache.startswith(relative + "/"))
            or (external_cache == "symlink" and relative == ".cache/Homebrew")
          )
          self.assertEqual((home / relative).exists(), not applying or skipped)
        for relative in protected:
          self.assertEqual((home / relative).read_text(), "keep")
        self.assertEqual((outside / "data").read_text(), "keep")
        self.assertTrue((home / ".cache/pip").is_symlink())
        recorded = calls.read_text() if calls.exists() else ""
        self.assertEqual(
          "brew cleanup --prune=all" in recorded,
          applying
          and not external_cache
          and not mounted_cache.startswith(".cache/Homebrew"),
        )
        self.assertTrue(applying or not recorded)
        if applying and "--system" in arguments:
          self.assertIn("sudo -n systemd-tmpfiles --clean", recorded)
          self.assertIn(
            "sudo -n journalctl --rotate --vacuum-time=7d --vacuum-size=8M", recorded
          )
          self.assertIn(" -av", recorded)
        else:
          self.assertNotIn("sudo ", recorded)

  def test_platform_root_and_sudo_fail_before_cleanup(self):
    for platform, uid, sudo_status, mount_status in (
      ("Darwin", 1000, 0, 0),
      ("Linux", 0, 0, 0),
      ("Linux", 1000, 1, 0),
      ("Linux", 1000, 0, 1),
    ):
      with (
        self.subTest(
          platform=platform, uid=uid, sudo_status=sudo_status, mount_status=mount_status
        ),
        tempfile.TemporaryDirectory() as temporary,
      ):
        home = Path(temporary)
        cache = home / ".npm/_cacache"
        cache.mkdir(parents=True)
        marker = cache / "keep"
        marker.write_text("keep")
        binaries = home / "bin"
        binaries.mkdir()
        for name, body in {
          "uname": f"printf '{platform}\\n'",
          "id": f"printf '{uid}\\n'",
          "sudo": f"exit {sudo_status}",
          "findmnt": f"printf '/\\n'; exit {mount_status}",
          "journalctl": "exit 99",
          "systemd-tmpfiles": "exit 99",
        }.items():
          target = binaries / name
          target.write_text("#!/bin/sh\n" + body + "\n")
          target.chmod(0o700)
        result = subprocess.run(  # noqa: S603
          ["/bin/bash", str(REPO / "scripts/clean_linux"), "--apply", "--system"],
          env={"HOME": str(home), "PATH": f"{binaries}:/usr/bin:/bin"},
          capture_output=True,
          text=True,
          check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(), "keep")

  def test_invalid_options_do_not_mutate(self):
    result = subprocess.run(  # noqa: S603
      ["/bin/bash", str(REPO / "scripts/clean_linux"), "--unknown"],
      env={"PATH": os.defpath},
      capture_output=True,
      text=True,
      check=False,
    )
    self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
  unittest.main()
