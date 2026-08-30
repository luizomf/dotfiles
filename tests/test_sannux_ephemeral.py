import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SANNUX_EPHEMERAL = REPOSITORY / "scripts" / "sannux_ephemeral"


class SannuxEphemeralTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.home = self.root / "home"
        self.projects = self.root / "projects"
        self.sannux = self.projects / "sannux"
        self.pi_home = self.root / "agent-homes" / "pi"
        self.codex_home = self.root / "agent-homes" / "codex"
        self.workspace = self.root / "workspace"
        self.docker_log = self.root / "docker.jsonl"

        for path in (
            self.home,
            self.pi_home,
            self.codex_home,
            self.workspace,
            self.sannux / "templates" / "pi",
            self.sannux / "templates" / "codex",
        ):
            path.mkdir(parents=True)

        (self.sannux / "templates" / "pi" / ".env").write_text(
            f"AGENT_HOME_PATH={self.pi_home}\n", encoding="utf-8"
        )
        (self.sannux / "templates" / "codex" / ".env").write_text(
            f"AGENT_HOME_PATH={self.codex_home}\n", encoding="utf-8"
        )

        self.fake_bin = self.root / "bin"
        self.fake_bin.mkdir()
        fake_docker = self.fake_bin / "docker"
        fake_docker.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import sys

                with open(os.environ["DOCKER_LOG"], "a", encoding="utf-8") as handle:
                    handle.write(json.dumps(sys.argv[1:]) + "\\n")
                """
            ),
            encoding="utf-8",
        )
        fake_docker.chmod(0o755)

    def environment(self) -> dict[str, str]:
        return {
            **os.environ,
            "HOME": str(self.home),
            "PROJECTS_DIR": str(self.projects),
            "CURDIR": str(self.workspace),
            "DOCKER_LOG": str(self.docker_log),
            "PATH": f"{self.fake_bin}{os.pathsep}{os.environ['PATH']}",
        }

    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(SANNUX_EPHEMERAL), *arguments],
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            env=self.environment(),
            check=False,
        )

    def docker_invocations(self) -> list[list[str]]:
        if not self.docker_log.exists():
            return []
        return [
            json.loads(line)
            for line in self.docker_log.read_text(encoding="utf-8").splitlines()
        ]

    def test_pi_home_uses_a_private_namespace_and_cleans_only_its_run(self) -> None:
        ephemeral_root = Path(f"{self.pi_home}.ephemeral-runs")
        concurrent_home = ephemeral_root / "run.concurrent"
        concurrent_home.mkdir(parents=True)
        marker = concurrent_home / "still-running"
        marker.write_text("keep", encoding="utf-8")

        result = self.run_script("pi", "--list-models")

        self.assertEqual(result.returncode, 0, result.stderr)
        invocations = self.docker_invocations()
        self.assertEqual(len(invocations), 1)
        home_mounts = [
            argument
            for argument in invocations[0]
            if argument.endswith(":/home/agent")
        ]
        self.assertEqual(len(home_mounts), 1)
        run_home = Path(home_mounts[0].removesuffix(":/home/agent"))
        self.assertEqual(run_home.parent, ephemeral_root)
        self.assertRegex(run_home.name, re.compile(r"^run\.[A-Za-z0-9]{6}$"))
        self.assertFalse(run_home.exists())
        self.assertEqual(stat.S_IMODE(ephemeral_root.stat().st_mode), 0o700)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    @unittest.skipUnless(shutil.which("rsync"), "rsync is required")
    def test_refresh_resolves_links_and_excludes_all_host_node_modules(self) -> None:
        host_agent = self.home / ".pi" / "agent"
        extensions = host_agent / "extensions"
        skills = host_agent / "skills"
        locked = extensions / "locked"
        unlocked = extensions / "unlocked"
        skill = skills / "example"
        for path in (locked, unlocked, skill):
            path.mkdir(parents=True)

        (locked / "package.json").write_text("{}\n", encoding="utf-8")
        (locked / "package-lock.json").write_text("{}\n", encoding="utf-8")
        (unlocked / "package.json").write_text("{}\n", encoding="utf-8")
        (locked / "node_modules" / "native").mkdir(parents=True)
        (locked / "node_modules" / "native" / "host.node").write_text(
            "host", encoding="utf-8"
        )
        (skill / "SKILL.md").write_text("# Example\n", encoding="utf-8")
        (skill / "node_modules" / "dependency").mkdir(parents=True)
        (skill / "node_modules" / "dependency" / "package.json").write_text(
            "{}\n", encoding="utf-8"
        )
        (skills / ".omskills-managed-links").write_text(
            "managed\n", encoding="utf-8"
        )

        linked_source = self.root / "linked-extension.ts"
        linked_source.write_text("export const linked = true;\n", encoding="utf-8")
        (extensions / "linked.ts").symlink_to(linked_source)

        result = self.run_script("--refresh-pi-resources")

        self.assertEqual(result.returncode, 0, result.stderr)
        snapshot = self.pi_home / ".pi" / "agent"
        self.assertEqual(
            (snapshot / "extensions" / "linked.ts").read_text(encoding="utf-8"),
            linked_source.read_text(encoding="utf-8"),
        )
        self.assertFalse((snapshot / "extensions" / "linked.ts").is_symlink())
        self.assertTrue((snapshot / "skills" / "example" / "SKILL.md").is_file())
        self.assertFalse((snapshot / "skills" / ".omskills-managed-links").exists())
        self.assertEqual(list(snapshot.rglob("node_modules")), [])

        invocations = self.docker_invocations()
        self.assertEqual(len(invocations), 2)
        commands_by_package = {}
        for invocation in invocations:
            prefix_index = invocation.index("--prefix")
            package_path = invocation[prefix_index + 1]
            commands_by_package[Path(package_path).name] = invocation

        self.assertIn("ci", commands_by_package["locked"])
        self.assertIn("--omit=dev", commands_by_package["locked"])
        self.assertIn("install", commands_by_package["unlocked"])
        self.assertIn("--package-lock=false", commands_by_package["unlocked"])
        self.assertIn("--omit=dev", commands_by_package["unlocked"])


if __name__ == "__main__":
    unittest.main()
