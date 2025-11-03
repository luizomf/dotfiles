#!/usr/bin/env python3.14

# ruff: noqa: S607,S602
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


ROOT_DIR = Path(__file__).parent.parent
curr_history_filename = ".zsh_history"

HOME = Path.home()
BKP_ZSH_HISTORY_DIR = HOME / ".zsh_history_bkp"
CURR_ZSH_HISTORY = HOME / curr_history_filename


@dataclass(slots=True, frozen=True, kw_only=True)
class ZshHistoryEntry:
    timestamp: bytes
    duration: bytes
    command: bytes
    raw: bytes


def history_to_entries(raw_bytes: bytes) -> set[ZshHistoryEntry]:
    entries: set[ZshHistoryEntry] = set()
    line_start = b": "

    history_entry = b""
    for line in raw_bytes.splitlines(keepends=True):
        if line.startswith(line_start):
            if history_entry:
                entry = parse_entry(history_entry)
                entries.add(entry)

            history_entry = line
        else:
            history_entry += line

    if history_entry:
        entry = parse_entry(history_entry)
        entries.add(entry)

    return entries


def parse_entry(entry: bytes) -> ZshHistoryEntry:
    line_start = b": "
    cmd_splitter = b";"
    meta_splitter = b":"
    empty_byte = b""

    meta: bytes | None = None
    command: bytes | None = None

    meta, command = (
        entry.strip().replace(line_start, empty_byte, 1).split(cmd_splitter, 1)
    )
    timestamp, duration = meta.split(meta_splitter)

    return ZshHistoryEntry(
        timestamp=timestamp, duration=duration, command=command, raw=entry
    )


def merge_history(
    curr_history_path: Path, merge_history_bytes: bytes
) -> Sequence[ZshHistoryEntry]:
    curr_history_entries = history_to_entries(curr_history_path.read_bytes())
    merge_history_entries = history_to_entries(merge_history_bytes)
    all_entries = curr_history_entries.union(merge_history_entries)

    return sorted(all_entries, key=lambda e: int(e.timestamp))


def merge_and_overwrite_histories(
    curr_history_path: Path,
) -> None:
    BKP_ZSH_HISTORY_DIR.mkdir(exist_ok=True)

    zsh_source_cmds = f"""
    fc -W
    source {Path.home() / ".zshrc"}
    fc -W
    """
    ssh_cp_zsh_history_cmd = """
    ssh maclo 'cat .zsh_history'
    """
    subprocess.run(["fc", "-W"], check=False, shell=True)
    subprocess.run(
        ["-l", "-c", zsh_source_cmds],
        executable="/bin/zsh",
        check=False,
        shell=True,
        capture_output=True,
    )
    out = subprocess.run(
        ["-l", "-c", ssh_cp_zsh_history_cmd],
        executable="/bin/zsh",
        check=False,
        shell=True,
        capture_output=True,
    )
    merge_history_bytes = out.stdout

    merged_history_entries = merge_history(curr_history_path, merge_history_bytes)
    curr_history_path.copy(BKP_ZSH_HISTORY_DIR / f".zsh_history_BKP_{int(time.time())}")

    with CURR_ZSH_HISTORY.open("wb") as curr_file_obj:
        for entry in merged_history_entries:
            curr_file_obj.write(entry.raw)

    subprocess.run(["fc", "-W"], check=False, shell=True)
    subprocess.run(
        ["-l", "-c", zsh_source_cmds],
        executable="/bin/zsh",
        check=False,
        shell=True,
        capture_output=True,
    )


if __name__ == "__main__":
    print()
    print("ZSH History Sync starting...")
    print("Python version:", sys.version)

    merge_and_overwrite_histories(CURR_ZSH_HISTORY)

    print()
    print("ZSH History Sync...")
    print("Sync done!")
    print()
