#!/usr/bin/env python3
"""Stage a portable resurrect save without changing the live snapshot."""

import os
from pathlib import Path
import shutil
import sys


def prepare(source: Path, destination: Path, home: str) -> None:
    source = source.resolve(strict=True)
    snapshot = (source / "last").resolve(strict=True)
    if snapshot.parent != source or not snapshot.is_file():
        raise ValueError("last must reference a snapshot file inside the resurrect directory")

    prefix = b":" + os.fsencode(home.rstrip("/"))
    lines = []
    for line in snapshot.read_bytes().splitlines(keepends=True):
        fields = line.split(b"\t")
        if fields[0] == b"pane":
            if len(fields) < 11:
                raise ValueError("unsupported resurrect pane record")
            directory = fields[7]
            # Resurrect expands ~ in new_window, but not new_session/new_pane.
            # All three pass -c through tmux's format expansion instead.
            if directory == prefix or directory.startswith(prefix + b"/"):
                fields[7] = b":#{HOME}" + directory[len(prefix):]
            elif directory == b":~" or directory.startswith(b":~/"):
                # Also upgrade snapshots produced by the old staging helper.
                fields[7] = b":#{HOME}" + directory[2:]
        lines.append(b"\t".join(fields))

    # Keep pane contents and other metadata, but never follow copied symlinks
    # when replacing the snapshot or last in the disposable destination.
    shutil.copytree(source, destination, symlinks=True)
    name = snapshot.name if snapshot.name != "last" else "tmux_resurrect_synchosts.txt"
    staged_snapshot = destination / name
    staged_snapshot.unlink(missing_ok=True)
    staged_snapshot.write_bytes(b"".join(lines))
    staged_snapshot.chmod(snapshot.stat().st_mode & 0o777)
    last = destination / "last"
    last.unlink(missing_ok=True)
    last.symlink_to(name)


if __name__ == "__main__":
    try:
        if len(sys.argv) != 4:
            raise ValueError("usage: prepare_tmux_resurrect.py SOURCE DESTINATION HOME")
        prepare(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
    except (OSError, ValueError) as exc:
        print(f"Cannot stage resurrect snapshot: {exc}", file=sys.stderr)
        sys.exit(1)
