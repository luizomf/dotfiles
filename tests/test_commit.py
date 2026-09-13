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
        shutil.copy2(COMMIT_SCRIPT, self.repo / "commit")
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
            'git diff --cached --name-only >"$MODEL_LOG"\n'
            "git commit -qm 'test commit'",
        )

    def run_git(
        self, *args: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [GIT, *args],
            cwd=self.repo,
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

    def run_commit(
        self,
        *args: str,
        path: str | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
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
        return subprocess.run(
            [str(BASH), "./commit", *args],
            cwd=self.repo,
            env=env,
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
        )

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
        self.assertEqual("tracked.txt\n", (self.repo / "model.log").read_text())
        self.assertTrue((self.repo / "untracked.txt").exists())
        self.assertEqual("", self.run_git("diff", "--cached").stdout)
        self.assertIn("staged diff", (self.repo / "prompt.log").read_text())

    def test_configured_python_checks_use_uv_without_sync(self) -> None:
        self.write("pyproject.toml", "[tool.ruff]\n[tool.pyright]\n")
        self.write("module.py", "value = 1\n")
        self.run_git("add", "pyproject.toml", "module.py")
        self.make_command("uv", 'printf "%s\\n" "$*" >>"$CHECK_LOG"')

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        calls = (self.repo / "check.log").read_text()
        self.assertIn("run --locked --no-sync ruff check --no-fix -- module.py", calls)
        self.assertIn("run --locked --no-sync ruff format --check -- module.py", calls)
        self.assertIn("run --locked --no-sync pyright", calls)

    def test_missing_configured_python_runner_fails_before_model(self) -> None:
        self.write("pyproject.toml", "[tool.ruff]\n")
        self.write("module.py", "value = 1\n")
        self.run_git("add", "pyproject.toml", "module.py")
        restricted_path = f"{self.bin_dir}:/usr/bin:/bin"

        result = self.run_commit(path=restricted_path)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("uv", result.stdout + result.stderr)
        self.assertFalse((self.repo / "model.log").exists())

    def test_python_deletion_runs_configured_whole_project_pyright(self) -> None:
        self.write("pyproject.toml", "[tool.pyright]\n")
        self.write("old.py", "value = 1\n")
        self.run_git("add", "pyproject.toml", "old.py")
        self.run_git("commit", "-qm", "add python")
        self.run_git("rm", "old.py")
        self.make_command("uv", 'printf "%s\\n" "$*" >>"$CHECK_LOG"')

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(
            "run --locked --no-sync pyright\n",
            (self.repo / "check.log").read_text(),
        )

    def test_shell_syntax_failure_does_not_call_shellcheck_or_model(self) -> None:
        self.write("broken.sh", "#!/usr/bin/env bash\nif true; then\n")
        self.run_git("add", "broken.sh")
        self.make_command("shellcheck", 'printf "shellcheck\\n" >>"$CHECK_LOG"')

        result = self.run_commit()

        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.repo / "check.log").exists())
        self.assertFalse((self.repo / "model.log").exists())

    def test_missing_shellcheck_fails_before_model(self) -> None:
        self.write("valid.sh", "#!/bin/sh\nprintf '%s\\n' ok\n")
        self.run_git("add", "valid.sh")

        result = self.run_commit(path=f"{self.bin_dir}:/usr/bin:/bin")

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
            "zsh -n ./nested/.zprofile\nzsh -n ./nested/.zshrc\n",
            (self.repo / "check.log").read_text(),
        )

    def test_staged_pyproject_is_not_sent_to_prettier(self) -> None:
        self.write(".prettierrc.json", "{}\n")
        self.run_git("add", ".prettierrc.json")
        self.run_git("commit", "-qm", "configure prettier")
        self.write("pyproject.toml", "[tool.pyright]\n")
        self.run_git("add", "pyproject.toml")
        self.make_command("uv", 'printf "%s\\n" "$*" >>"$CHECK_LOG"')
        self.make_command("prettier", 'case "$*" in *toml*) exit 23;; esac')

        result = self.run_commit()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(
            "run --locked --no-sync pyright\n",
            (self.repo / "check.log").read_text(),
        )
        self.assertEqual("pyproject.toml\n", (self.repo / "model.log").read_text())

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
            "git commit -qm 'test commit'",
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
