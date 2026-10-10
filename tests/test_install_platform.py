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

  def test_alpine_node_setup_uses_native_node_and_user_npm_prefix(self):
    source = (ROOT / "install.sh").read_text()
    node_setup = (
      source.split('loginfo "Instalando Lazy.nvim..."', 1)[1]
      .split("\nfi\n", 1)[1]
      .split("\nif configure_install_python;", 1)[0]
    )
    for skip in ("0", "1"):
      with self.subTest(skip=skip), tempfile.TemporaryDirectory() as tmp:
        result = self.shell(
          """
          set -Eeuo pipefail
          HOME=$2 OP_SYSTEM=alpine OM_INSTALL_SKIP_TOOLCHAINS=$3
          loginfo() { :; }
          run_remote_script() { printf 'UNEXPECTED_DOWNLOAD\\n'; return 99; }
          npm() { printf 'npm'; printf ' <%s>' "$@"; printf '\\n'; }
          """
          + node_setup,
          tmp,
          skip,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("UNEXPECTED", result.stdout)
        self.assertFalse((Path(tmp) / ".nvm").exists())
        if skip == "0":
          self.assertIn(
            f"npm <install> <--global> <--prefix> <{tmp}/.local>", result.stdout
          )
          for package in ("prettier", "pyright", "@earendil-works/pi-coding-agent"):
            self.assertIn(f"<{package}>", result.stdout)
        else:
          self.assertEqual(result.stdout, "")

  def test_lfs_uses_brew_node_tools_and_preserves_native_python(self):
    source = (ROOT / "install.sh").read_text()
    node_setup = (
      source.split('loginfo "Instalando Lazy.nvim..."', 1)[1]
      .split("\nfi\n", 1)[1]
      .split("\nif configure_install_python;", 1)[0]
    )
    result = self.shell(
      """
      set -Eeuo pipefail
      OP_SYSTEM=lfs
      export HOME=/nonexistent-dotfiles-test-home
      loginfo() { :; }
      require_new_toolchain_dir() { return 99; }
      run_remote_script() { printf 'UNEXPECTED_DOWNLOAD\\n'; return 99; }
      npm() { printf 'UNEXPECTED_NPM\\n'; return 99; }
      """
      + node_setup
      + """
      source "$2"
      uv() { printf 'uv'; printf ' <%s>' "$@"; printf '\\n'; }
      configure_install_python
      """,
      str(ROOT / "scripts/lib/install-python.sh"),
    )
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertNotIn("UNEXPECTED", result.stdout)
    self.assertIn("<--python> </usr/bin/python3>", result.stdout)
    self.assertIn("<--no-python-downloads>", result.stdout)

  def test_alpine_python_sync_uses_system_python_without_managed_downloads(self):
    for skip, failure in (("0", "0"), ("0", "29"), ("1", "0")):
      with self.subTest(skip=skip, failure=failure):
        result = self.shell(
          """
          set -Eeuo pipefail
          source "$2"
          OP_SYSTEM=alpine OM_INSTALL_SKIP_TOOLCHAINS=$3
          failure=$4 REPO_DIR='/fixture/repo with spaces'
          loginfo() { :; }
          pyenv() { printf 'UNEXPECTED_PYENV\\n'; return 99; }
          run_remote_script() { printf 'UNEXPECTED_DOWNLOAD\\n'; return 99; }
          uv() {
            printf 'venv=<%s> uv' "$UV_PROJECT_ENVIRONMENT"
            printf ' <%s>' "$@"; printf '\\n'
            return "$failure"
          }
          if configure_install_python; then
            printf 'SUCCESS\\n'
          else
            printf 'FAILED %s: %s\\n' "$?" "$PYTHON_SETUP_STEP"
          fi
          """,
          str(ROOT / "scripts/lib/install-python.sh"),
          skip,
          failure,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("UNEXPECTED", result.stdout)
        if skip == "1":
          self.assertEqual(result.stdout, "SUCCESS\n")
        else:
          self.assertIn("venv=</fixture/repo with spaces/.venv>", result.stdout)
          self.assertIn(
            "<--locked> <--python> </usr/bin/python3> <--no-python-downloads>",
            result.stdout,
          )
          self.assertIn(
            "SUCCESS" if failure == "0" else "FAILED 29: Sync", result.stdout
          )

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

  def test_lfs_preserves_native_tools_and_installs_missing_tools_with_brew(self):
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      (root / "config").mkdir()
      (root / "config/install-platforms.list").write_text("lfs lfs,lebasix linuxbrew\n")
      (root / "config/packages.list").write_text(
        "lfs brew bash\nlfs brew missing-formula missing-command\n"
        "darwin cask forbidden\n"
      )
      (root / "missing-command").write_text("#!/bin/sh\nexit 0\n")
      (root / "missing-command").chmod(0o755)
      result = self.shell(
        """
        set -Eeuo pipefail
        REPO_DIR=$2
        export PATH="$2:$PATH"
        loginfo() { printf '%s\\n' "$*"; }
        install_homebrew() { printf 'LOAD_BREW\\n'; }
        brew() { printf 'brew'; printf ' <%s>' "$@"; printf '\\n'; }
        sudo() { printf 'UNEXPECTED_SUDO\\n'; return 99; }
        detect_install_platform Linux lebasix 0
        install_platform_packages lfs
        """,
        tmp,
      )
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertIn("lfs\n", result.stdout)
      self.assertIn("Keeping native bash", result.stdout)
      self.assertIn("brew <install> <missing-formula>", result.stdout)
      self.assertNotIn("<bash>", result.stdout)
      self.assertNotIn("bundle", result.stdout)
      self.assertNotIn("UNEXPECTED", result.stdout)

  def test_lfs_all_native_selection_avoids_an_empty_brew_install(self):
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      (root / "config").mkdir()
      (root / "config/install-platforms.list").write_text("lfs lfs linuxbrew\n")
      (root / "config/packages.list").write_text("lfs brew bash")
      result = self.shell(
        """
        set -Eeuo pipefail
        REPO_DIR=$2
        loginfo() { :; }
        install_homebrew() { printf 'LOAD_BREW\\n'; }
        brew() { printf 'UNEXPECTED_BREW_INSTALL\\n'; return 99; }
        install_platform_packages lfs
        """,
        tmp,
      )
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertEqual(result.stdout, "LOAD_BREW\n")

  def test_lfs_brew_loading_keeps_native_python_first(self):
    source = (ROOT / "install.sh").read_text()
    loader = (
      "load_brew() {"
      + source.split("load_brew() {", 1)[1].split("\ninstall_homebrew()", 1)[0]
    )
    result = self.shell(
      """
      set -Eeuo pipefail
      OP_SYSTEM=lfs
      brew() { printf 'export PATH=/fixture/brew/bin:$PATH\\n'; }
      """
      + loader
      + '\nload_brew\nprintf "%s\\n" "$PATH"\n'
    )
    self.assertEqual(result.returncode, 0, result.stderr)
    paths = result.stdout.strip().split(":")
    self.assertLess(paths.index("/usr/bin"), paths.index("/fixture/brew/bin"))

  def test_lfs_brew_failure_is_propagated(self):
    result = self.shell("""
      set -Eeuo pipefail
      loginfo() { :; }
      install_homebrew() { return 23; }
      brew() { printf 'UNEXPECTED_INSTALL\\n'; }
      if install_platform_packages lfs; then exit 99; else exit $?; fi
    """)
    self.assertEqual(result.returncode, 23)
    self.assertNotIn("UNEXPECTED", result.stdout)

  def test_supported_platforms(self):
    for kernel, distro, expected in (
      ("Darwin", "", "darwin"),
      ("Linux", "ubuntu", "ubuntu"),
      ("Linux", "debian", "debian"),
      ("Linux", "fedora", "fedora"),
      ("Linux", "fedora-asahi-remix", "fedora"),
      ("Linux", "omarchy", "arch"),
      ("Linux", "arch", "arch"),
      ("Linux", "alpine", "alpine"),
      ("Linux", "lfs", "lfs"),
      ("Linux", "lebasix", "lfs"),
    ):
      with self.subTest(distro=distro or kernel):
        result = self.shell('detect_install_platform "$2" "$3" 0', kernel, distro)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), expected)

  def test_unsupported_and_immutable_platforms(self):
    for kernel, distro, ostree in (
      ("Linux", "linuxmint", "0"),
      ("Linux", "", "0"),
      ("Linux", "debian", "1"),
      ("Linux", "ubuntu", "1"),
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

  def test_alpine_uses_native_packages_and_noninteractive_doas_without_brew(self):
    result = self.shell("""
      set -Eeuo pipefail
      OM_INSTALL_ASSUME_YES=1
      loginfo() { :; }
      doas() { printf 'doas'; printf ' <%s>' "$@"; printf '\\n'; }
      sudo() { printf 'UNEXPECTED_SUDO\\n'; return 99; }
      install_homebrew() { printf 'UNEXPECTED_BREW\\n'; return 99; }
      install_platform_packages alpine
    """)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertTrue(result.stdout.startswith("doas <-n> <apk> <add>"))
    for package in (
      "bash",
      "build-base",
      "git",
      "zsh",
      "tmux",
      "neovim",
      "vim",
      "nodejs",
      "npm",
      "python3",
      "uv",
      "ruff",
      "stylua",
      "taplo",
      "lua-language-server",
      "rust-analyzer",
      "tree-sitter-cli",
      "shadow",
    ):
      self.assertIn(f"<{package}>", result.stdout)
    for forbidden in ("UNEXPECTED", "gcompat", "glibc", "systemd", "upgrade"):
      self.assertNotIn(forbidden, result.stdout)

  def test_alpine_package_failure_is_not_hidden(self):
    result = self.shell("""
      set -Eeuo pipefail
      loginfo() { :; }
      doas() { printf 'apk failed\\n' >&2; return 23; }
      install_homebrew() { printf 'UNEXPECTED_BREW\\n'; }
      install_platform_packages alpine
      printf 'UNEXPECTED_SUCCESS\\n'
    """)
    self.assertEqual(result.returncode, 23)
    self.assertIn("apk failed", result.stderr)
    self.assertNotIn("UNEXPECTED", result.stdout)

  def test_alpine_uses_existing_sudo_when_doas_is_absent(self):
    result = self.shell("""
      set -Eeuo pipefail
      command() {
        if [[ "$*" == '-v doas' ]]; then return 1; fi
        builtin command "$@"
      }
      sudo() { printf 'sudo'; printf ' <%s>' "$@"; printf '\\n'; }
      run_install_privileged alpine chsh -s /bin/zsh 'user with spaces'
    """)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "sudo <chsh> <-s> </bin/zsh> <user with spaces>\n")

  def test_alpine_login_shell_uses_doas(self):
    source = (ROOT / "install.sh").read_text()
    setup = source.split('install_platform_packages "$OP_SYSTEM"', 1)[1].split(
      'loginfo "Configurando Oh My Zsh..."', 1
    )[0]
    result = self.shell(
      """
      set -Eeuo pipefail
      OP_SYSTEM=alpine
      OM_INSTALL_ASSUME_YES=0
      doas() { printf 'doas %s\\n' "$*"; }
      sudo() { printf 'UNEXPECTED_SUDO\\n'; return 99; }
      getent() { printf 'user:x:1000:1000::/home/user:/bin/bash\\n'; }
      zsh() { :; }
      """
      + setup
    )
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn("doas chsh -s zsh", result.stdout)
    self.assertNotIn("UNEXPECTED", result.stdout)

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

  def test_apt_and_macos_package_managers(self):
    for platform in ("ubuntu", "debian", "darwin"):
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
        if platform in ("ubuntu", "debian"):
          self.assertIn("apt-get update", result.stdout)
          self.assertIn("apt-get install -y", result.stdout)
          self.assertIn("libssl-dev", result.stdout)
          self.assertIn("fd-find", result.stdout)
          self.assertIn("font-fira-code-nerd-font", result.stdout)
          if platform == "debian":
            native_line = result.stdout.splitlines()[1].split()
            self.assertIn("procps", native_line)
            self.assertIn("libffi-dev", native_line)
            self.assertNotIn("watch", native_line)
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
        "arch,pacman native git\n"
        "darwin brew mac-only\n"
        "arch brew bat\n"
        "arch brew rtk"
      )
      shutil.copyfile(
        ROOT / "config/install-platforms.list", root / "config/install-platforms.list"
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
      "debian": {"native", "brew"},
      "apt": {"native", "brew"},
      "dnf": {"native", "brew"},
      "pacman": {"native", "brew"},
      "fedora": {"native", "brew"},
      "arch": {"native", "brew"},
      "alpine": {"native"},
      "apk": {"native"},
      "lfs": {"brew"},
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
        if options and platforms == "lfs":
          self.assertRegex(options[0], r"^[a-zA-Z0-9_-]+$")
        elif options:
          self.assertEqual(platforms, "darwin")
          self.assertIn(
            (provider, options[0]), (("brew", "unlinked"), ("tap", "trusted"))
          )

  def test_alpine_verification_does_not_require_brew_or_pyenv(self):
    source = (ROOT / "install.sh").read_text()
    verification = source.split('loginfo "Verificando a instalação..."', 1)[1].split(
      "\nrequired_links=", 1
    )[0]
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      (root / ".venv/bin").mkdir(parents=True)
      for name in ("python", "pyright", "ruff"):
        tool = root / ".venv/bin" / name
        tool.write_text("#!/bin/sh\nexit 0\n")
        tool.chmod(0o755)
      for platform in ("alpine", "darwin", "ubuntu", "debian", "fedora", "arch"):
        with self.subTest(platform=platform):
          result = self.shell(
            """
            set -Eeuo pipefail
            REPO_DIR=$2 OP_SYSTEM=$3 python_failure=''
            OM_INSTALL_SKIP_TOOLCHAINS=0
            logerror() { printf '%s\\n' "$1" >&2; }
            command() {
              case "$2" in brew|pyenv|python) return 1 ;; esac
              return 0
            }
            """
            + verification,
            tmp,
            platform,
          )
          if platform == "alpine":
            self.assertEqual(result.returncode, 0, result.stderr)
          else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("brew", result.stderr)

  def test_linux_does_not_install_or_require_ghostty(self):
    source = (ROOT / "install.sh").read_text()
    self.assertNotIn("ghostty-ubuntu", source)
    self.assertNotIn("command -v ghostty", source)
    self.assertNotIn("required_commands+=(ghostty)", source)

  def test_debian_preserves_locale_and_does_not_install_ubuntu_ghostty(self):
    source = (ROOT / "install.sh").read_text()
    setup = source.split('install_platform_packages "$OP_SYSTEM"', 1)[1].split(
      'loginfo "Configurando Oh My Zsh..."', 1
    )[0]
    with tempfile.TemporaryDirectory() as tmp:
      result = self.shell(
        """
        set -Eeuo pipefail
        OP_SYSTEM=debian
        HOME=$2
        sudo() { printf 'sudo %s\\n' "$*"; }
        locale() { printf 'UNEXPECTED_LOCALE\\n'; }
        run_remote_script() { printf 'UNEXPECTED_REMOTE\\n'; }
        getent() { printf 'user:x:1000:1000::/home/user:/bin/bash\\n'; }
        command() {
          case "$*" in
            '-v fd'|'-v bat') return 1 ;;
            '-v fdfind') printf '/usr/bin/fdfind\\n' ;;
            '-v batcat') printf '/usr/bin/batcat\\n' ;;
            '-v zsh') printf '/usr/bin/zsh\\n' ;;
            *) return 99 ;;
          esac
        }
        """
        + setup,
        tmp,
      )
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertNotIn("UNEXPECTED", result.stdout)
      self.assertNotIn("locale", result.stdout)
      self.assertIn("chsh -s /usr/bin/zsh", result.stdout)
      self.assertEqual(
        (Path(tmp) / ".local/bin/fd").readlink(), Path("/usr/bin/fdfind")
      )
      self.assertEqual(
        (Path(tmp) / ".local/bin/bat").readlink(), Path("/usr/bin/batcat")
      )

  def test_platform_table_can_add_an_apt_distro_without_shell_changes(self):
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      (root / "config").mkdir()
      # Both detection and manager lookup must consume an unterminated last row.
      (root / "config/install-platforms.list").write_text("example example,alias apt")
      (root / "config/packages.list").write_text(
        "apt,example native git\nexample brew bat\nubuntu native ubuntu-only\n"
      )
      result = self.shell(
        """
        set -Eeuo pipefail
        REPO_DIR=$2
        loginfo() { :; }
        sudo() { printf 'sudo %s\\n' "$*"; }
        install_homebrew() { :; }
        brew() { printf 'brew %s\\n' "$*"; }
        platform=$(detect_install_platform Linux alias)
        install_platform_packages "$platform"
        """,
        tmp,
      )
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertEqual(
        result.stdout.splitlines(),
        [
          "sudo DEBIAN_FRONTEND=noninteractive apt-get update",
          "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git",
          "brew install bat",
        ],
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
