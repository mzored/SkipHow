from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skiphow.intake import (
    DuplicateDisposition,
    EvidenceStatus,
    LocalIntakeStore,
    Recommendation,
    SignalType,
    WorkItem,
    actionable_work_items,
    atomize,
    decide_candidate,
    find_candidates,
    group_signals,
    map_epic,
)


def test_batch_of_twenty_preserves_provenance_and_does_not_invent_bugs(tmp_path: Path) -> None:
    records = [
        {"verbatim": f"Customer note {index}", "source": f"call-{index}", "context": "weekly review"}
        for index in range(18)
    ] + [
        {"verbatim": "Bug: checkout fails", "source": "support", "observed_evidence": ["HTTP 500"], "confidence": 0.9},
        {"verbatim": "Checkout might fail", "source": "sales"},
    ]
    signals = atomize(records, default_source="batch")
    assert len(signals) == 20
    assert {signal.source for signal in signals} >= {"call-0", "support", "sales"}
    assert signals[-2].kind is SignalType.BUG
    assert signals[-1].kind is not SignalType.BUG

    store = LocalIntakeStore(tmp_path)
    first = store.persist(signals)
    second = store.persist(signals)
    assert first["signals_added"] == 20
    assert second["signals_added"] == 0


def test_candidate_search_is_bounded_and_duplicate_decision_stays_outside() -> None:
    signal = atomize(["Checkout charges twice"], default_source="owner")[0]
    items = [
        WorkItem(str(index), f"Checkout duplicate charge {index}", (), "Prevent duplicate checkout charge", "money", ("one charge",))
        for index in range(30)
    ]
    candidates = find_candidates(signal, items)
    assert len(candidates) == 20
    assert all(candidate.score > 0 for candidate in candidates)

    decision = decide_candidate(
        signal, candidates, candidates[0].item_id, DuplicateDisposition.RELATED, "partial overlap"
    )
    assert decision.disposition is DuplicateDisposition.RELATED
    create = decide_candidate(signal, candidates, None, DuplicateDisposition.CREATE, "no semantic match")
    assert create.candidate_item_id is None
    with pytest.raises(ValueError, match="returned candidate"):
        decide_candidate(signal, candidates, "missing", "DUPLICATE", "same behavior")
    with pytest.raises(ValueError, match="limit"):
        find_candidates(signal, items, limit=21)


def test_mixed_raw_input_atomizes_explicit_lists_and_preserves_provenance() -> None:
    signals = atomize(
        [
            {
                "verbatim": "- Checkout fails\n- Add saved cards\n  for returning users",
                "source": "call-7",
                "source_record_id": "transcript-7",
                "captured_at": "2026-08-25",
                "links": ["https://example.test/call/7"],
            },
            "Why is export slow?",
        ],
        default_source="owner",
    )
    assert [signal.verbatim for signal in signals] == [
        "Checkout fails",
        "Add saved cards for returning users",
        "Why is export slow?",
    ]
    assert signals[0].raw_id == signals[1].raw_id == "transcript-7"
    assert [signals[0].atom_index, signals[1].atom_index] == [0, 1]
    assert signals[0].captured_at == "2026-08-25"
    assert signals[0].links == ("https://example.test/call/7",)
    assert signals[0].kind is SignalType.RISK
    assert signals[0].evidence_status is EvidenceStatus.SPECULATION

    # A direct string is one record, not an iterable of characters.
    assert len(atomize("One intact observation", default_source="owner")) == 1
    with pytest.raises(ValueError, match="sequence of strings"):
        atomize({"verbatim": "Broken", "observed_evidence": "HTTP 500"}, default_source="owner")


def test_explicit_bug_without_observed_evidence_stays_a_risk() -> None:
    speculative = atomize(
        {"verbatim": "Checkout may fail", "kind": "BUG", "confidence": 1},
        default_source="sales",
    )[0]
    observed = atomize(
        {"verbatim": "Checkout fails", "kind": "BUG", "observed_evidence": ["HTTP 500"], "confidence": 0.9},
        default_source="support",
    )[0]
    assert speculative.kind is SignalType.RISK
    assert speculative.recommendation is Recommendation.INVESTIGATE
    assert observed.kind is SignalType.BUG
    assert observed.evidence_status is EvidenceStatus.OBSERVED
    assert observed.recommendation is Recommendation.NOW


def test_grouping_accounts_for_every_signal_and_shapes_only_actionable_work() -> None:
    signals = atomize(
        [
            {"verbatim": "Checkout duplicate charge", "observed_evidence": ["charge ids 1 and 2"], "confidence": 0.9},
            {"verbatim": "Duplicate checkout charge", "observed_evidence": ["support case 8"], "confidence": 0.9},
            "Idea: add saved cards",
            "The new colors are pleasant",
            "Could invoices be wrong?",
        ],
        default_source="batch",
    )
    groups = group_signals(signals, similarity=0.3)
    assert sorted(signal_id for group in groups for signal_id in group.signal_ids) == sorted(
        signal.signal_id for signal in signals
    )
    assert any(len(group.signal_ids) == 2 for group in groups)
    items = actionable_work_items(signals, groups)
    item_signal_ids = {signal_id for item in items for signal_id in item.signal_ids}
    feedback = next(signal for signal in signals if signal.kind is SignalType.FEEDBACK)
    question = next(signal for signal in signals if signal.kind is SignalType.QUESTION)
    assert feedback.signal_id not in item_signal_ids
    assert question.signal_id not in item_signal_ids
    assert any(len(item.signal_ids) == 2 for item in items)


def test_epic_mapping_is_explicit_and_rejects_invalid_dependency_graphs() -> None:
    epic = WorkItem("epic", "Reliable checkout", (), "Reliable checkout", "revenue", ("all slices ship",))
    first = WorkItem("observe", "Observe", (), "Add telemetry", "diagnosis", ("events visible",))
    second = WorkItem("fix", "Fix", (), "Prevent repeat charge", "money", ("one charge",))

    mapped_epic, children = map_epic(epic, [first, second], dependencies={"fix": ["observe"]})
    assert mapped_epic.is_epic
    assert children[0].parent_id == children[1].parent_id == "epic"
    assert children[1].dependencies == ("observe",)
    with pytest.raises(ValueError, match="at least two"):
        map_epic(epic, [first])
    with pytest.raises(ValueError, match="cycle"):
        map_epic(epic, [first, second], dependencies={"fix": ["observe"], "observe": ["fix"]})


def test_local_store_deduplicates_one_batch_and_rejects_identity_drift(tmp_path: Path) -> None:
    signal = atomize("Idea: export CSV", default_source="owner")[0]
    store = LocalIntakeStore(tmp_path)
    result = store.persist([signal, signal])
    assert result == {"signals_added": 1, "signals_total": 1, "work_items": 0}
    assert len((tmp_path / ".skiphow/intake/signals.jsonl").read_text().splitlines()) == 1

    changed = replace(signal, context="changed under the same identity")
    with pytest.raises(ValueError, match="signal identity collision"):
        store.persist([changed])


def test_local_work_item_replay_keeps_priority_and_dependency_mapping(tmp_path: Path) -> None:
    item = WorkItem(
        "item-1",
        "Prevent repeat charges",
        ("sig-1",),
        "One charge per checkout",
        "Customers lose money",
        ("one charge",),
        evidence=("charge ids 1 and 2",),
        recommendation=Recommendation.NOW,
        parent_id="epic-1",
        dependencies=("item-0",),
    )
    store = LocalIntakeStore(tmp_path)
    assert store.persist([], [item])["work_items"] == 1
    assert store.persist([], [item])["work_items"] == 1
