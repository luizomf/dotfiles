#!/usr/bin/env python3.14
"""Merge the zsh history of every known host into the local history file.

Hosts that are offline are skipped, never fatal: their entries simply arrive on
a later run. The local history is always part of the merge, so the result is a
superset of what is already on disk.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

HOME = Path.home()
CURR_ZSH_HISTORY = HOME / ".zsh_history"
BKP_ZSH_HISTORY_DIR = HOME / ".zsh_history_bkp"
KEEP_BACKUPS = 10

REMOTE_HOSTS = ("m4128", "m132", "fedoraair")
REMOTE_HISTORY_PATH = "~/.zsh_history"
SSH_CONNECT_TIMEOUT = 10
SSH_READ_TIMEOUT = 120

ENTRY_START = b": "
META_SPLITTER = b":"
CMD_SPLITTER = b";"
CONTINUATION = b"\\"
NEWLINE = b"\n"


@dataclass(slots=True, frozen=True, kw_only=True)
class ZshHistoryEntry:
    timestamp: int
    duration: bytes
    command: bytes
    raw: bytes = field(compare=False)


def split_entries(raw_bytes: bytes) -> Iterator[bytes]:
    """Yield one raw record per history entry.

    zsh writes an embedded newline as a backslash glued to that newline, and
    protects a literal trailing backslash by appending a space. So a line
    ending in a backslash is always the continuation of the current entry,
    even when the next line starts like a new one.
    """
    current = b""
    continuing = False

    for line in raw_bytes.splitlines(keepends=True):
        if not continuing and line.startswith(ENTRY_START):
            if current:
                yield current
            current = line
        else:
            current += line

        continuing = line.rstrip(b"\r\n").endswith(CONTINUATION)

    if current:
        yield current


def parse_entry(raw_entry: bytes) -> ZshHistoryEntry | None:
    """Parse a raw record, or return None when it is not a history entry.

    Anything an ssh session may prepend to the stream (banners, MOTD, warnings)
    lands here as garbage and is dropped instead of aborting the whole sync.
    """
    if not raw_entry.startswith(ENTRY_START):
        return None

    meta, found_cmd, command = raw_entry[len(ENTRY_START) :].partition(CMD_SPLITTER)
    if not found_cmd:
        return None

    timestamp, found_meta, duration = meta.partition(META_SPLITTER)
    if not found_meta or not timestamp.strip().isdigit():
        return None

    return ZshHistoryEntry(
        timestamp=int(timestamp),
        duration=duration.strip(),
        command=command.rstrip(b"\r\n"),
        raw=raw_entry if raw_entry.endswith(NEWLINE) else raw_entry + NEWLINE,
    )


def history_to_entries(raw_bytes: bytes) -> set[ZshHistoryEntry]:
    entries: set[ZshHistoryEntry] = set()

    for raw_entry in split_entries(raw_bytes):
        entry = parse_entry(raw_entry)
        if entry is not None:
            entries.add(entry)

    return entries


def sort_entries(entries: set[ZshHistoryEntry]) -> Sequence[ZshHistoryEntry]:
    """Sort chronologically, breaking ties so the output is reproducible."""
    return sorted(entries, key=lambda e: (e.timestamp, e.command, e.duration))


def read_remote_history(host: str) -> bytes | None:
    """Return the host's raw history, or None when it cannot be read."""
    try:
        out = subprocess.run(
            [
                "ssh",
                "-n",
                "-T",
                "-o",
                "BatchMode=yes",
                "-o",
                f"ConnectTimeout={SSH_CONNECT_TIMEOUT}",
                host,
                f"cat {REMOTE_HISTORY_PATH}",
            ],
            check=False,
            capture_output=True,
            timeout=SSH_READ_TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError) as err:
        print(f"  {host}: skipped ({type(err).__name__})")
        return None

    if out.returncode != 0:
        stderr_lines = out.stderr.decode(errors="replace").strip().splitlines()
        reason = stderr_lines[-1] if stderr_lines else f"exit {out.returncode}"
        print(f"  {host}: skipped ({reason})")
        return None

    return out.stdout


def collect_entries(local_entries: set[ZshHistoryEntry]) -> set[ZshHistoryEntry]:
    all_entries = set(local_entries)

    for host in REMOTE_HOSTS:
        raw_bytes = read_remote_history(host)
        if raw_bytes is None:
            continue

        host_entries = history_to_entries(raw_bytes)
        new_entries = host_entries - all_entries
        all_entries |= host_entries
        print(f"  {host}: {len(host_entries)} entries, {len(new_entries)} new")

    return all_entries


def backup_history(curr_history_path: Path) -> Path:
    BKP_ZSH_HISTORY_DIR.mkdir(exist_ok=True)

    # Two syncs within the same second must not overwrite each other's backup.
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = BKP_ZSH_HISTORY_DIR / f"zsh_history-{stamp}"
    collision = 0
    while backup_path.exists():
        collision += 1
        backup_path = BKP_ZSH_HISTORY_DIR / f"zsh_history-{stamp}-{collision:02d}"

    shutil.copy2(curr_history_path, backup_path)
    prune_backups()

    return backup_path


def prune_backups() -> None:
    backups = sorted(
        p for p in BKP_ZSH_HISTORY_DIR.glob("zsh_history-*") if p.is_file()
    )

    for old_backup in backups[:-KEEP_BACKUPS]:
        old_backup.unlink()


def write_history(curr_history_path: Path, entries: Sequence[ZshHistoryEntry]) -> None:
    """Write every entry through a temporary file, then swap it in atomically."""
    mode = curr_history_path.stat().st_mode & 0o777
    fd, tmp_name = tempfile.mkstemp(
        dir=curr_history_path.parent,
        prefix=f".{curr_history_path.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_name)

    try:
        with os.fdopen(fd, "wb") as tmp_file:
            for entry in entries:
                tmp_file.write(entry.raw)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())

        tmp_path.chmod(mode)
        os.replace(tmp_path, curr_history_path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def merge_and_overwrite_histories(
    curr_history_path: Path, *, dry_run: bool = False
) -> int:
    if not curr_history_path.is_file():
        print(f"ABORT: {curr_history_path} does not exist")
        return 1

    local_entries = history_to_entries(curr_history_path.read_bytes())
    print(f"  local: {len(local_entries)} entries")

    all_entries = collect_entries(local_entries)

    if len(all_entries) < len(local_entries):
        # The merge is a superset of the local history by construction, so this
        # only trips when something went wrong. Never overwrite in that case.
        print("ABORT: merged history is smaller than the local one, nothing written")
        return 1

    if all_entries == local_entries:
        print("Nothing new, local history left untouched")
        return 0

    if dry_run:
        print(f"[dry-run] would write {len(all_entries)} entries")
        return 0

    backup_path = backup_history(curr_history_path)
    write_history(curr_history_path, sort_entries(all_entries))
    print(f"Backup: {backup_path}")
    print(f"Merged: {len(all_entries)} entries (+{len(all_entries - local_entries)})")

    return 0


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv[1:]

    print()
    print("ZSH History Sync starting...")

    exit_code = merge_and_overwrite_histories(CURR_ZSH_HISTORY, dry_run=dry_run)

    print("Sync done!" if exit_code == 0 else "Sync failed!")
    print()

    sys.exit(exit_code)
