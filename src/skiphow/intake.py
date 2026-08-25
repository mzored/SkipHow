"""Batch product-signal intake with provenance and local persistence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence


class SignalType(str, Enum):
    BUG = "BUG"
    IDEA = "IDEA"
    QUESTION = "QUESTION"
    RISK = "RISK"
    TECH_DEBT = "TECH_DEBT"
    FEEDBACK = "FEEDBACK"


class Recommendation(str, Enum):
    NOW = "NOW"
    NEXT = "NEXT"
    LATER = "LATER"
    DECLINE = "DECLINE"
    INVESTIGATE = "INVESTIGATE"


class EvidenceStatus(str, Enum):
    OBSERVED = "OBSERVED"
    SPECULATION = "SPECULATION"


class DuplicateDisposition(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DUPLICATE = "DUPLICATE"
    RELATED = "RELATED"
    DISTINCT = "DISTINCT"
    NEEDS_RESEARCH = "NEEDS_RESEARCH"


@dataclass(frozen=True, slots=True)
class Signal:
    signal_id: str
    source: str
    verbatim: str
    context: str = ""
    observed_evidence: tuple[str, ...] = ()
    confidence: float = 0.5
    kind: SignalType = SignalType.FEEDBACK
    recommendation: Recommendation = Recommendation.INVESTIGATE
    raw_id: str = ""
    atom_index: int = 0
    evidence_status: EvidenceStatus = EvidenceStatus.SPECULATION
    captured_at: str = ""
    links: tuple[str, ...] = ()
    source_record_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["observed_evidence"] = list(self.observed_evidence)
        value["links"] = list(self.links)
        return value


@dataclass(frozen=True, slots=True)
class Candidate:
    item_id: str
    title: str
    score: float


@dataclass(frozen=True, slots=True)
class CandidateDecision:
    signal_id: str
    candidate_item_id: str | None
    disposition: DuplicateDisposition
    reason: str


@dataclass(frozen=True, slots=True)
class SignalGroup:
    group_id: str
    signal_ids: tuple[str, ...]
    title: str
    recommendation: Recommendation
    actionable: bool


@dataclass(frozen=True, slots=True)
class WorkItem:
    item_id: str
    title: str
    signal_ids: tuple[str, ...]
    outcome: str
    why: str
    acceptance: tuple[str, ...]
    non_goals: tuple[str, ...] = ()
    relationships: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    recommendation: Recommendation = Recommendation.INVESTIGATE
    parent_id: str | None = None
    dependencies: tuple[str, ...] = ()
    is_epic: bool = False

    def __post_init__(self) -> None:
        if not self.item_id.strip() or not self.title.strip() or not self.outcome.strip():
            raise ValueError("work item identity, title, and outcome must be non-empty")
        if self.item_id in self.dependencies:
            raise ValueError("work item cannot depend on itself")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for name in (
            "signal_ids",
            "acceptance",
            "non_goals",
            "relationships",
            "evidence",
            "dependencies",
        ):
            value[name] = list(value[name])
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> WorkItem:
        sequence_fields = (
            "signal_ids",
            "acceptance",
            "non_goals",
            "relationships",
            "evidence",
            "dependencies",
        )
        normalized = dict(value)
        for name in sequence_fields:
            raw = normalized.get(name, ())
            if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
                raise ValueError(f"work item {name} must be a sequence of strings")
            if not all(isinstance(item, str) for item in raw):
                raise ValueError(f"work item {name} must contain strings")
            normalized[name] = tuple(raw)
        try:
            normalized["recommendation"] = Recommendation(
                normalized.get("recommendation", Recommendation.INVESTIGATE)
            )
            return cls(**normalized)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid stored work item") from exc


def _stable_id(source: str, verbatim: str, context: str) -> str:
    digest = hashlib.sha256(f"{source}\0{verbatim}\0{context}".encode()).hexdigest()
    return f"sig-{digest[:16]}"


def _raw_id(source: str, verbatim: str, context: str) -> str:
    digest = hashlib.sha256(f"{source}\0{verbatim}\0{context}".encode()).hexdigest()
    return f"raw-{digest[:16]}"


def _source_record_raw_id(source: str, source_record_id: str) -> str:
    digest = hashlib.sha256(
        f"source-record\0{source}\0{source_record_id}".encode()
    ).hexdigest()
    return f"raw-{digest[:16]}"


def _tokens(value: str) -> frozenset[str]:
    stop_words = {
        "a", "an", "and", "are", "at", "be", "for", "from", "in", "is", "it",
        "of", "on", "or", "the", "to", "we", "with", "и", "в", "во", "на", "не",
        "но", "с", "со", "что", "это",
    }
    return frozenset(
        token
        for token in re.findall(r"[\w]+", value.casefold(), re.UNICODE)
        if len(token) > 1 and token not in stop_words
    )


_LIST_ITEM = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")


def _atoms(verbatim: str) -> list[str]:
    """Split explicit lists and line-separated notes without splitting sentences."""
    lines = [line.strip() for line in verbatim.splitlines() if line.strip()]
    if len(lines) < 2:
        return [verbatim.strip()]
    if not any(_LIST_ITEM.match(line) for line in lines):
        return lines
    atoms: list[str] = []
    current: list[str] = []
    for line in lines:
        if _LIST_ITEM.match(line):
            if current:
                atoms.append(" ".join(current))
            current = [_LIST_ITEM.sub("", line, count=1).strip()]
        elif current:
            current.append(line)
        else:
            current = [line]
    if current:
        atoms.append(" ".join(current))
    return [atom for atom in atoms if atom]


def classify(verbatim: str, evidence: Sequence[str]) -> SignalType:
    """Provide a conservative cold-start type; the product controller may override it."""
    text = verbatim.casefold()
    if any(word in text for word in ("?", "should we", "стоит ли", "почему")):
        return SignalType.QUESTION
    if any(word in text for word in ("debt", "legacy", "ownership", "техдолг", "поддерж")):
        return SignalType.TECH_DEBT
    if any(word in text for word in ("risk", "might", "could", "риск", "может")) and not evidence:
        return SignalType.RISK
    if any(word in text for word in ("bug", "broken", "fails", "duplicate", "twice", "wrong", "ошиб", "слом", "не работает")):
        return SignalType.BUG if evidence else SignalType.RISK
    if any(word in text for word in ("idea", "add ", "feature", "идея", "добав")):
        return SignalType.IDEA
    return SignalType.FEEDBACK


def recommend(kind: SignalType, confidence: float, evidence: Sequence[str]) -> Recommendation:
    if kind is SignalType.BUG and evidence and confidence >= 0.8:
        return Recommendation.NOW
    if kind in {SignalType.RISK, SignalType.QUESTION} or (kind is SignalType.BUG and not evidence):
        return Recommendation.INVESTIGATE
    if kind in {SignalType.IDEA, SignalType.TECH_DEBT} and confidence >= 0.7:
        return Recommendation.NEXT
    return Recommendation.LATER


def atomize(
    records: str | Mapping[str, Any] | Iterable[str | Mapping[str, Any]],
    *,
    default_source: str,
) -> list[Signal]:
    """Turn mixed raw records and explicit lists into provenance-linked signals."""
    if isinstance(records, (str, Mapping)):
        records = [records]
    signals: list[Signal] = []
    seen: dict[str, Signal] = {}
    for record in records:
        if isinstance(record, str):
            item = {"verbatim": record}
        elif isinstance(record, Mapping):
            item = dict(record)
        else:
            raise ValueError("every raw signal must be text or a mapping")
        verbatim = item.get("verbatim", item.get("text", item.get("transcript")))
        source = item.get("source", default_source)
        context = item.get("context", "")
        evidence_value = item.get("observed_evidence", ())
        if isinstance(evidence_value, (str, bytes)) or evidence_value is None:
            raise ValueError("signal evidence must be a sequence of strings")
        try:
            evidence = tuple(evidence_value)
        except TypeError as exc:
            raise ValueError("signal evidence must be a sequence of strings") from exc
        links_value = item.get("links", ())
        if isinstance(links_value, (str, bytes)) or links_value is None:
            raise ValueError("signal links must be a sequence of strings")
        try:
            links = tuple(links_value)
        except TypeError as exc:
            raise ValueError("signal links must be a sequence of strings") from exc
        captured_at = item.get("captured_at", "")
        try:
            confidence = float(item.get("confidence", 0.5))
        except (TypeError, ValueError) as exc:
            raise ValueError("signal confidence must be a number in [0, 1]") from exc
        if not isinstance(verbatim, str) or not verbatim.strip():
            raise ValueError("every signal needs non-empty verbatim text")
        if (
            not isinstance(source, str)
            or not source.strip()
            or not isinstance(context, str)
            or not isinstance(captured_at, str)
        ):
            raise ValueError("signal source and context must be strings")
        if (
            not all(isinstance(value, str) and value.strip() for value in evidence + links)
            or not 0 <= confidence <= 1
        ):
            raise ValueError("signal evidence must be strings and confidence must be in [0, 1]")
        supplied_raw_id = item.get("source_record_id")
        if supplied_raw_id is not None and (
            not isinstance(supplied_raw_id, str) or not supplied_raw_id.strip()
        ):
            raise ValueError("source_record_id must be a non-empty string")
        raw_id = (
            _source_record_raw_id(source, supplied_raw_id)
            if supplied_raw_id is not None
            else _raw_id(source, verbatim, context)
        )
        atoms = _atoms(verbatim)
        for atom_index, atom in enumerate(atoms):
            signal_id = (
                _stable_id(raw_id, str(atom_index), "")
                if supplied_raw_id is not None or len(atoms) > 1
                else _stable_id(source, atom, context)
            )
            requested_kind = item.get("kind")
            kind = SignalType(requested_kind) if requested_kind else classify(atom, evidence)
            # A report without an observation is a risk to investigate, even if its
            # author called it a bug. This prevents speculation becoming bug evidence.
            if kind is SignalType.BUG and not evidence:
                kind = SignalType.RISK
            requested_recommendation = item.get("recommendation")
            disposition = (
                Recommendation(requested_recommendation)
                if requested_recommendation
                else recommend(kind, confidence, evidence)
            )
            signal = Signal(
                signal_id, source, atom, context, evidence, confidence, kind,
                disposition, raw_id, atom_index,
                EvidenceStatus.OBSERVED if evidence else EvidenceStatus.SPECULATION,
                captured_at, links, supplied_raw_id or "",
            )
            current = seen.get(signal_id)
            if current is not None:
                if current != signal:
                    identity = supplied_raw_id or "derived raw record"
                    raise ValueError(
                        f"raw signal identity was reused with different content: {identity}"
                    )
                continue
            seen[signal_id] = signal
            signals.append(signal)
    return signals


def find_candidates(
    signal: Signal, items: Iterable[WorkItem], *, limit: int = 20
) -> list[Candidate]:
    """Return a bounded lexical candidate set. The controller decides duplicates."""
    if not 1 <= limit <= 20:
        raise ValueError("candidate limit must be in [1, 20]")
    query = _tokens(signal.verbatim)
    candidates: dict[str, Candidate] = {}
    for item in items:
        target = _tokens(
            " ".join((item.title, item.outcome, item.why, *item.acceptance, *item.evidence))
        )
        union = query | target
        score = len(query & target) / len(union) if union else 0.0
        if score:
            candidate = Candidate(item.item_id, item.title, score)
            current = candidates.get(item.item_id)
            if current is None or candidate.score > current.score:
                candidates[item.item_id] = candidate
    return sorted(candidates.values(), key=lambda value: (-value.score, value.item_id))[:limit]


def decide_candidate(
    signal: Signal,
    candidates: Sequence[Candidate],
    candidate_item_id: str | None,
    disposition: DuplicateDisposition | str,
    reason: str,
) -> CandidateDecision:
    """Record a controller decision without inferring it from lexical similarity."""
    if not reason.strip():
        raise ValueError("candidate decision needs a reason")
    if len(candidates) > 20:
        raise ValueError("candidate decision set must contain at most 20 items")
    selected = DuplicateDisposition(disposition)
    requires_candidate = selected in {
        DuplicateDisposition.UPDATE,
        DuplicateDisposition.DUPLICATE,
        DuplicateDisposition.RELATED,
    }
    if requires_candidate and candidate_item_id not in {
        candidate.item_id for candidate in candidates
    }:
        raise ValueError("duplicate decision must refer to a returned candidate")
    if not requires_candidate and candidate_item_id is not None and candidate_item_id not in {
        candidate.item_id for candidate in candidates
    }:
        raise ValueError("duplicate decision must refer to a returned candidate")
    return CandidateDecision(
        signal.signal_id,
        candidate_item_id,
        selected,
        reason.strip(),
    )


def group_signals(signals: Sequence[Signal], *, similarity: float = 0.34) -> list[SignalGroup]:
    """Group materially related signals without merging or discarding provenance."""
    if not 0 < similarity <= 1:
        raise ValueError("similarity must be in (0, 1]")
    groups: list[list[Signal]] = []
    for signal in signals:
        query = _tokens(f"{signal.verbatim} {signal.context}")
        match: list[Signal] | None = None
        best_score = 0.0
        for group in groups:
            target = frozenset().union(
                *(_tokens(f"{member.verbatim} {member.context}") for member in group)
            )
            union = query | target
            score = len(query & target) / len(union) if union else 0.0
            if score >= similarity and score > best_score:
                match, best_score = group, score
        if match is None:
            groups.append([signal])
        else:
            match.append(signal)

    result: list[SignalGroup] = []
    priority = {
        Recommendation.NOW: 0,
        Recommendation.NEXT: 1,
        Recommendation.INVESTIGATE: 2,
        Recommendation.LATER: 3,
        Recommendation.DECLINE: 4,
    }
    for members in groups:
        recommendation = min((item.recommendation for item in members), key=priority.__getitem__)
        actionable = recommendation is not Recommendation.DECLINE and any(
            item.kind in {SignalType.IDEA, SignalType.TECH_DEBT}
            or (
                item.kind is SignalType.BUG
                and item.evidence_status is EvidenceStatus.OBSERVED
            )
            for item in members
        )
        ids = tuple(item.signal_id for item in members)
        digest = hashlib.sha256("\0".join(sorted(ids)).encode()).hexdigest()[:16]
        result.append(SignalGroup(f"group-{digest}", ids, members[0].verbatim, recommendation, actionable))
    return result


def actionable_work_items(
    signals: Sequence[Signal], groups: Sequence[SignalGroup] | None = None
) -> list[WorkItem]:
    """Shape only actionable groups into minimal work items."""
    by_id = {signal.signal_id: signal for signal in signals}
    selected_groups = list(groups) if groups is not None else group_signals(signals)
    items: list[WorkItem] = []
    for group in selected_groups:
        if not group.actionable:
            continue
        if any(signal_id not in by_id for signal_id in group.signal_ids):
            raise ValueError("signal group refers to an unknown signal")
        members = [by_id[signal_id] for signal_id in group.signal_ids]
        observed = tuple(
            evidence
            for signal in members
            for evidence in signal.observed_evidence
            if evidence
        )
        sources = ", ".join(dict.fromkeys(signal.source for signal in members))
        acceptance = (
            ("The observed behavior no longer reproduces under the recorded conditions",)
            if any(signal.kind is SignalType.BUG for signal in members)
            else ("The requested outcome is observable by the affected user",)
        )
        items.append(
            WorkItem(
                f"item-{group.group_id.removeprefix('group-')}",
                group.title,
                group.signal_ids,
                group.title,
                f"Reported by {sources}",
                acceptance,
                evidence=observed,
                recommendation=group.recommendation,
            )
        )
    return items


def map_epic(
    epic: WorkItem,
    children: Sequence[WorkItem],
    *,
    dependencies: Mapping[str, Sequence[str]] | None = None,
) -> tuple[WorkItem, tuple[WorkItem, ...]]:
    """Attach an explicitly approved Epic and validate its dependency graph."""
    if len(children) < 2:
        raise ValueError("an epic needs at least two independently deliverable work items")
    if not epic.outcome.strip() or not all(child.acceptance for child in children):
        raise ValueError("epic children need a coherent outcome and acceptance criteria")
    child_ids = {child.item_id for child in children}
    if len(child_ids) != len(children) or epic.item_id in child_ids:
        raise ValueError("epic and child identities must be unique")
    graph: dict[str, tuple[str, ...]] = {}
    for item_id, values in (dependencies or {}).items():
        if isinstance(values, (str, bytes)):
            raise ValueError("dependencies must be a sequence of child identities")
        graph[item_id] = tuple(values)
    if set(graph) - child_ids:
        raise ValueError("dependency mapping refers to an unknown child")
    for item_id, values in graph.items():
        if any(value not in child_ids or value == item_id for value in values):
            raise ValueError("dependencies must refer to another child")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in visiting:
            raise ValueError("epic dependency graph contains a cycle")
        if item_id in visited:
            return
        visiting.add(item_id)
        for dependency in graph.get(item_id, ()):
            visit(dependency)
        visiting.remove(item_id)
        visited.add(item_id)

    for child_id in child_ids:
        visit(child_id)
    mapped = tuple(
        replace(child, parent_id=epic.item_id, dependencies=graph.get(child.item_id, ()))
        for child in children
    )
    return replace(epic, is_epic=True), mapped


class LocalIntakeStore:
    """Idempotent project-local fallback for signals and actionable work items."""

    def __init__(self, root: Path):
        self.project_root = root.resolve()
        self._configured_root = self.project_root / ".skiphow" / "intake"
        self._root()

    def _inside_project(self, path: Path) -> Path:
        resolved = path.resolve(strict=False)
        try:
            resolved.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError("local intake store escapes the project") from exc
        return resolved

    def _root(self) -> Path:
        return self._inside_project(self._configured_root)

    @property
    def root(self) -> Path:
        """Resolved local ledger directory, retained for API compatibility."""
        return self._root()

    def _path(self, name: str) -> Path:
        return self._inside_project(self._root() / name)

    def persist(
        self,
        signals: Sequence[Signal],
        items: Sequence[WorkItem] = (),
        *,
        provenance_updates: Sequence[WorkItem] = (),
    ) -> dict[str, int]:
        self._root().mkdir(parents=True, exist_ok=True)
        signal_path = self._path("signals.jsonl")
        stored_signals = self._signals(signal_path)
        added: list[Signal] = []
        for signal in signals:
            value = signal.to_dict()
            current = stored_signals.get(signal.signal_id)
            if current is not None and current != value:
                raise ValueError(f"signal identity collision: {signal.signal_id}")
            if current is None:
                stored_signals[signal.signal_id] = value
                added.append(signal)
        items_path = self._path("work-items.json")
        stored = self._items(items_path)
        for item in items:
            current = stored.get(item.item_id)
            value = item.to_dict()
            if current is not None and current != value:
                raise ValueError(f"work item identity collision: {item.item_id}")
            stored[item.item_id] = value
        for update in provenance_updates:
            current_value = stored.get(update.item_id)
            if current_value is None:
                raise ValueError(f"provenance target does not exist: {update.item_id}")
            current = WorkItem.from_dict(current_value)
            immutable = (
                "title",
                "outcome",
                "why",
                "acceptance",
                "non_goals",
                "parent_id",
                "dependencies",
                "is_epic",
            )
            if any(getattr(current, name) != getattr(update, name) for name in immutable):
                raise ValueError(f"provenance update changes work item scope: {update.item_id}")
            merged = replace(
                current,
                signal_ids=tuple(dict.fromkeys((*current.signal_ids, *update.signal_ids))),
                evidence=tuple(dict.fromkeys((*current.evidence, *update.evidence))),
                relationships=tuple(
                    dict.fromkeys((*current.relationships, *update.relationships))
                ),
            )
            stored[update.item_id] = merged.to_dict()
        # Validate both ledgers before replacing either file. Exact replay is a no-op.
        if added:
            temporary = self._path("signals.jsonl.tmp")
            temporary.write_text(
                "".join(
                    json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n"
                    for value in stored_signals.values()
                ),
                encoding="utf-8",
            )
            temporary.replace(signal_path)
        if items or provenance_updates:
            temporary = self._path("work-items.json.tmp")
            temporary.write_text(json.dumps(stored, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            temporary.replace(items_path)
        return {"signals_added": len(added), "signals_total": len(stored_signals), "work_items": len(stored)}

    def work_items(self) -> list[WorkItem]:
        """Read the local candidate set without creating the intake directory."""
        values = self._items(self._path("work-items.json"))
        return [WorkItem.from_dict(values[item_id]) for item_id in sorted(values)]

    @staticmethod
    def _signals(path: Path) -> dict[str, dict[str, Any]]:
        if not path.is_file():
            return {}
        result: dict[str, dict[str, Any]] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            value = json.loads(line)
            signal_id = value.get("signal_id") if isinstance(value, dict) else None
            if not isinstance(signal_id, str) or not signal_id:
                raise ValueError("local signal store is corrupt")
            if signal_id in result and result[signal_id] != value:
                raise ValueError(f"signal identity collision: {signal_id}")
            result[signal_id] = value
        return result

    @staticmethod
    def _items(path: Path) -> dict[str, dict[str, Any]]:
        if not path.is_file():
            return {}
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("local work item store is corrupt")
        return value
