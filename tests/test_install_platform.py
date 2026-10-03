# Copyright (c) 2026 Otávio Miranda
"""Test installer policy without executing install.sh or package managers."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/lib/install-platform.sh"


class InstallPlatformTests(unittest.TestCase):
  def shell(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
    # Only repository-owned shell snippets and fixture arguments are executed.
    return subprocess.run(  # noqa: S603
      [
        "/bin/bash",
        "-c",
        'REPO_DIR=$(dirname "$(dirname "$(dirname "$1")")"); '
        'source "$1" || exit; ' + script,
        "test",
        str(MODULE),
        *args,
      ],
      text=True,
      capture_output=True,
      timeout=5,
      check=False,
    )

  def run_error_policy(self, body: str) -> subprocess.CompletedProcess[str]:
    # Exercise the actual prologue without running the destructive installer.
    lines = (ROOT / "install.sh").read_text().splitlines()
    options = next(line for line in lines if line.startswith("set -"))
    trap = next(line for line in lines if line.startswith("trap "))
    script = (
      options + '\nlogerror() { printf "INSTALLER_ERR\\n" >&2; }\n' + trap + "\n" + body
    )
    # macOS /bin/bash 3.2 differs from newer Bash for ERR in a guarded $(...).
    # The script combines the repository prologue with a fixed test fixture.
    return subprocess.run(  # noqa: S603
      ["/bin/bash", "-c", script],
      text=True,
      capture_output=True,
      timeout=5,
      check=False,
    )

  def test_unattended_mode_disables_prompts_and_requires_noninteractive_sudo(self):
    with tempfile.TemporaryDirectory() as tmp:
      sudo = Path(tmp) / "sudo"
      sudo.write_text('#!/bin/sh\nprintf "sudo"; printf " <%s>" "$@"; printf "\\n"\n')
      sudo.chmod(0o755)
      result = self.shell(
        """
        set -Eeuo pipefail
        export PATH="$2:$PATH"
        OM_INSTALL_ASSUME_YES=1
        INTERACTIVE=1
        exec <<< 'must-not-be-read'
        configure_install_interaction
        /bin/bash -c '
          printf "brew=%s git=%s interactive=%s\\n" \\
            "$NONINTERACTIVE" "$GIT_TERMINAL_PROMPT" "${INTERACTIVE-unset}"
        '
        if read -r answer; then exit 99; fi
        sudo dnf install -y patch
        printf 'LOGS_REMAIN_VISIBLE\\n'
        """,
        tmp,
      )
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertIn("brew=1 git=0 interactive=unset", result.stdout)
      self.assertIn("sudo <-n> <dnf> <install> <-y> <patch>", result.stdout)
      self.assertIn("LOGS_REMAIN_VISIBLE", result.stdout)

  def test_normal_mode_preserves_input_and_sudo_behavior(self):
    result = self.shell("""
      set -Eeuo pipefail
      OM_INSTALL_ASSUME_YES=0
      unset NONINTERACTIVE GIT_TERMINAL_PROMPT
      INTERACTIVE=1
      sudo() { printf 'existing sudo\\n'; }
      exec <<< 'answer'
      configure_install_interaction
      read -r answer
      printf '%s %s %s %s\\n' "$answer" "$INTERACTIVE" \\
        "${NONINTERACTIVE-unset}" "${GIT_TERMINAL_PROMPT-unset}"
      sudo true
    """)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn("answer 1 unset unset", result.stdout)
    self.assertIn("existing sudo", result.stdout)

  def test_expected_subshell_probe_does_not_report_installation_failure(self):
    result = self.run_error_policy("""
            probe() {
                local value
                if ! value="$(false)"; then printf 'expected-miss\\n'; fi
            }
            probe
            printf 'READY\\n'
        """)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn("READY", result.stdout)
    self.assertEqual(result.stderr, "")

  def test_real_failures_still_abort_and_report(self):
    for command in (
      "false",
      "fail() { false; }; fail",
      'value="$(false)"',
      "( false )",
    ):
      with self.subTest(command=command):
        result = self.run_error_policy(command + '\nprintf "UNREACHABLE\\n"')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("UNREACHABLE", result.stdout)
        self.assertIn("INSTALLER_ERR", result.stderr)

  def test_nvm_bootstrap_uses_the_shell_path_with_xdg_config_home(self):
    # Exercise the actual Node block, without packages, links or network calls.
    # The fixture implements nvm v0.40.3's destination selection and its
    # requirement that an explicitly configured non-default directory exists.
    source = (ROOT / "install.sh").read_text()
    node_setup = (
      source.split('loginfo "Instalando Lazy.nvim..."', 1)[1]
      .split("\nfi\n", 1)[1]
      .split("\nif configure_install_python;", 1)[0]
    )
    for scenario in ("xdg", "inherited"):
      with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        other_nvm = home / ".config/nvm"
        other_nvm.mkdir(parents=True)
        sentinel = other_nvm / "user-data"
        sentinel.write_text("preserve me")
        (home / "fixture-install.sh").write_text(
          "#!/bin/bash\n"
          'default="$HOME/.nvm"\n'
          '[[ -z "${XDG_CONFIG_HOME:-}" ]] || default="$XDG_CONFIG_HOME/nvm"\n'
          "target=${NVM_DIR:-$default}\n"
          'if [[ -n "${NVM_DIR:-}" && "$target" != "$default" '
          '&& ! -d "$target" ]]; then exit 44; fi\n'
          'mkdir -p "$target"\n'
          'printf \'nvm() { printf "nvm %%s\\\\n" "$*"; }\\n\' '
          '> "$target/nvm.sh"\n'
        )
        result = self.shell(
          """
          set -Eeuo pipefail
          export HOME=$2 XDG_CONFIG_HOME=$2/.config
          unset NVM_DIR
          unset -f nvm || :
          if [[ "$3" == inherited ]]; then
            export NVM_DIR="$HOME/.config/nvm"
            nvm() { printf 'WRONG_NVM\\n'; }
          fi
          OM_INSTALL_SKIP_TOOLCHAINS=0
          loginfo() { :; }
          run_remote_script() { "$1" "$HOME/fixture-install.sh"; }
          npm() { printf 'npm %s\\n' "$*"; }
          """
          + node_setup,
          tmp,
          scenario,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((home / ".nvm/nvm.sh").is_file())
        self.assertEqual(sentinel.read_text(), "preserve me")
        self.assertIn("nvm install --lts", result.stdout)
        self.assertIn("npm install --global prettier", result.stdout)
        self.assertNotIn("WRONG_NVM", result.stdout)

  def test_python_build_failure_preserves_error_and_skips_dependents(self):
    result = self.shell(
      """
            set -Eeuo pipefail
            source "$2"
            loginfo() { :; }
            logerror() { printf '%s\\n' "$1" >&2; }
            pyenv() {
                case "$1" in
                    init) return 0 ;;
                    install) printf 'compiler failed\\n' >&2; return 42 ;;
                    *) printf 'UNREACHABLE pyenv %s\\n' "$*" ;;
                esac
            }
            uv() { printf 'UNREACHABLE uv %s\\n' "$*"; }
            OM_PYTHON_VERSION=3.14.7
            if configure_install_python; then
                printf 'UNEXPECTED_SUCCESS\\n'
            else
                printf 'FAILED: %s (exit %s)\\n' "$PYTHON_SETUP_STEP" "$?"
            fi
            printf 'CONTINUED\\n'
        """,
      str(ROOT / "scripts/lib/install-python.sh"),
    )
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn("compiler failed", result.stderr)
    self.assertIn("3.14.7 (exit 42)", result.stdout)
    self.assertIn("CONTINUED", result.stdout)
    self.assertNotIn("UNREACHABLE", result.stdout)
    self.assertNotIn("UNEXPECTED_SUCCESS", result.stdout)

  def test_python_setup_propagates_discovery_and_sync_failures(self):
    for failure, expected in (
      ("list", "Find a stable Python"),
      ("sync", "Sync the dotfiles"),
      ("none", "SUCCESS"),
    ):
      with self.subTest(failure=failure):
        result = self.shell(
          """
                    set -Eeuo pipefail
                    source "$2"
                    failure=$3
                    REPO_DIR=/unused-checkout
                    loginfo() { :; }
                    logerror() { printf '%s\\n' "$1" >&2; }
                    pyenv() {
                        case "$*" in
                            'install --list')
                                if [[ "$failure" == list ]]; then
                                    printf 'discovery failed\\n' >&2
                                    return 17
                                fi
                                printf '  3.14.7\\n' ;;
                            'which python') printf '/fake/python\\n' ;;
                        esac
                    }
                    uv() {
                        if [[ "$1" == sync && "$failure" == sync ]]; then
                            printf 'sync failed\\n' >&2
                            return 17
                        fi
                    }
                    if configure_install_python; then
                        printf 'SUCCESS\\n'
                    else
                        printf '%s (exit %s)\\n' "$PYTHON_SETUP_STEP" "$?"
                    fi
                """,
          str(ROOT / "scripts/lib/install-python.sh"),
          failure,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(expected, result.stdout)
        if failure != "none":
          self.assertIn("exit 17", result.stdout)
          self.assertIn("failed", result.stderr)
          self.assertNotIn("SUCCESS", result.stdout)

  def test_python_failure_is_reported_after_independent_work(self):
    # Exercise the production recovery and final-report blocks, not packages
    # or deployed links. The existing prologue test uses the same safe seam.
    source = (ROOT / "install.sh").read_text()
    recovery = source.split("if configure_install_python; then", 1)[1].split(
      'loginfo "Criando links', 1
    )[0]
    finish = source.split('if [[ -n "$python_failure" ]]; then', 1)[1].split(
      "printf '\\n%s\\n'", 1
    )[0]
    result = self.run_error_policy(
      """
            configure_install_python() {
                PYTHON_SETUP_STEP='Install Python 3.14.7'
                printf 'original build error\\n' >&2
                return 42
            }
            loginfo() { printf '%s\\n' "$1"; }
            logerror() { printf '%s\\n' "$1" >&2; }
            """
      "if configure_install_python; then"
      + recovery
      + "printf 'INDEPENDENT_WORK_DONE\\n'\n"
      + 'if [[ -n "$python_failure" ]]; then'
      + finish
    )
    self.assertEqual(result.returncode, 1, result.stderr)
    self.assertIn("INDEPENDENT_WORK_DONE", result.stdout)
    self.assertIn("original build error", result.stderr)
    self.assertIn("Installation incomplete", result.stderr)
    self.assertIn("Install Python 3.14.7 (exit 42)", result.stderr)

  def test_supported_platforms(self):
    for kernel, distro, expected in (
      ("Darwin", "", "darwin"),
      ("Linux", "ubuntu", "ubuntu"),
      ("Linux", "fedora", "fedora"),
      ("Linux", "fedora-asahi-remix", "fedora"),
      ("Linux", "omarchy", "arch"),
      ("Linux", "arch", "arch"),
    ):
      with self.subTest(distro=distro or kernel):
        result = self.shell('detect_install_platform "$2" "$3" 0', kernel, distro)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), expected)

  def test_unsupported_and_immutable_platforms(self):
    for kernel, distro, ostree in (
      ("Linux", "debian", "0"),
      ("FreeBSD", "", "0"),
      ("Linux", "fedora", "1"),
      ("Linux", "fedora-asahi-remix", "1"),
      ("Linux", "omarchy", "1"),
      ("Linux", "arch", "1"),
    ):
      with self.subTest(distro=distro, ostree=ostree):
        result = self.shell(
          'detect_install_platform "$2" "$3" "$4"', kernel, distro, ostree
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

  def test_fedora_commands_use_dnf_and_no_ubuntu_or_system_services(self):
    result = self.shell("""
            loginfo() { :; }
            sudo() { printf 'sudo'; printf ' <%s>' "$@"; printf '\\n'; }
            install_homebrew() { printf 'load-homebrew\\n'; }
            brew() { printf 'brew'; printf ' <%s>' "$@"; printf '\\n'; }
            install_platform_packages fedora
        """)
    self.assertEqual(result.returncode, 0, result.stderr)
    lines = result.stdout.splitlines()
    self.assertEqual(len(lines), 3)
    self.assertTrue(lines[0].startswith("sudo <dnf> <install> <-y>"))
    for package in (
      "gcc-c++",
      "openssl-devel",
      "libffi-devel",
      "zlib-devel",
      "tmux",
      "zsh",
    ):
      self.assertIn(f"<{package}>", lines[0])
    self.assertEqual(lines[1], "load-homebrew")
    self.assertTrue(lines[2].startswith("brew <install>"))
    self.assertIn("<tmux>", lines[2])
    for forbidden in (
      "apt-get",
      "ghostty-ubuntu",
      "systemctl",
      "kernel",
      "bootloader",
    ):
      self.assertNotIn(forbidden, result.stdout)

  def test_arch_installs_native_build_dependencies_and_shared_brew_tools(self):
    result = self.shell("""
      set -Eeuo pipefail
      loginfo() { :; }
      sudo() { printf 'sudo'; printf ' <%s>' "$@"; printf '\\n'; }
      install_homebrew() { printf 'load-homebrew\\n'; }
      brew() { printf 'brew'; printf ' <%s>' "$@"; printf '\\n'; }
      install_platform_packages arch
    """)
    self.assertEqual(result.returncode, 0, result.stderr)
    lines = result.stdout.splitlines()
    self.assertEqual(len(lines), 3)
    self.assertTrue(lines[0].startswith("sudo <pacman> <-S> <--needed>"))
    self.assertNotIn("--noconfirm", lines[0])
    for package in ("base-devel", "libffi", "openssl", "zlib", "zsh", "tmux"):
      self.assertIn(f"<{package}>", lines[0])
    self.assertEqual(lines[1], "load-homebrew")
    for package in ("neovim", "rtk", "pi-coding-agent", "shellcheck"):
      self.assertIn(f"<{package}>", lines[2])
    for forbidden in ("yay", "-Sy", "systemctl", "chsh", "ghostty-ubuntu", "dnf"):
      self.assertNotIn(forbidden, result.stdout)

  def test_unattended_arch_uses_noninteractive_pacman(self):
    result = self.shell("""
      set -Eeuo pipefail
      OM_INSTALL_ASSUME_YES=1
      loginfo() { :; }
      sudo() { printf '%s\\n' "$*"; }
      install_homebrew() { :; }
      brew() { :; }
      install_platform_packages arch
    """)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertTrue(result.stdout.startswith("pacman -S --needed --noconfirm "))

  def test_ubuntu_and_macos_keep_their_package_managers(self):
    for platform in ("ubuntu", "darwin"):
      with self.subTest(platform=platform):
        result = self.shell(
          """
          set -Eeuo pipefail
          loginfo() { :; }
          sudo() { printf 'sudo %s\\n' "$*"; }
          install_homebrew() { printf 'load-homebrew\\n'; }
          brew() { printf 'brew %s\\n' "$*"; }
          install_platform_packages "$2"
          """,
          platform,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        if platform == "ubuntu":
          self.assertIn("apt-get update", result.stdout)
          self.assertIn("apt-get install -y", result.stdout)
          self.assertIn("libssl-dev", result.stdout)
          self.assertIn("fd-find", result.stdout)
          self.assertIn("font-fira-code-nerd-font", result.stdout)
        else:
          self.assertEqual(
            result.stdout.splitlines(),
            [
              "load-homebrew",
              "brew update",
              f"brew bundle --file={ROOT}/homebrew/Brewfile",
            ],
          )

  @unittest.skipUnless(shutil.which("ruby"), "Ruby is required for the Brewfile DSL")
  def test_brewfile_reads_only_macos_entries_from_the_shared_catalog(self):
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      (root / "homebrew").mkdir()
      (root / "config").mkdir()
      brewfile = root / "homebrew/Brewfile"
      shutil.copyfile(ROOT / "homebrew/Brewfile", brewfile)
      (root / "config/packages.list").write_text(
        "# platforms provider package [option]\n"
        "darwin tap docker/tap trusted\n"
        "darwin,ubuntu,fedora,arch brew bat\n"
        "darwin brew popt unlinked\n"
        "darwin cask ghostty\n"
        "darwin uv mypy\n"
        "ubuntu,arch native git\n"
        "fedora,arch brew pi-coding-agent\n"
      )
      # Evaluate Bundle's DSL with inert package declarations, never Homebrew.
      result = subprocess.run(  # noqa: S603
        [
          shutil.which("ruby") or "ruby",
          "-e",
          (
            'require "json"; %w[tap brew cask uv].each { |name| '
            "define_singleton_method(name) { |*args| "
            "puts JSON.generate([name, *args]) } }; load ARGV.fetch(0)"
          ),
          str(brewfile),
        ],
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
      )
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertEqual(
        [json.loads(line) for line in result.stdout.splitlines()],
        [
          ["tap", "docker/tap", {"trusted": True}],
          ["brew", "bat"],
          ["brew", "popt", {"link": False}],
          ["cask", "ghostty"],
          ["uv", "mypy"],
        ],
      )

  def test_linux_catalog_keeps_the_last_package_without_a_final_newline(self):
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      (root / "config").mkdir()
      (root / "config/packages.list").write_text(
        "# Fixture catalog\n"
        "arch native git\n"
        "darwin brew mac-only\n"
        "arch brew bat\n"
        "arch brew rtk"
      )
      result = self.shell(
        """
        set -Eeuo pipefail
        REPO_DIR=$2
        loginfo() { :; }
        sudo() { printf 'sudo %s\\n' "$*"; }
        install_homebrew() { :; }
        brew() { printf 'brew %s\\n' "$*"; }
        install_platform_packages arch
        """,
        tmp,
      )
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertEqual(
        result.stdout.splitlines(),
        ["sudo pacman -S --needed git", "brew install bat rtk"],
      )

  def test_native_package_failure_stops_before_homebrew(self):
    result = self.shell("""
      set -Eeuo pipefail
      loginfo() { :; }
      sudo() { printf 'package download failed\\n' >&2; return 23; }
      install_homebrew() { printf 'UNREACHABLE\\n'; }
      install_platform_packages arch
    """)
    self.assertEqual(result.returncode, 23)
    self.assertIn("package download failed", result.stderr)
    self.assertNotIn("UNREACHABLE", result.stdout)

  def test_catalog_has_supported_unique_declarations(self):
    seen: set[tuple[str, str, str]] = set()
    providers = {
      "darwin": {"brew", "cask", "tap", "uv"},
      "ubuntu": {"native", "brew"},
      "fedora": {"native", "brew"},
      "arch": {"native", "brew"},
    }
    for number, line in enumerate(
      (ROOT / "config/packages.list").read_text().splitlines(), start=1
    ):
      if not line.strip() or line.lstrip().startswith("#"):
        continue
      with self.subTest(line=number):
        fields = line.split()
        self.assertIn(len(fields), (3, 4))
        platforms, provider, package, *options = fields
        for platform in platforms.split(","):
          self.assertIn(platform, providers)
          self.assertIn(provider, providers[platform])
          self.assertNotIn((platform, provider, package), seen)
          seen.add((platform, provider, package))
        if options:
          self.assertEqual(platforms, "darwin")
          self.assertIn(
            (provider, options[0]), (("brew", "unlinked"), ("tap", "trusted"))
          )

  def test_existing_toolchain_is_never_removed(self):
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      existing = root / "toolchain"
      existing.mkdir()
      sentinel = existing / "user-data"
      sentinel.write_text("preserve me")
      result = self.shell('require_new_toolchain_dir "$2"', str(existing))
      self.assertNotEqual(result.returncode, 0)
      self.assertEqual(sentinel.read_text(), "preserve me")
      link = root / "broken-link"
      link.symlink_to(root / "missing-target")
      self.assertNotEqual(
        self.shell('require_new_toolchain_dir "$2"', str(link)).returncode, 0
      )
      self.assertTrue(link.is_symlink())
      result = self.shell('require_new_toolchain_dir "$2"', str(root / "new"))
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertFalse((root / "new").exists())


if __name__ == "__main__":
  unittest.main()
