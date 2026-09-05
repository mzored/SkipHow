#!/usr/bin/env python3
"""Preview or manage an owned activation block in an explicit trusted file."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path
import re
import sys


ACTIVATION = (
    "For current-project requests, load the installed SkipHow skill before consequential "
    "action and use it as the adaptive virtual CTO policy. Do not load it for unrelated "
    "conversation or for a request that only discusses SkipHow without adopting it."
)
MARKER = b"<!-- skiphow activation"
END = b"<!-- /skiphow activation -->\n"
START = re.compile(rb"<!-- skiphow activation v1 separator=([01]) created=([01]) -->\n")


def locate(data: bytes) -> tuple[int, int, bool] | None:
    """Accept only the exact block we own; leave edits for human inspection."""
    if MARKER not in data and b"<!-- /skiphow activation" not in data:
        return None
    matches = list(START.finditer(data))
    if len(matches) != 1 or data.count(MARKER) != 1 or data.count(b"<!-- /skiphow activation") != 1:
        raise ValueError("Activation markers are edited, incomplete, or duplicated; inspect the file.")
    match = matches[0]
    body = ACTIVATION.encode("utf-8") + b"\n" + END
    end = match.end() + len(body)
    if data[match.end():end] != body:
        raise ValueError("The owned activation block was edited; inspect it before changing it.")
    start = match.start()
    if match.group(1) == b"1":
        if start == 0 or data[start - 1:start] != b"\n":
            raise ValueError("The owned activation separator was edited; inspect the file.")
        start -= 1
    return start, end, match.group(2) == b"1"


def transform(original: bytes | None, action: str) -> bytes | None:
    data = original if original is not None else b""
    data.decode("utf-8")
    block = locate(data)
    if action == "remove":
        if block is None:
            return original
        start, end, created = block
        remaining = data[:start] + data[end:]
        return None if created and not remaining else remaining
    if block is not None:
        return original
    separator = bool(data and not data.endswith(b"\n"))
    start = f"<!-- skiphow activation v1 separator={int(separator)} created={int(original is None)} -->\n"
    return data + (b"\n" if separator else b"") + start.encode() + ACTIVATION.encode() + b"\n" + END


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "status", "remove"))
    parser.add_argument("--target", type=Path, required=True, help="Explicit trusted user instruction file")
    parser.add_argument("--apply", action="store_true", help="Apply the displayed change; default is preview only")
    args = parser.parse_args(argv)
    if args.action == "status" and args.apply:
        parser.error("status is read-only")
    target = args.target.expanduser().absolute()
    try:
        if target.is_symlink() or any(parent.is_symlink() for parent in target.parents):
            raise ValueError("Use an ordinary target path without symbolic links.")
        if not target.parent.is_dir():
            raise ValueError("The target parent directory must already exist.")
        original = target.read_bytes() if target.exists() else None
        if args.action == "status":
            block = locate(original or b"")
            print(f"{target}: owned activation block {'present' if block else 'absent'}.")
            print("Installed package availability and runtime loading are UNVERIFIED by this check.")
            return 0
        changed = transform(original, args.action)
        if changed == original:
            print(f"{target}: no change.")
            return 0
        diff = difflib.unified_diff(
            (original or b"").decode().splitlines(keepends=True),
            (changed or b"").decode().splitlines(keepends=True),
            fromfile=str(target) if original is not None else "/dev/null",
            tofile=str(target) if changed is not None else "/dev/null",
        )
        for line in diff:
            sys.stdout.write(line)
            if not line.endswith("\n"):
                sys.stdout.write("\n\\ No newline at end of file\n")
        if args.apply:
            if (target.read_bytes() if target.exists() else None) != original:
                raise ValueError("The target changed since inspection; rerun the preview.")
            if changed is None:
                target.unlink()
            elif original is None:
                with target.open("xb") as destination:
                    destination.write(changed)
            else:
                target.write_bytes(changed)
            print("Applied.")
        else:
            print("Preview only. Add --apply to write this change.")
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
