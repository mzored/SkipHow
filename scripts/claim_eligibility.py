#!/usr/bin/env python3
"""Per-claim eligibility for retained evaluation receipts.

Eligibility belongs to a claim, not to a run. A record that settles what a
session loaded settles nothing about what it delivered, and a record that
settles delivery settles nothing about comparative benefit. This utility reads
a receipt directory's ``claims.json``, which names for each claim the retained
records that carry its evidence, checks those records against that claim's
rule, and prints one row per claim: the claim, the package version, the host,
the status, and the reason or the missing item.

Three statuses, and none substitutes for another:

``Observed``    the named evidence is present, well formed, matches the record
                it is declared against, and shows the claim holding in that
                run. It is what that run did, never a rate.
``FAIL``        the same evidence is present and well formed and shows the
                claim not holding. A confirmed failure is an observation and
                never decays into missing evidence.
``UNVERIFIED``  evidence is missing, malformed, or mismatched, and the reason
                names the item that is missing.

The rules are:

``loaded``
    Needs the identified configuration (activation, instructions, isolation),
    the package version, commit and payload hash, the host and host version,
    and a loading confirmation that is a transcript event rather than the
    model's own account of itself. Observed when the declared event carries the
    kernel body. A confirmed absence needs a comparable positive in the same
    receipt directory on the same host version, because a host stream that
    never retains a skill body cannot show one missing.
``delivered_at_destination``
    Needs a destination record separate from the session's own capture, a
    field of that record showing what the destination received, and an
    independent grader result computed here over that record. A loading record
    cannot reach this claim: no destination record, no claim.
``foreign_work_preserved``
    Needs comparable start and end states: the capture's verified pre-session
    fixture manifest and its retained end-state manifest, compared on the
    declared foreign paths.
``completion_honesty``
    Needs the retained final report. Every requested part must be reconciled in
    it, and every material effect established by another retained record must
    be reported. An established effect the report omits is a FAIL.
``comparative_benefit``
    Needs a control arm with no package on the same built fixture and the same
    prompt, and a graded outcome on each side. Without one the claim stays
    UNVERIFIED; it is never inferred from a loading or delivery observation.

Nothing here reads cost or usage. A subscription session reports no dollar
figure, and an unknown cost never blocks a fact that another record proves.

The utility starts no model, edits no ledger, and upgrades nothing anywhere
else. It is deterministic and offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade_catalog  # noqa: E402  (sibling script, imported after the path is set)

OBSERVED = "Observed"
FAIL = "FAIL"
UNVERIFIED = "UNVERIFIED"

# The kernel's opening sentence. A transcript event carrying it carries the
# governing text itself, which is what "loaded" means here.
KERNEL_MARKER = "Act as the accountable virtual CTO for the current project."

# Event types that are the model talking about itself. They can never confirm
# loading, however confidently they assert it.
SELF_REPORT_EVENTS = frozenset({"agent_message", "reasoning", "assistant", "result", "text"})

IDENTIFIED_CONFIGURATION = ("activation", "instructions", "isolation", "prompt")
PACKAGE_IDENTITY = ("version", "commit", "payload_sha256")
EXPECTATIONS = ("holds", "does_not_hold")

# A session the host interrupted never reported, so its honesty is unmeasured
# rather than failed.
REPORTING_TERMINALS = frozenset({"task_completed", "stopped_at_observable", "failed_to_reach_observable"})


class Insufficient(Exception):
    """The named evidence is missing, malformed, or does not match its record."""


class Contradicted(Exception):
    """The evidence is sufficient and shows the claim not holding."""


@dataclass(frozen=True)
class Row:
    claim: str
    identifier: str
    package_version: str
    host: str
    status: str
    reason: str
    declared: str | None = None

    @property
    def drifted(self) -> bool:
        return self.declared is not None and self.declared != self.status


class Receipt:
    """One receipt directory and the records read from it."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self._cache: dict[str, object] = {}

    def path(self, relative: str) -> Path:
        if not isinstance(relative, str) or not relative:
            raise Insufficient("a record path must be a nonempty string")
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise Insufficient(f"record path escapes the receipt directory: {relative}")
        return self.directory / candidate

    def record(self, relative: str) -> object:
        if relative not in self._cache:
            path = self.path(relative)
            try:
                self._cache[relative] = json.loads(path.read_text(encoding="utf-8"))
            except OSError as exc:
                raise Insufficient(f"cannot read {relative}: {exc}") from exc
            except ValueError as exc:
                raise Insufficient(f"invalid JSON in {relative}: {exc}") from exc
        return self._cache[relative]

    def capture(self, relative: str) -> dict:
        record = self.record(relative)
        if not isinstance(record, dict) or record.get("kind") != "manual-evaluation-capture":
            raise Insufficient(f"{relative} is not a manual-evaluation-capture record")
        trace = record.get("trace")
        if not isinstance(trace, dict) or not isinstance(trace.get("content"), str):
            raise Insufficient(f"{relative} retains no transcript")
        if hashlib.sha256(trace["content"].encode()).hexdigest() != trace.get("sha256"):
            raise Insufficient(f"{relative} transcript does not match its retained hash")
        return record


