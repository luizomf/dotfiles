# Copyright (c) 2026 Luiz Otávio Miranda

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMIT_SCRIPT = PROJECT_ROOT / "scripts" / "commit"
BASH = Path("/bin/bash")
GIT = "/usr/bin/git"


class CommitCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.repo = Path(self.temp_dir.name) / "repo"
        self.bin_dir = Path(self.temp_dir.name) / "bin"
        self.repo.mkdir()
        self.bin_dir.mkdir()
        # Do not inherit Git directories, indexes, hooks or signing policy.
        self.env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        self.env.update(
            {
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_COUNT": "0",
            }
        )
        scripts = self.repo / "scripts"
        scripts.mkdir()
        shutil.copy2(COMMIT_SCRIPT, scripts / "commit")
        shutil.copy2(
            PROJECT_ROOT / "scripts" / "check_staged", scripts / "check_staged"
        )
        self.run_git("init", "-q")
        self.run_git("config", "user.name", "Test User")
        self.run_git("config", "user.email", "test@example.com")
        self.write("tracked.txt", "original\n")
        self.run_git("add", "tracked.txt")
        self.run_git("commit", "-qm", "initial")
        self.make_command("title", "exit 0")
        self.make_command(
            "sannux_ephemeral",
            'cat >"$PROMPT_LOG"\n'
            'printf "called\\n" >"$MODEL_LOG"\n'
            'printf "chore: test commit\\n" >"$CURDIR/commit-message.txt"',
        )

    def run_git(
        self, *args: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        # Arguments come from test fixtures, never external input.
        return subprocess.run(  # noqa: S603
            [GIT, *args],
            cwd=self.repo,
            env=self.env,
            check=check,
            text=True,
            capture_output=True,
        )

    def write(self, relative_path: str, content: str) -> None:
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def make_command(self, name: str, body: str) -> None:
        path = self.bin_dir / name
        path.write_text(f"#!/bin/sh\n{body}\n")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def minimal_path(self) -> str:
        system_bin = self.bin_dir / "system"
        system_bin.mkdir()
        for name in (
            "bash",
            "git",
            "dirname",
            "mktemp",
            "rm",
            "grep",
            "head",
            "awk",
            "cat",
        ):
            executable = shutil.which(name)
            if executable is None:
                self.fail(f"Test prerequisite missing: {name}")
            (system_bin / name).symlink_to(executable)
        return f"{self.bin_dir}:{system_bin}"

    def run_commit(
        self,
        *args: str,
        path: str | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = self.env.copy()
        env.update(
            {
                "PATH": path or f"{self.bin_dir}:{env['PATH']}",
                "MODEL": "test-model",
                "LOCAL_MODEL_REASONING": "low",
                "MODEL_LOG": str(self.repo / "model.log"),
                "PROMPT_LOG": str(self.repo / "prompt.log"),
                "CHECK_LOG": str(self.repo / "check.log"),
            }
        )
        if extra_env:
            env.update(extra_env)
        # Execute the repository script with fixture-controlled arguments.
        return subprocess.run(  # noqa: S603
            [str(BASH), "./scripts/commit", *args],
            cwd=self.repo,
            env=env,
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
        )

    def test_git_hook_blocks_bad_staging_without_calling_a_model(self) -> None:
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.symlink_to(PROJECT_ROOT / ".githooks" / "pre-commit")
        self.env.pop("MODEL", None)
        self.env.pop("LOCAL_MODEL_REASONING", None)
        head_before = self.run_git("rev-parse", "HEAD").stdout
        self.write("tracked.txt", "trailing whitespace   \n")
        self.run_git("add", "tracked.txt")

        rejected = self.run_git("commit", "-qm", "invalid", check=False)

        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("trailing whitespace", rejected.stdout + rejected.stderr)
        self.assertEqual(head_before, self.run_git("rev-parse", "HEAD").stdout)

        self.write("tracked.txt", "valid\n")
        self.run_git("add", "tracked.txt")
        accepted = self.run_git("commit", "-qm", "valid", check=False)

        self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)
        self.assertEqual("valid\n", self.run_git("show", "HEAD:tracked.txt").stdout)
        self.assertFalse((self.repo / "model.log").exists())

    def test_host_commits_message_written_in_an_isolated_model_workspace(self) -> None:
        self.write("tracked.txt", "selected\n")
        self.run_git("add", "tracked.txt")
        (self.repo / ".git" / "hooks" / "pre-commit").symlink_to(
            PROJECT_ROOT / ".githooks" / "pre-commit"
        )
        self.make_command(
            "sannux_ephemeral",
            'cat >"$PROMPT_LOG"\n'
            'test -n "${CURDIR:-}" && test "$CURDIR" != "$PWD" || exit 91\n'
            'test ! -e "$CURDIR/.git" || exit 92\n'
            'printf "chore: document selected change\\n" >"$CURDIR/commit-message.txt"',
        )

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(
            "chore: document selected change\n",
            self.run_git("log", "-1", "--format=%s").stdout,
        )
        self.assertEqual("selected\n", self.run_git("show", "HEAD:tracked.txt").stdout)
        self.assertIn("+selected", (self.repo / "prompt.log").read_text())

    def test_no_staged_changes_does_not_call_model(self) -> None:
        result = self.run_commit()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No staged changes", result.stdout + result.stderr)
        self.assertFalse((self.repo / "model.log").exists())

    def test_partially_staged_file_is_refused_without_changing_index(self) -> None:
        self.write("tracked.txt", "staged\n")
        self.run_git("add", "tracked.txt")
        self.write("tracked.txt", "unstaged\n")
        index_before = self.run_git("diff", "--cached", "--binary").stdout

        result = self.run_commit()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("additional unstaged edits", result.stdout + result.stderr)
        self.assertFalse((self.repo / "model.log").exists())
        self.assertEqual(
            index_before, self.run_git("diff", "--cached", "--binary").stdout
        )
        self.assertEqual("unstaged\n", (self.repo / "tracked.txt").read_text())

    def test_success_checks_and_commits_only_the_staged_selection(self) -> None:
        self.write("tracked.txt", "selected\n")
        self.run_git("add", "tracked.txt")
        self.write("untracked.txt", "not selected\n")

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("called\n", (self.repo / "model.log").read_text())
        self.assertEqual(
            "tracked.txt\n",
            self.run_git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"
            ).stdout,
        )
        self.assertTrue((self.repo / "untracked.txt").exists())
        self.assertEqual("", self.run_git("diff", "--cached").stdout)
        self.assertIn("+selected", (self.repo / "prompt.log").read_text())
        self.assertNotIn("untracked.txt", (self.repo / "prompt.log").read_text())

    def test_model_success_without_a_message_does_not_commit(self) -> None:
        self.write("tracked.txt", "selected\n")
        self.run_git("add", "tracked.txt")
        head_before = self.run_git("rev-parse", "HEAD").stdout
        self.make_command("sannux_ephemeral", 'cat >"$PROMPT_LOG"\nexit 0')

        result = self.run_commit()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("did not write a commit message", result.stderr)
        self.assertEqual(head_before, self.run_git("rev-parse", "HEAD").stdout)
        self.assertEqual("selected\n", self.run_git("show", ":tracked.txt").stdout)

    def test_concurrent_commit_is_reported_without_rollback(self) -> None:
        self.write("tracked.txt", "selected\n")
        self.run_git("add", "tracked.txt")
        self.make_command(
            "sannux_ephemeral",
            'cat >"$PROMPT_LOG"\n'
            'printf "chore: selected change\\n" >"$CURDIR/commit-message.txt"\n'
            'printf "unexpected\\n" >tracked.txt\n'
            "git add tracked.txt\ngit commit -qm 'wrong content'",
        )

        result = self.run_commit()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("changed during message generation", result.stderr)
        self.assertEqual(
            "unexpected\n", self.run_git("show", "HEAD:tracked.txt").stdout
        )

    def test_commit_succeeds_without_a_terminal(self) -> None:
        self.write("tracked.txt", "selected\n")
        self.run_git("add", "tracked.txt")
        shutil.copy2(PROJECT_ROOT / "scripts" / "title", self.bin_dir / "title")

        result = self.run_commit(
            extra_env={"TMUX": "", "TMUX_PANE": "", "TERM": "dumb"}
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", self.run_git("diff", "--cached").stdout)

    def test_configured_python_checks_work_without_a_project_virtualenv(self) -> None:
        self.write("pyproject.toml", "[tool.ruff]\n[tool.pyright]\n")
        self.write("module.py", "value = 1\n")
        self.run_git("add", "pyproject.toml", "module.py")
        self.make_command("ruff", 'printf "ruff %s\\n" "$*" >>"$CHECK_LOG"')
        self.make_command("pyright", 'printf "pyright\\n" >>"$CHECK_LOG"')
        self.make_command("uv", "exit 99")

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        calls = (self.repo / "check.log").read_text()
        self.assertIn("ruff check --no-fix -- module.py", calls)
        self.assertIn("ruff format --check -- module.py", calls)
        self.assertIn("pyright\n", calls)
        self.assertFalse((self.repo / ".venv").exists())

    def test_python_config_discovery_accepts_spacing_but_not_table_prefixes(
        self,
    ) -> None:
        self.write("module.py", "value = 1\n")
        self.make_command("ruff", 'printf "ruff\\n" >>"$CHECK_LOG"')
        self.make_command("pyright", "exit 23")
        for config, expected_status in (
            ("[ tool . ruff ]\n[ tool . pyright ]\n", 23),
            ("[tool.ruff_extra]\n[tool.pyright_extra]\n", 0),
        ):
            with self.subTest(config=config):
                self.write("pyproject.toml", config)
                self.run_git("add", "pyproject.toml", "module.py")

                result = self.run_commit()

                self.assertEqual(expected_status, result.returncode)
                if expected_status:
                    self.assertTrue((self.repo / "check.log").exists())
                    self.assertFalse((self.repo / "model.log").exists())

    def test_missing_configured_python_runner_fails_before_model(self) -> None:
        self.write("pyproject.toml", "[tool.ruff]\n")
        self.write("module.py", "value = 1\n")
        self.run_git("add", "pyproject.toml", "module.py")
        result = self.run_commit(path=self.minimal_path())

        self.assertNotEqual(0, result.returncode)
        self.assertIn("ruff", result.stdout + result.stderr)
        self.assertFalse((self.repo / "model.log").exists())

    def test_python_deletion_runs_configured_whole_project_pyright(self) -> None:
        self.write("pyproject.toml", "[tool.pyright]\n")
        self.write("old.py", "value = 1\n")
        self.run_git("add", "pyproject.toml", "old.py")
        self.run_git("commit", "-qm", "add python")
        self.run_git("rm", "old.py")
        self.make_command("pyright", 'printf "pyright\\n" >>"$CHECK_LOG"')

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(
            {"pyright"},
            set((self.repo / "check.log").read_text().splitlines()),
        )

    def test_removing_python_sources_runs_pyright_even_without_a_py_suffix(
        self,
    ) -> None:
        self.write("pyrightconfig.json", "{}\n")
        self.write("command", "#!/usr/bin/env python3\nvalue = 1\n")
        self.write("module.py", "value = 1\n")
        self.run_git("add", "pyrightconfig.json", "command", "module.py")
        self.run_git("commit", "-qm", "add python sources")
        self.make_command("pyright", "exit 23")

        for operation in (("rm", "command"), ("mv", "module.py", "module.txt")):
            with self.subTest(operation=operation):
                self.run_git(*operation)

                result = self.run_commit()

                self.assertEqual(23, result.returncode, result.stdout + result.stderr)
                self.assertFalse((self.repo / "model.log").exists())
            self.run_git("reset", "--hard", "HEAD")

    def test_shell_syntax_failure_does_not_call_shellcheck_or_model(self) -> None:
        self.write("broken.sh", "#!/usr/bin/env bash\nif true; then\n")
        self.run_git("add", "broken.sh")
        self.make_command("shellcheck", 'printf "shellcheck\\n" >>"$CHECK_LOG"')

        result = self.run_commit()

        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.repo / "check.log").exists())
        self.assertFalse((self.repo / "model.log").exists())

    def test_shell_dialects_are_checked_with_arguments_or_without_shebangs(
        self,
    ) -> None:
        self.make_command("shellcheck", "exit 99")
        for filename, content in (
            ("command", "#!/bin/sh -e\nif true; then\n"),
            ("fragment.bash", "if true; then\n"),
        ):
            with self.subTest(filename=filename):
                self.run_git("reset", "--hard", "HEAD")
                self.write(filename, content)
                self.run_git("add", filename)

                result = self.run_commit()

                self.assertNotEqual(0, result.returncode)
                self.assertNotEqual(99, result.returncode)
                self.assertFalse((self.repo / "model.log").exists())

    def test_shellcheck_follows_a_sourced_project_file(self) -> None:
        shellcheck = shutil.which("shellcheck")
        if shellcheck is None:
            self.skipTest("ShellCheck is required for this integration check")
        (self.bin_dir / "shellcheck").symlink_to(shellcheck)
        self.write("lib/helper.sh", "#!/bin/sh\nprintf '%s\\n' helper\n")
        self.run_git("add", "lib/helper.sh")
        self.run_git("commit", "-qm", "add shell helper")
        self.write("entry.sh", "#!/bin/sh\n. ./lib/helper.sh\n")
        self.run_git("add", "entry.sh")

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", self.run_git("diff", "--cached").stdout)

    def test_missing_shellcheck_fails_before_model(self) -> None:
        self.write("valid.sh", "#!/bin/sh\nprintf '%s\\n' ok\n")
        self.run_git("add", "valid.sh")

        result = self.run_commit(path=self.minimal_path())

        self.assertNotEqual(0, result.returncode)
        self.assertIn("shellcheck", result.stdout + result.stderr)
        self.assertFalse((self.repo / "model.log").exists())

    def test_nested_zsh_startup_files_use_zsh_without_shellcheck(self) -> None:
        self.write("nested/.zshrc", "#!/usr/bin/env bash\nexport VALUE=1\n")
        self.write("nested/.zprofile", "export PROFILE=1\n")
        self.run_git("add", "nested/.zshrc", "nested/.zprofile")
        self.make_command("zsh", 'printf "zsh %s\\n" "$*" >>"$CHECK_LOG"')
        self.make_command("shellcheck", "exit 99")

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(
            {"zsh -n ./nested/.zprofile", "zsh -n ./nested/.zshrc"},
            set((self.repo / "check.log").read_text().splitlines()),
        )

    def test_staged_symlink_does_not_make_prettier_reject_the_commit(self) -> None:
        prettier = shutil.which("prettier")
        if prettier is None:
            self.skipTest("Prettier is required for this integration check")
        (self.bin_dir / "prettier").symlink_to(prettier)
        self.write("config/prettier.json", "{}\n")
        (self.repo / ".prettierrc.json").symlink_to("config/prettier.json")
        self.run_git("add", ".prettierrc.json", "config/prettier.json")

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", self.run_git("diff", "--cached").stdout)
        self.assertTrue((self.repo / ".prettierrc.json").is_symlink())

    def test_staged_pyproject_is_not_sent_to_prettier(self) -> None:
        self.write(".prettierrc.json", "{}\n")
        self.run_git("add", ".prettierrc.json")
        self.run_git("commit", "-qm", "configure prettier")
        self.write("pyproject.toml", "[tool.pyright]\n")
        self.run_git("add", "pyproject.toml")
        self.make_command("pyright", 'printf "pyright\\n" >>"$CHECK_LOG"')
        self.make_command("prettier", 'case "$*" in *toml*) exit 23;; esac')

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(
            {"pyright"},
            set((self.repo / "check.log").read_text().splitlines()),
        )
        self.assertEqual(
            "pyproject.toml\n",
            self.run_git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"
            ).stdout,
        )

    def test_prettierrc_javascript_configuration_blocks_on_failure(self) -> None:
        self.write(".prettierrc.js", "module.exports = {};\n")
        self.write("README.md", "unformatted\n")
        self.run_git("add", ".prettierrc.js", "README.md")
        self.make_command("prettier", "exit 23")

        result = self.run_commit()

        self.assertEqual(23, result.returncode)
        self.assertFalse((self.repo / "model.log").exists())

    def test_package_prettier_configuration_runs_prettier(self) -> None:
        self.write("package.json", '{"prettier": "shared-config"}\n')
        self.write("README.md", "formatted\n")
        self.run_git("add", "package.json", "README.md")
        self.make_command("prettier", 'printf "prettier %s\\n" "$*" >>"$CHECK_LOG"')

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("README.md", (self.repo / "check.log").read_text())

    def test_prettier_dependency_alone_is_not_configuration(self) -> None:
        self.write("package.json", '{"devDependencies": {"prettier": "3.0.0"}}\n')
        self.write("README.md", "formatted\n")
        self.run_git("add", "package.json", "README.md")
        self.make_command("prettier", "exit 23")

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse((self.repo / "check.log").exists())

    def test_configured_prettier_eslint_and_typescript_use_local_tools(self) -> None:
        self.write(".prettierrc.json", "{}\n")
        self.write("eslint.config.js", "export default [];\n")
        self.write("tsconfig.json", "{}\n")
        self.write("web.ts", "const value: number = 1;\n")
        self.run_git(
            "add", ".prettierrc.json", "eslint.config.js", "tsconfig.json", "web.ts"
        )
        self.make_command("prettier", 'printf "prettier %s\\n" "$*" >>"$CHECK_LOG"')
        local_bin = self.repo / "node_modules" / ".bin"
        local_bin.mkdir(parents=True)
        for tool in ("eslint", "tsc"):
            path = local_bin / tool
            path.write_text(f'#!/bin/sh\nprintf "{tool} %s\\n" "$*" >>"$CHECK_LOG"\n')
            path.chmod(path.stat().st_mode | stat.S_IXUSR)

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        calls = (self.repo / "check.log").read_text()
        self.assertIn("prettier --check", calls)
        self.assertIn("web.ts", calls)
        self.assertIn("eslint -- eslint.config.js", calls)
        self.assertIn("eslint -- web.ts", calls)
        self.assertIn("tsc --noEmit -p tsconfig.json", calls)

    def test_module_javascript_is_blocked_by_configured_eslint(self) -> None:
        self.write("eslint.config.ts", "export default [];\n")
        self.run_git("add", "eslint.config.ts")
        self.run_git("commit", "-qm", "configure eslint")
        self.write("web.mjs", "const value = ;\n")
        self.run_git("add", "web.mjs")
        local_bin = self.repo / "node_modules" / ".bin"
        local_bin.mkdir(parents=True)
        eslint = local_bin / "eslint"
        eslint.write_text("#!/bin/sh\nexit 23\n")
        eslint.chmod(eslint.stat().st_mode | stat.S_IXUSR)

        result = self.run_commit()

        self.assertEqual(23, result.returncode)
        self.assertFalse((self.repo / "model.log").exists())
        self.assertEqual(
            "web.mjs\n", self.run_git("diff", "--cached", "--name-only").stdout
        )

    def test_git_index_error_is_propagated_without_calling_model(self) -> None:
        self.write("tracked.txt", "selected\n")
        self.run_git("add", "tracked.txt")
        (self.repo / ".git" / "index").write_text("not an index")

        result = self.run_commit()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("index", result.stdout + result.stderr)
        self.assertFalse((self.repo / "model.log").exists())

    def test_conflict_marker_check_does_not_call_model(self) -> None:
        self.write("tracked.txt", "<<<<<<< ours\na\n=======\nb\n>>>>>>> theirs\n")
        self.run_git("add", "tracked.txt")

        result = self.run_commit()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("leftover conflict marker", result.stdout + result.stderr)
        self.assertFalse((self.repo / "model.log").exists())

    def test_verbose_mode_preserves_pi_argument_passthrough(self) -> None:
        self.write("tracked.txt", "selected\n")
        self.run_git("add", "tracked.txt")
        self.make_command("pi_parse_json", "cat")
        self.make_command(
            "sannux_ephemeral",
            'cat >"$PROMPT_LOG"\nprintf "%s\\n" "$*" >"$MODEL_LOG"\n'
            'printf "chore: test commit\\n" >"$CURDIR/commit-message.txt"',
        )

        result = self.run_commit("--verbose", "--", "--extra")

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        invocation = (self.repo / "model.log").read_text()
        self.assertIn("--mode json", invocation)
        self.assertIn("-- --extra", invocation)

    def test_failing_staged_check_does_not_call_model_or_change_index(self) -> None:
        self.write("tracked.txt", "trailing whitespace   \n")
        self.run_git("add", "tracked.txt")
        index_before = self.run_git("diff", "--cached", "--binary").stdout

        result = self.run_commit()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trailing whitespace", result.stdout + result.stderr)
        self.assertFalse((self.repo / "model.log").exists())
        self.assertEqual(
            index_before, self.run_git("diff", "--cached", "--binary").stdout
        )


if __name__ == "__main__":
    unittest.main()
