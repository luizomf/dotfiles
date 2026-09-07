"""Isolated startup checks; no live shell, credentials, tmux or tool invocations."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ZSH = shutil.which('zsh')


@unittest.skipUnless(ZSH, 'zsh is required')
class StartupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = {'HOME': str(self.home), 'PATH': '/usr/bin:/bin', 'TERM': 'dumb'}

    def run_zsh(self, script):
        return subprocess.run([ZSH, '-dfc', script], env=self.env, cwd=self.home,
                              text=True, capture_output=True, timeout=5)

    def test_lazy_generators_and_argument_forwarding(self):
        module = ROOT / 'zsh/config/completions'
        for tool, function, arguments in (
            ('codex', '_codex', 'completion zsh'),
            ('docker', '_docker', 'completion zsh'),
            ('gh', '_gh', 'completion -s zsh'),
            ('just', '_just', '--completions zsh'),
            ('omqueue', '_omqueue_zsh', 'completion zsh'),
        ):
            with self.subTest(tool=tool):
                binary = self.home / 'bin' / tool
                binary.parent.mkdir(exist_ok=True)
                binary.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$HOME/calls"\n'
                                  f"printf '%s\\n' '{function}() {{ print -r -- \"$*\"; }}'\n")
                binary.chmod(0o700)
                (self.home / '.docker/completions').mkdir(parents=True, exist_ok=True)
                (self.home / '.docker/completions/_docker').touch()
                (self.home / 'Justfile').touch()
                result = self.run_zsh(f'''
                    path=("$HOME/bin" $path)
                    autoload -Uz compinit
                    compinit -D -u
                    source {module}
                    [[ ! -e "$HOME/calls" ]] || exit 10
                    service={tool}
                    ${{_comps[{tool}]}} first || exit 11
                    ${{_comps[{tool}]}} second || exit 12
                ''')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), ['first', 'second'])
                self.assertEqual((self.home / 'calls').read_text().splitlines(), [arguments])
                (self.home / 'calls').unlink()
                binary.unlink()

    def test_generation_failure_can_retry(self):
        binary = self.home / 'bin/codex'
        binary.parent.mkdir()
        binary.write_text('#!/bin/sh\nif [ ! -f "$HOME/retry" ]; then exit 1; fi\n'
                          "printf '%s\\n' '_codex() { print recovered; }'\n")
        binary.chmod(0o700)
        result = self.run_zsh(f'''
            path=("$HOME/bin" $path)
            autoload -Uz compinit; compinit -D -u
            source {ROOT / 'zsh/config/completions'}
            service=codex
            ${{_comps[codex]}} && exit 10
            : > "$HOME/retry"
            ${{_comps[codex]}}
        ''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'recovered')

    def test_generator_can_register_a_different_function_name(self):
        binary = self.home / 'bin/just'
        binary.parent.mkdir()
        binary.write_text('#!/bin/sh\n' + "printf '%s\\n' "
                          "'_clap_dynamic_completer_just() { print dynamic; }' "
                          "'compdef _clap_dynamic_completer_just just'\n")
        binary.chmod(0o700)
        (self.home / 'Justfile').touch()
        result = self.run_zsh(f'''
            path=("$HOME/bin" $path)
            autoload -Uz compinit; compinit -D -u
            source {ROOT / 'zsh/config/completions'}
            service=just
            ${{_comps[just]}} || exit 10
            [[ ${{_comps[just]}} == _clap_dynamic_completer_just ]]
        ''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'dynamic')

    def test_no_completion_system_is_a_noop(self):
        result = self.run_zsh(f'source {ROOT / "zsh/config/completions"}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')

    def test_title_outside_tmux_remains_synchronous_and_handles_root(self):
        config = self.home / 'dotfiles/zsh/config'
        config.mkdir(parents=True)
        for name in ('config', 'functions', 'exports', 'aliases', 'keybinds'):
            (config / name).touch()
        title = self.home / 'dotfiles/scripts/title'
        title.parent.mkdir(parents=True)
        title.write_text('#!/bin/sh\nprintf "title:%s\\n" "$1"\n')
        title.chmod(0o700)
        result = self.run_zsh(f'''
            cd /
            source {ROOT / 'zsh/config/use_this_to_load'}
            print ready
        ''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['title:/', 'ready'])

    def test_automatic_tmux_title_does_not_block_loader(self):
        config = self.home / 'dotfiles/zsh/config'
        config.mkdir(parents=True)
        for name in ('config', 'functions', 'exports', 'aliases', 'keybinds'):
            (config / name).touch()
        title = self.home / 'dotfiles/scripts/title'
        title.parent.mkdir(parents=True)
        # A handshake: a synchronous title invocation cannot reach loader-ready.
        title.write_text('#!/bin/sh\n'
                         'for attempt in 1 2 3 4 5 6 7 8 9 10; do\n'
                         '  [ -f "$HOME/loader-ready" ] && exit 0\n'
                         '  sleep 0.1\n'
                         'done\n'
                         'touch "$HOME/title-blocked"\n')
        title.chmod(0o700)
        self.env.update(TMUX='fake', TMUX_PANE='%1')
        result = self.run_zsh(f'''
            source {ROOT / 'zsh/config/use_this_to_load'}
            : > "$HOME/loader-ready"
            [[ ! -e "$HOME/title-blocked" ]]
        ''')
        self.assertEqual(result.returncode, 0, result.stderr)
        # Allow the bounded fixture child to finish before removing its home.
        subprocess.run(['/bin/sleep', '0.2'], check=True)


if __name__ == '__main__':
    unittest.main()