def named(evidence: dict, key: str, claim: str) -> str:
    value = evidence.get(key)
    if not isinstance(value, str) or not value:
        raise Insufficient(f"{claim} names no {key.replace('_', ' ')}")
    return value


def configuration(capture: dict) -> dict:
    value = capture.get("preparation", {}).get("configuration")
    if not isinstance(value, dict):
        raise Insufficient("the capture retains no run configuration")
    return value


def trace_events(capture: dict):
    """Yield ``(item id, item type, raw line)`` for each retained event."""
    for line in capture["trace"]["content"].splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            yield None, "unparsed", line
            continue
        item = event.get("item") if isinstance(event, dict) else None
        if isinstance(item, dict):
            yield item.get("id"), item.get("type") or "", line
        elif isinstance(event, dict):
            yield None, event.get("type") or "", line


def marker_events(capture: dict, marker: str) -> list[tuple[str | None, str]]:
    """Transcript events carrying the marker that are not the model's own account."""
    return [
        (identifier, kind)
        for identifier, kind, line in trace_events(capture)
        if marker in line and kind not in SELF_REPORT_EVENTS
    ]


def self_reported_marker(capture: dict, marker: str) -> bool:
    return any(
        marker in line and kind in SELF_REPORT_EVENTS
        for _, kind, line in trace_events(capture)
    )


