"""Test installer policy without executing install.sh or package managers."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'scripts/lib/install-platform.sh'


class InstallPlatformTests(unittest.TestCase):
    def shell(self, script, *args):
        return subprocess.run(['bash', '-c', 'source "$1" || exit; '+script,
                               'test', str(MODULE), *args],
                              text=True, capture_output=True, timeout=5)

    def run_error_policy(self, body):
        # Exercise the actual prologue without running the destructive installer.
        lines = (ROOT / 'install.sh').read_text().splitlines()
        options = next(line for line in lines if line.startswith('set -'))
        trap = next(line for line in lines if line.startswith('trap '))
        script = options + '\nlogerror() { printf "INSTALLER_ERR\\n" >&2; }\n' + trap + '\n' + body
        # macOS /bin/bash 3.2 differs from newer Bash for ERR in a guarded $(...).
        return subprocess.run(['/bin/bash', '-c', script], text=True,
                              capture_output=True, timeout=5)

    def test_expected_subshell_probe_does_not_report_installation_failure(self):
        result = self.run_error_policy('''
            probe() {
                local value
                if ! value="$(false)"; then printf 'expected-miss\\n'; fi
            }
            probe
            printf 'READY\\n'
        ''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('READY', result.stdout)
        self.assertEqual(result.stderr, '')

    def test_real_failures_still_abort_and_report(self):
        for command in ('false', 'fail() { false; }; fail', 'value="$(false)"', '( false )'):
            with self.subTest(command=command):
                result = self.run_error_policy(command + '\nprintf "UNREACHABLE\\n"')
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('UNREACHABLE', result.stdout)
                self.assertIn('INSTALLER_ERR', result.stderr)

    def test_supported_platforms(self):
        for kernel, distro, expected in (
            ('Darwin', '', 'darwin'), ('Linux', 'ubuntu', 'ubuntu'),
            ('Linux', 'fedora', 'fedora'),
            ('Linux', 'fedora-asahi-remix', 'fedora'),
        ):
            with self.subTest(distro=distro or kernel):
                result = self.shell('detect_install_platform "$2" "$3" 0', kernel, distro)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)

    def test_unsupported_and_immutable_platforms(self):
        for kernel, distro, ostree in (
            ('Linux', 'debian', '0'), ('FreeBSD', '', '0'),
            ('Linux', 'fedora', '1'), ('Linux', 'fedora-asahi-remix', '1'),
        ):
            with self.subTest(distro=distro, ostree=ostree):
                result = self.shell('detect_install_platform "$2" "$3" "$4"', kernel, distro, ostree)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')

    def test_fedora_commands_use_dnf_and_no_ubuntu_or_system_services(self):
        result = self.shell('''
            loginfo() { :; }
            sudo() { printf 'sudo'; printf ' <%s>' "$@"; printf '\\n'; }
            install_homebrew() { printf 'load-homebrew\\n'; }
            brew() { printf 'brew'; printf ' <%s>' "$@"; printf '\\n'; }
            install_fedora_packages
        ''')
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith('sudo <dnf> <install> <-y>'))
        for package in ('gcc-c++', 'openssl-devel', 'libffi-devel', 'zlib-devel', 'tmux', 'zsh'):
            self.assertIn(f'<{package}>', lines[0])
        self.assertEqual(lines[1], 'load-homebrew')
        self.assertTrue(lines[2].startswith('brew <install>'))
        self.assertIn('<tmux>', lines[2])
        for forbidden in ('apt-get', 'ghostty-ubuntu', 'systemctl', 'kernel', 'bootloader'):
            self.assertNotIn(forbidden, result.stdout)

    def test_existing_toolchain_is_never_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / 'toolchain'
            existing.mkdir()
            sentinel = existing / 'user-data'
            sentinel.write_text('preserve me')
            result = self.shell('require_new_toolchain_dir "$2"', str(existing))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(), 'preserve me')
            link = root / 'broken-link'
            link.symlink_to(root / 'missing-target')
            self.assertNotEqual(self.shell('require_new_toolchain_dir "$2"', str(link)).returncode, 0)
            self.assertTrue(link.is_symlink())
            result = self.shell('require_new_toolchain_dir "$2"', str(root / 'new'))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / 'new').exists())


if __name__ == '__main__':
    unittest.main()
