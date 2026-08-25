"""Command line interface for deterministic scenario grading."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .outcome import GradeReport, ManifestError, grade_files


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evals.graders",
        description="Grade a SkipHow scenario receipt without model or network calls.",
    )
    parser.add_argument("manifest", type=Path, help="scenario manifest JSON")
    parser.add_argument("receipt", type=Path, help="scenario result receipt JSON")
    parser.add_argument("--output", type=Path, help="write the JSON report to this path")
    parser.add_argument("--compact", action="store_true", help="write JSON on one line")
    return parser


def _invalid(message: str) -> GradeReport:
    return GradeReport("UNKNOWN", "INVALID", (), (message,))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = grade_files(args.manifest, args.receipt)
    except ManifestError as exc:
        report = _invalid(str(exc))
    payload = json.dumps(
        report.as_dict(),
        ensure_ascii=False,
        indent=None if args.compact else 2,
        sort_keys=True,
    ) + "\n"
    if args.output:
        try:
            args.output.write_text(payload, encoding="utf-8")
        except OSError as exc:
            print(f"cannot write {args.output}: {exc}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(payload)
    if report.verdict == "PASS":
        return 0
    if report.verdict == "FAIL":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