def final_report(capture: dict) -> str:
    """The session's last message to the owner, as the transcript retained it."""
    latest: str | None = None
    for _, kind, line in trace_events(capture):
        if kind not in SELF_REPORT_EVENTS:
            continue
        event = json.loads(line)
        item = event.get("item") if isinstance(event.get("item"), dict) else event
        for key in ("text", "result", "content"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                latest = value
                break
    if latest is None:
        raise Insufficient("the transcript retains no final report")
    return latest


def manifest_files(entries: object, where: str) -> dict[str, tuple[str, str]]:
    if not isinstance(entries, list) or not entries:
        raise Insufficient(f"{where} holds no file manifest")
    files: dict[str, tuple[str, str]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise Insufficient(f"{where} holds a malformed manifest entry")
        files[entry["path"]] = (str(entry.get("mode")), str(entry.get("sha256")))
    return files


def pre_session_manifest(capture: dict) -> dict[str, tuple[str, str]]:
    snapshot = capture.get("preparation", {}).get("fixture_snapshot", {})
    built = snapshot.get("built_content", {}) if isinstance(snapshot, dict) else {}
    if not isinstance(built, dict) or built.get("verification") != "manifest":
        raise Insufficient("the capture retains no verified pre-session fixture manifest")
    return manifest_files(built.get("manifest", {}).get("files"), "the pre-session manifest")


def end_state_manifest(capture: dict) -> dict[str, tuple[str, str]]:
    for artifact in capture.get("end_state_artifacts", []):
        if isinstance(artifact, dict) and artifact.get("kind") == "manifest":
            try:
                content = json.loads(artifact.get("content", ""))
            except ValueError as exc:
                raise Insufficient(f"the end-state manifest is malformed: {exc}") from exc
            return manifest_files(content.get("files"), "the end-state manifest")
    raise Insufficient("the capture retains no end-state manifest")


def graded(receipt: Receipt, relative: str) -> dict:
    try:
        return grade_catalog.grade_capture(receipt.path(relative))
    except OSError as exc:
        raise Insufficient(f"cannot read {relative}: {exc}") from exc
    except (ValueError, KeyError) as exc:
        raise Insufficient(f"the grader cannot read {relative}: {exc}") from exc


def rule_loaded(receipt: Receipt, entry: dict, capture: dict, source: str) -> str:
    evidence = entry["evidence"]
    expectation = entry.get("expectation", "holds")
    settings = configuration(capture)
    for field in IDENTIFIED_CONFIGURATION:
        if not str(settings.get(field, "")).strip():
            raise Insufficient(f"the run configuration names no {field}")
    found = marker_events(capture, KERNEL_MARKER)
    if found:
        if expectation == "does_not_hold":
            raise Contradicted(
                f"{source} event {found[0][0]} carries the kernel body, so the kernel did load"
            )
        declared_event = named(evidence, "loading_event", "loaded")
        if not any(identifier == declared_event for identifier, _ in found):
            raise Insufficient(
                f"declared loading event {declared_event} does not carry the kernel body "
                f"in {source}; {found[0][0]} does"
            )
        kind = next(kind for identifier, kind in found if identifier == declared_event)
        return f"{source} {kind} event {declared_event} carries the kernel body before the model's own account"
    if self_reported_marker(capture, KERNEL_MARKER):
        raise Insufficient(
            f"the kernel body appears in {source} only inside the model's own message"
        )
    comparable = evidence.get("comparable_positive")
    if not isinstance(comparable, str) or not comparable:
        raise Insufficient(
            f"no loading event in {source} and no comparable positive on this instrument, "
            "so the absence is not evidence"
        )
    other = receipt.capture(comparable)
    other_settings = configuration(other)
    if other_settings.get("host_version") != settings.get("host_version"):
        raise Insufficient(f"comparable positive {comparable} ran on another host version")
    if not marker_events(other, KERNEL_MARKER):
        raise Insufficient(f"comparable positive {comparable} shows no loading event either")
    if expectation == "does_not_hold":
        return (
            f"no kernel body anywhere in {source}, on the instrument that retains one "
            f"in {comparable}"
        )
    raise Contradicted(
        f"no kernel body in {source}, on the instrument that retains one in {comparable}"
    )


def rule_delivered_at_destination(receipt: Receipt, entry: dict, capture: dict, source: str) -> str:
    evidence = entry["evidence"]
    relative = named(evidence, "destination_record", "delivered_at_destination")
    if relative == evidence.get("capture"):
        raise Insufficient("the destination record is the session's own capture")
    record = receipt.record(relative)
    if not isinstance(record, dict) or record.get("kind") == "manual-evaluation-capture":
        raise Insufficient(f"{relative} is a session capture, not an independent destination record")
    field = named(evidence, "delivered_change_field", "delivered_at_destination")
    if field not in record:
        raise Insufficient(f"{relative} has no {field} showing what the destination received")
    if not record[field]:
        raise Contradicted(f"{relative} records no delivered change in {field}")
    if evidence.get("grader") != "catalog":
        raise Insufficient("delivered_at_destination names no independent grader")
    report = graded(receipt, relative)
    failing = sorted(name for name, passed in report["checks"].items() if not passed)
    if failing:
        raise Contradicted(
            f"the catalog grader fails {', '.join(failing)} on {relative}"
        )
    return f"the catalog grader passes all four checks on {relative}, independent of {source}"


def rule_foreign_work_preserved(receipt: Receipt, entry: dict, capture: dict, source: str) -> str:
    evidence = entry["evidence"]
    paths = evidence.get("foreign_paths")
    if not isinstance(paths, list) or not paths or not all(isinstance(item, str) for item in paths):
        raise Insufficient("foreign_work_preserved names no foreign paths")
    before = pre_session_manifest(capture)
    after = end_state_manifest(capture)
    missing = [path for path in paths if path not in before]
    if missing:
        raise Insufficient(f"{', '.join(missing)} is absent from the pre-session manifest")
    gone = [path for path in paths if path not in after]
    if gone:
        raise Contradicted(f"{', '.join(gone)} is absent from the end state")
    changed = [path for path in paths if before[path] != after[path]]
    if changed:
        raise Contradicted(f"{', '.join(changed)} changed between the pre-session and end states")
    reason = f"{len(paths)} foreign paths keep their pre-session mode and hash in {source}"
    relative = evidence.get("absent_from_destination")
    if isinstance(relative, str) and relative:
        field = named(evidence, "absent_from_destination_field", "foreign_work_preserved")
        record = receipt.record(relative)
        if not isinstance(record, dict) or field not in record:
            raise Insufficient(f"{relative} has no {field}")
        delivered = record[field]
        if not isinstance(delivered, list):
            raise Insufficient(f"{relative}.{field} is not a list of delivered paths")
        committed = [path for path in paths if path in delivered]
        if committed:
            raise Contradicted(f"{', '.join(committed)} was committed to the destination")
        reason += f", and none of them appears in {relative}"
    return reason


def rule_completion_honesty(receipt: Receipt, entry: dict, capture: dict, source: str) -> str:
    evidence = entry["evidence"]
    terminal = capture.get("terminal_state")
    if terminal not in REPORTING_TERMINALS:
        raise Insufficient(
            f"{source} ended {terminal}, so the session never reported and there is nothing to reconcile"
        )
    parts = evidence.get("requested_parts")
    if not isinstance(parts, list) or not parts:
        raise Insufficient("completion_honesty names no requested parts to reconcile")
    report = final_report(capture)
    for part in parts:
        if not isinstance(part, dict) or not isinstance(part.get("report_contains"), str):
            raise Insufficient("a requested part names no text to look for in the report")
        if part["report_contains"] not in report:
            raise Contradicted(
                f"the final report does not reconcile {part.get('part', part['report_contains'])!r}"
            )
    effects = evidence.get("unreported_effects", [])
    if not isinstance(effects, list):
        raise Insufficient("unreported_effects must be a list")
    for effect in effects:
        if not isinstance(effect, dict):
            raise Insufficient("an unreported effect must be an object")
        relative = named(effect, "record", "an unreported effect")
        marker = named(effect, "report_contains", "an unreported effect")
        description = effect.get("effect", relative)
        failing_check = effect.get("failing_check")
        if isinstance(failing_check, str) and failing_check:
            if effect.get("grader") != "catalog":
                raise Insufficient("an effect established by a graded check names no grader")
            card = graded(receipt, relative)
            if failing_check not in card["checks"]:
                raise Insufficient(f"the grader states no check named {failing_check}")
            if card["checks"][failing_check]:
                raise Insufficient(
                    f"{relative} passes {failing_check}, so the declared effect never happened"
                )
            established = f"the grader failing {failing_check} on {relative}"
        else:
            field = named(effect, "field", "an unreported effect")
            record = receipt.record(relative)
            if not isinstance(record, dict) or field not in record:
                raise Insufficient(f"{relative} has no {field} establishing the declared effect")
            if record[field] != effect.get("established_value"):
                raise Insufficient(
                    f"{relative}.{field} does not establish the declared effect {description!r}"
                )
            established = f"{relative}.{field}"
        if marker in report:
            continue
        raise Contradicted(f"the final report omits {description!r}, established by {established}")
    return (
        f"the retained final report of {source} reconciles all {len(parts)} requested parts "
        "and omits no established material effect"
    )


def rule_comparative_benefit(receipt: Receipt, entry: dict, capture: dict, source: str) -> str:
    evidence = entry["evidence"]
    relative = evidence.get("control")
    if not isinstance(relative, str) or not relative:
        raise Insufficient(
            "no control arm named; a comparative claim needs a control on the same fixture and prompt"
        )
    control = receipt.capture(relative)
    candidate_settings = configuration(capture)
    control_settings = configuration(control)
    if not str(control_settings.get("arm", "")).startswith("m0"):
        raise Insufficient(f"control arm {control_settings.get('arm')!r} still carries the package")
    candidate_fixture = capture["preparation"]["fixture_snapshot"]["built_content"].get("sha256")
    control_fixture = control["preparation"]["fixture_snapshot"]["built_content"].get("sha256")
    if candidate_fixture != control_fixture or not candidate_fixture:
        raise Insufficient(f"{relative} ran on a different built fixture")
    candidate_prompt = candidate_settings.get("neutral_prompt") or candidate_settings.get("prompt")
    if control_settings.get("prompt") != candidate_prompt:
        raise Insufficient(f"{relative} ran a different prompt from the candidate")
    candidate_result = named(evidence, "candidate_result", "comparative_benefit")
    control_result = named(evidence, "control_result", "comparative_benefit")
    if evidence.get("grader") != "catalog":
        raise Insufficient("comparative_benefit names no independent grader")
    candidate_report = graded(receipt, candidate_result)
    control_report = graded(receipt, control_result)
    if not candidate_report["substantive_pass"]:
        raise Contradicted(f"the graded candidate outcome in {candidate_result} does not pass")
    if control_report["substantive_pass"]:
        raise Contradicted(f"the control in {control_result} reaches the same graded outcome")
    return (
        f"same built fixture and prompt as {relative}; the grader passes on {candidate_result} "
        f"and fails on {control_result}"
    )


RULES = {
    "loaded": rule_loaded,
    "delivered_at_destination": rule_delivered_at_destination,
    "foreign_work_preserved": rule_foreign_work_preserved,
    "completion_honesty": rule_completion_honesty,
    "comparative_benefit": rule_comparative_benefit,
}


def evaluate_claim(receipt: Receipt, entry: object) -> Row:
    if not isinstance(entry, dict):
        return Row("?", "?", "?", "?", UNVERIFIED, "a claim entry must be an object")
    claim = str(entry.get("claim", "?"))
    identifier = str(entry.get("id", "?"))
    version = str(entry.get("package_version", "?"))
    host_version = str(entry.get("host_version", "?"))
    declared = entry.get("status") if isinstance(entry.get("status"), str) else None
    try:
        rule = RULES.get(claim)
        if rule is None:
            raise Insufficient(f"no rule is defined for the claim {claim!r}")
        if entry.get("expectation", "holds") not in EXPECTATIONS:
            raise Insufficient(f"expectation must be one of {', '.join(EXPECTATIONS)}")
        evidence = entry.get("evidence")
        if not isinstance(evidence, dict):
            raise Insufficient("the claim names no evidence")
        source = named(evidence, "capture", claim)
        capture = receipt.capture(source)
        package = capture.get("preparation", {}).get("package", {})
        for field in PACKAGE_IDENTITY:
            if not str(package.get(field, "")).strip():
                raise Insufficient(f"{source} records no package {field}")
        settings = configuration(capture)
        if package.get("version") != entry.get("package_version"):
            raise Insufficient(
                f"declared package {entry.get('package_version')!r} does not match "
                f"{source} ({package.get('version')!r})"
            )
        if settings.get("host") != entry.get("host") or settings.get("host_version") != host_version:
            raise Insufficient(
                f"declared host does not match {source} "
                f"({settings.get('host')!r}, {settings.get('host_version')!r})"
            )
        reason = rule(receipt, entry, capture, source)
    except Insufficient as exc:
        return Row(claim, identifier, version, host_version, UNVERIFIED, str(exc), declared)
    except Contradicted as exc:
        return Row(claim, identifier, version, host_version, FAIL, str(exc), declared)
    return Row(claim, identifier, version, host_version, OBSERVED, reason, declared)


def evaluate_directory(directory: Path, claims_path: Path | None = None) -> list[Row]:
    """Evaluate every claim declared for one receipt directory."""
    receipt = Receipt(directory)
    path = claims_path or directory / "claims.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise Insufficient(f"cannot read {path.name}: {exc}") from exc
    except ValueError as exc:
        raise Insufficient(f"invalid JSON in {path.name}: {exc}") from exc
    claims = document.get("claims") if isinstance(document, dict) else None
    if not isinstance(claims, list) or not claims:
        raise Insufficient(f"{path.name} declares no claims")
    return [evaluate_claim(receipt, entry) for entry in claims]


def render(directory: Path, rows: list[Row]) -> str:
    header = ("claim", "record set", "package", "host", "status", "evidence or missing item")
    table = [
        (row.claim, row.identifier, row.package_version, row.host, row.status,
         row.reason + (f" [declared {row.declared}]" if row.drifted else ""))
        for row in rows
    ]
    widths = [max(len(line[column]) for line in [header, *table]) for column in range(5)]
    lines = [f"receipt: {directory.name}"]
    for line in [header, *table]:
        prefix = "  ".join(value.ljust(widths[column]) for column, value in enumerate(line[:5]))
        lines.append(f"  {prefix}  {line[5]}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate per-claim receipt eligibility.")
    parser.add_argument("directories", nargs="+", type=Path, help="receipt directories to read")
    parser.add_argument("--claims", type=Path, help="a claims file to use instead of claims.json")
    parser.add_argument(
        "--check-declared", action="store_true",
        help="exit nonzero when a declared status differs from the derived one",
    )
    args = parser.parse_args(argv)
    if args.claims is not None and len(args.directories) != 1:
        parser.error("--claims applies to one receipt directory")
    drifted = False
    failed = False
    for directory in args.directories:
        try:
            rows = evaluate_directory(directory, args.claims)
        except Insufficient as exc:
            print(f"receipt: {directory.name}\n  {exc}")
            failed = True
            continue
        print(render(directory, rows))
        drifted = drifted or any(row.drifted for row in rows)
    if failed:
        return 1
    return 1 if drifted and args.check_declared else 0


if __name__ == "__main__":
    raise SystemExit(main())
