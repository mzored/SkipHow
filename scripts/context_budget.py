#!/usr/bin/env python3
"""Measure SkipHow runtime context and enforce its committed route limits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "plugins/skiphow/skills/skiphow"
BASELINE = ROOT / "scripts/context_budget_baseline.json"
SOURCE_MANIFEST = SKILL_ROOT / "references/third_party/sources.json"

ROUTE_ROOTS: dict[str, tuple[str, ...]] = {
    "router": ("SKILL.md",),
    "common": ("SKILL.md",),
    "clear": ("SKILL.md",),
    "repair": ("SKILL.md",),
    "diagnosis": ("SKILL.md",),
    "testing": ("SKILL.md",),
    "technical_review": ("SKILL.md",),
    "codebase_design": ("SKILL.md",),
}

REFERENCE_ACTIVATIONS: dict[tuple[str, str], tuple[str, ...]] = {
    ("SKILL.md", "references/product/idea/SKILL.md"): (),
    ("SKILL.md", "references/product/shape/SKILL.md"): (),
    ("SKILL.md", "references/engineering/fix/SKILL.md"): ("repair", "diagnosis"),
    ("SKILL.md", "references/trackers/setup/SKILL.md"): (),
    ("SKILL.md", "references/trackers/doctor/SKILL.md"): (),
    ("SKILL.md", "references/project-context.md"): (),
    ("SKILL.md", "references/extension-contract.md"): (),
    ("SKILL.md", "references/engineering/cto/SKILL.md"): (
        "common",
        "clear",
        "testing",
        "technical_review",
        "codebase_design",
    ),
    (
        "references/engineering/cto/SKILL.md",
        "references/engineering/cto/references/technical-policy.md",
    ): (
        "common",
        "clear",
        "repair",
        "diagnosis",
        "testing",
        "technical_review",
        "codebase_design",
    ),
    ("references/engineering/cto/SKILL.md", "references/host-capabilities.md"): (),
    (
        "references/engineering/cto/SKILL.md",
        "references/capabilities/prototype/SKILL.md",
    ): (),
    (
        "references/engineering/cto/SKILL.md",
        "references/engineering/diagnose/SKILL.md",
    ): ("diagnosis",),
    (
        "references/engineering/cto/SKILL.md",
        "references/campaign/cto-run/SKILL.md",
    ): (),
    (
        "references/engineering/cto/SKILL.md",
        "references/capabilities/testing/SKILL.md",
    ): ("testing",),
    (
        "references/engineering/cto/SKILL.md",
        "references/capabilities/codebase-design/SKILL.md",
    ): ("codebase_design",),
    (
        "references/engineering/cto/SKILL.md",
        "references/capabilities/technical-review/SKILL.md",
    ): ("technical_review",),
    (
        "references/engineering/cto/SKILL.md",
        "references/capabilities/resolving-merge-conflicts/SKILL.md",
    ): (),
    (
        "references/engineering/cto/SKILL.md",
        "references/trackers/github-task/SKILL.md",
    ): (),
    (
        "references/engineering/cto/SKILL.md",
        "references/product/shape/references/product-acceptance.md",
    ): (),
    (
        "references/engineering/fix/SKILL.md",
        "references/engineering/cto/SKILL.md",
    ): ("repair", "diagnosis"),
    (
        "references/engineering/fix/SKILL.md",
        "references/product/shape/SKILL.md",
    ): (),
    (
        "references/engineering/fix/SKILL.md",
        "references/engineering/diagnose/SKILL.md",
    ): ("diagnosis",),
    (
        "references/engineering/fix/SKILL.md",
        "references/trackers/github-task/SKILL.md",
    ): (),
}

ROUTE_EDGES: dict[str, tuple[tuple[str, str], ...]] = {
    route: tuple(
        edge for edge, activations in REFERENCE_ACTIVATIONS.items() if route in activations
    )
    for route in ROUTE_ROOTS
}

V06_REFERENCE = {
    "router": {"bytes": 4454, "words": 619},
    "common": {"bytes": 18310, "words": 2442},
    "clear": {"bytes": 19472, "words": 2602},
    "repair": {"bytes": 22065, "words": 2991},
    "diagnosis": {"bytes": 32402, "words": 4654},
    "testing": {"bytes": 27094, "words": 3724},
    "technical_review": {"bytes": 27168, "words": 3820},
    "codebase_design": {"bytes": 28931, "words": 3896},
}

TARGETS = {
    "router": {"bytes": 4454, "words": 619},
    "common": {"bytes": 14648, "words": 1953},
    "clear": {"bytes": 15577, "words": 2081},
    "repair": {"bytes": 17652, "words": 2392},
    "diagnosis": {"bytes": 22681, "words": 3257},
    "testing": {"bytes": 18965, "words": 2606},
    "technical_review": {"bytes": 19017, "words": 2674},
    "codebase_design": {"bytes": 20251, "words": 2727},
}

UPSTREAM_REFERENCE = re.compile(r"\bupstream/", re.IGNORECASE)
ACTION_WORD = re.compile(
    r"\b(?:read|load|open|consult|follow|use|see|apply|refer(?:ence)?|rely)\b",
    re.IGNORECASE,
)
MARKDOWN_PATH = re.compile(r"`([^`]+\.md)`", re.IGNORECASE)


def metrics(text: str) -> dict[str, int]:
    """Return stable byte and whitespace-delimited word counts."""
    return {"bytes": len(text.encode("utf-8")), "words": len(text.split())}


def extract_runtime_references(relative: str) -> list[dict[str, str | int]]:
    """Find actionable local Markdown reads in one runtime instruction file."""
    source = SKILL_ROOT / relative
    records: list[dict[str, str | int]] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        action = ACTION_WORD.search(line)
        if not action:
            continue
        for target_match in MARKDOWN_PATH.finditer(line):
            raw_target = target_match.group(1)
            candidate = (source.parent / raw_target).resolve()
            try:
                target = candidate.relative_to(SKILL_ROOT.resolve()).as_posix()
            except ValueError:
                continue
            if not candidate.is_file():
                continue
            records.append(
                {
                    "source": relative,
                    "target": target,
                    "line": line_number,
                    "action": action.group(0).lower(),
                }
            )
    return records


def derive_route_files(route: str) -> tuple[str, ...]:
    """Derive one ordered closure from its roots and validated runtime edges."""
    ordered = list(ROUTE_ROOTS[route])
    seen = set(ordered)
    changed = True
    while changed:
        changed = False
        for source, target in ROUTE_EDGES[route]:
            if source in seen and target not in seen:
                ordered.append(target)
                seen.add(target)
                changed = True
    return tuple(ordered)


ROUTES: dict[str, tuple[str, ...]] = {
    route: derive_route_files(route) for route in ROUTE_ROOTS
}


def measured_runtime_references() -> list[dict[str, str | int]]:
    sources = sorted({item for paths in ROUTES.values() for item in paths})
    return [record for source in sources for record in extract_runtime_references(source)]


def normalized_references(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    pairs = {(str(item["source"]), str(item["target"])) for item in records}
    return [{"source": source, "target": target} for source, target in sorted(pairs)]


def reference_digest(records: list[dict[str, Any]]) -> str:
    payload = json.dumps(normalized_references(records), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_source_manifest() -> list[str]:
    errors: list[str] = []
    data = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 2:
        errors.append("source manifest must use schema_version 2")
    declared_roots: set[Path] = set()
    for source in data.get("sources", []):
        capability = str(source.get("skiphow_capability", "<unknown>"))
        root = (SKILL_ROOT / str(source.get("vendored_at", ""))).resolve()
        declared_roots.add(root)
        adaptation = (SKILL_ROOT / str(source.get("adaptation_path", ""))).resolve()
        if not adaptation.is_file() or adaptation.is_relative_to(root):
            errors.append(f"{capability} adaptation_path must be a runtime file outside upstream")
        if source.get("provenance") != "exact_pinned_copy":
            errors.append(f"{capability} provenance must identify exact pinned copies")
        notice = source.get("notice_path")
        notice_path = root / str(notice) if notice else None
        if notice_path and not notice_path.is_file():
            errors.append(f"{capability} notice_path does not exist: {notice}")
        declared_files: set[Path] = set()
        for item in source.get("files", []):
            local_path = root / str(item.get("local_path", ""))
            declared_files.add(local_path.resolve())
            if not item.get("source_path"):
                errors.append(f"{capability} has a vendored file without source_path")
            if not local_path.is_file():
                errors.append(f"{capability} missing vendored file: {item.get('local_path')}")
                continue
            actual_hash = hashlib.sha256(local_path.read_bytes()).hexdigest()
            if actual_hash != item.get("sha256"):
                errors.append(
                    f"{capability} hash mismatch for {item.get('local_path')}: "
                    f"{actual_hash} != {item.get('sha256')}"
                )
        actual_files = {
            path.resolve()
            for path in root.rglob("*")
            if path.is_file() and (notice_path is None or path.resolve() != notice_path.resolve())
        }
        undeclared = sorted(path.relative_to(root).as_posix() for path in actual_files - declared_files)
        missing = sorted(path.relative_to(root).as_posix() for path in declared_files - actual_files)
        if undeclared:
            errors.append(f"{capability} has undeclared vendored files: {', '.join(undeclared)}")
        if missing:
            errors.append(f"{capability} declares absent vendored files: {', '.join(missing)}")
    actual_roots = {path.resolve() for path in SKILL_ROOT.rglob("upstream") if path.is_dir()}
    if declared_roots != actual_roots:
        missing = sorted(path.relative_to(SKILL_ROOT).as_posix() for path in actual_roots - declared_roots)
        extra = sorted(path.relative_to(SKILL_ROOT).as_posix() for path in declared_roots - actual_roots)
        if missing:
            errors.append(f"source manifest misses upstream directories: {', '.join(missing)}")
        if extra:
            errors.append(f"source manifest declares absent upstream directories: {', '.join(extra)}")
    return errors


def source_only_roots() -> set[Path]:
    data = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    roots: set[Path] = {SOURCE_MANIFEST.parent.resolve()}
    for source in data["sources"]:
        roots.add((SKILL_ROOT / source["vendored_at"]).resolve())
    return roots


def is_source_only(path: Path, roots: set[Path]) -> bool:
    resolved = path.resolve()
    return any(resolved == root or resolved.is_relative_to(root) for root in roots)


def collect_report() -> tuple[dict[str, Any], list[str]]:
    roots = source_only_roots()
    files: dict[str, dict[str, int | str]] = {}
    lint_errors = validate_source_manifest()
    for path in sorted(SKILL_ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(SKILL_ROOT).as_posix()
        kind = "source_only" if is_source_only(path, roots) else "runtime"
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        files[relative] = {**metrics(text), "kind": kind}
        if kind == "runtime" and path.suffix == ".md":
            for match in UPSTREAM_REFERENCE.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                lint_errors.append(
                    f"runtime Markdown references source-only upstream: {relative}:{line}"
                )

    discovered_references = measured_runtime_references()
    discovered_pairs = {
        (str(item["source"]), str(item["target"])) for item in discovered_references
    }
    classified_pairs = set(REFERENCE_ACTIVATIONS)
    unclassified = sorted(discovered_pairs - classified_pairs)
    stale_classifications = sorted(classified_pairs - discovered_pairs)
    if unclassified:
        detail = ", ".join(f"{source} -> {target}" for source, target in unclassified)
        lint_errors.append(f"unclassified actionable runtime references: {detail}")
    if stale_classifications:
        detail = ", ".join(
            f"{source} -> {target}" for source, target in stale_classifications
        )
        lint_errors.append(f"stale runtime reference classifications: {detail}")
    route_report: dict[str, dict[str, Any]] = {}
    for route, relative_paths in ROUTES.items():
        edges = ROUTE_EDGES.get(route, ())
        edge_members = {item for edge in edges for item in edge}
        undeclared = sorted(edge_members.difference(relative_paths))
        if undeclared:
            lint_errors.append(
                f"route {route} has runtime edges outside its closure: {', '.join(undeclared)}"
            )
        stale_edges = sorted(edge for edge in edges if edge not in discovered_pairs)
        if stale_edges:
            detail = ", ".join(f"{source} -> {target}" for source, target in stale_edges)
            lint_errors.append(f"route {route} has no matching runtime directive: {detail}")
        missing = [item for item in relative_paths if not (SKILL_ROOT / item).is_file()]
        if missing:
            lint_errors.append(f"route {route} has missing runtime files: {', '.join(missing)}")
            continue
        source_members = [item for item in relative_paths if is_source_only(SKILL_ROOT / item, roots)]
        if source_members:
            lint_errors.append(
                f"route {route} includes source-only files: {', '.join(source_members)}"
            )
        closure = "\n".join(
            (SKILL_ROOT / item).read_text(encoding="utf-8") for item in relative_paths
        )
        route_report[route] = {"files": list(relative_paths), **metrics(closure)}

    return {
        "schema_version": 1,
        "files": files,
        "routes": route_report,
        "runtime_references": {
            "discovered": discovered_references,
            "route_edges": {
                route: [{"from": source, "to": target} for source, target in edges]
                for route, edges in ROUTE_EDGES.items()
            },
        },
        "source_manifest": SOURCE_MANIFEST.relative_to(ROOT).as_posix(),
    }, lint_errors


def load_baseline(path: Path | None = None) -> dict[str, Any]:
    target = BASELINE if path is None else path
    return json.loads(target.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def baseline_from_git(base: str) -> dict[str, Any] | None:
    relative = BASELINE.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "show", f"{base}:{relative}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def route_counts(report: dict[str, Any]) -> dict[str, dict[str, int]]:
    return {
        route: {"bytes": values["bytes"], "words": values["words"]}
        for route, values in report["routes"].items()
    }


def report_references(report: dict[str, Any]) -> list[dict[str, str]]:
    return normalized_references(report["runtime_references"]["discovered"])


def target_errors(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for route, counts in route_counts(report).items():
        for unit in ("bytes", "words"):
            if counts[unit] > TARGETS[route][unit]:
                errors.append(
                    f"{route} {unit} exceeds v0.7 target: "
                    f"{counts[unit]} > {TARGETS[route][unit]}"
                )
    return errors


def check_report(report: dict[str, Any], baseline: dict[str, Any], base: str | None) -> list[str]:
    errors = target_errors(report)
    current = route_counts(report)
    recorded = baseline.get("routes", {})
    for route, counts in current.items():
        for unit in ("bytes", "words"):
            previous = recorded.get(route, {}).get(unit)
            if previous is None:
                errors.append(f"baseline has no {route} {unit} value")
            elif counts[unit] > previous:
                errors.append(
                    f"{route} {unit} increased: {counts[unit]} > {previous}; "
                    "run --update --accept-increase --reason '...'"
                )

    current_references = report_references(report)
    recorded_references = baseline.get("runtime_references", [])
    added_references = [item for item in current_references if item not in recorded_references]
    if added_references:
        detail = ", ".join(
            f"{item['source']} -> {item['target']}" for item in added_references
        )
        errors.append(
            "new actionable runtime references require classification in route edges and "
            f"an explained baseline update: {detail}"
        )

    if baseline.get("schema_version") != 2:
        errors.append("context budget baseline must use schema_version 2")
    if baseline.get("v0_6_reference") != V06_REFERENCE:
        errors.append("baseline v0.6 reference changed")
    if baseline.get("targets") != TARGETS:
        errors.append("baseline v0.7 targets changed")

    if base:
        old = baseline_from_git(base)
        if old:
            old_explanations = old.get("increase_explanations", [])
            explanations = baseline.get("increase_explanations", [])
            new_explanations = [item for item in explanations if item not in old_explanations]
            for route, counts in recorded.items():
                old_counts = old.get("routes", {}).get(route, {})
                for unit in ("bytes", "words"):
                    before = old_counts.get(unit)
                    after = counts.get(unit)
                    if before is None or after is None or after <= before:
                        continue
                    if not any(
                        item.get("route") == route
                        and item.get("unit") == unit
                        and item.get("from") == before
                        and item.get("to") == after
                        and str(item.get("reason", "")).strip()
                        for item in new_explanations
                    ):
                        errors.append(
                            f"baseline raises {route} {unit} without a new matching explanation"
                        )
            old_references = old.get("runtime_references", [])
            new_references = baseline.get("runtime_references", [])
            added = [item for item in new_references if item not in old_references]
            if added:
                before = reference_digest(old_references)
                after = reference_digest(new_references)
                if not any(
                    item.get("route") == "runtime_references"
                    and item.get("unit") == "entries"
                    and item.get("from") == before
                    and item.get("to") == after
                    and str(item.get("reason", "")).strip()
                    for item in new_explanations
                ):
                    errors.append(
                        "baseline adds runtime references without a new matching explanation"
                    )
    return errors


def update_baseline(
    report: dict[str, Any], *, accept_increase: bool, reason: str | None
) -> list[str]:
    previous = load_baseline() if BASELINE.exists() else {"routes": {}, "increase_explanations": []}
    current = route_counts(report)
    current_references = report_references(report)
    explanations = list(previous.get("increase_explanations", []))
    errors: list[str] = []
    for route, counts in current.items():
        old_counts = previous.get("routes", {}).get(route, {})
        for unit in ("bytes", "words"):
            before = old_counts.get(unit)
            after = counts[unit]
            if before is not None and after < before:
                for item in explanations:
                    if (
                        item.get("route") == route
                        and item.get("unit") == unit
                        and item.get("to") == before
                        and isinstance(item.get("from"), int)
                        and after > item["from"]
                    ):
                        item["to"] = after
            if before is not None and after > before:
                if not accept_increase or not reason or not reason.strip():
                    errors.append(
                        f"refusing to raise {route} {unit} from {before} to {after} without "
                        "--accept-increase and --reason"
                    )
                else:
                    explanations.append(
                        {"route": route, "unit": unit, "from": before, "to": after, "reason": reason.strip()}
                    )
    old_references = previous.get("runtime_references", [])
    added_references = [item for item in current_references if item not in old_references]
    removed_references = [item for item in old_references if item not in current_references]
    if removed_references and not added_references:
        old_digest = reference_digest(old_references)
        current_digest = reference_digest(current_references)
        for item in explanations:
            if (
                item.get("route") == "runtime_references"
                and item.get("unit") == "entries"
                and item.get("to") == old_digest
            ):
                item["to"] = current_digest
    if added_references:
        if not accept_increase or not reason or not reason.strip():
            errors.append(
                "refusing to add actionable runtime references without "
                "--accept-increase and --reason"
            )
        else:
            explanations.append(
                {
                    "route": "runtime_references",
                    "unit": "entries",
                    "from": reference_digest(old_references),
                    "to": reference_digest(current_references),
                    "reason": reason.strip(),
                }
            )
    if errors:
        return errors
    payload = {
        "schema_version": 2,
        "v0_6_reference": V06_REFERENCE,
        "targets": TARGETS,
        "routes": current,
        "runtime_references": current_references,
        "increase_explanations": explanations,
    }
    BASELINE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="compare with committed limits")
    action.add_argument("--update", action="store_true", help="write lower measured limits")
    parser.add_argument("--base", help="base revision used to audit limit increases")
    parser.add_argument("--accept-increase", action="store_true")
    parser.add_argument("--reason")
    parser.add_argument("--json", action="store_true", help="print the full measurement report")
    args = parser.parse_args(argv)

    report, errors = collect_report()
    if args.update:
        errors.extend(target_errors(report))
        if not errors:
            errors.extend(
                update_baseline(
                    report, accept_increase=args.accept_increase, reason=args.reason
                )
            )
    elif args.check:
        if not BASELINE.exists():
            errors.append(f"missing baseline: {display_path(BASELINE)}")
        else:
            errors.extend(check_report(report, load_baseline(), args.base))
            if not errors:
                baseline = load_baseline()
                if (
                    baseline.get("routes") != route_counts(report)
                    or baseline.get("runtime_references") != report_references(report)
                ):
                    errors.extend(
                        update_baseline(
                            report, accept_increase=False, reason=None
                        )
                    )
                    if not errors:
                        print(f"lowered {display_path(BASELINE)}")

    if args.json or not (args.check or args.update):
        print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        for error in errors:
            print(f"context budget: {error}", file=sys.stderr)
        return 1
    if args.update:
        print(f"updated {display_path(BASELINE)}")
    elif args.check:
        print("context budget passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
