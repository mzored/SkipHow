"""Synthetic privacy checks never inspect authentication or start a host."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from receipt_privacy import privacy_errors, sanitize, sanitize_text

ROOT = Path(__file__).resolve().parents[1]


def test_account_fields_are_removed_and_per_run_usage_survives():
    event = {"usage": {"input_tokens": 123, "output_tokens": 45}, "total_cost_usd": .03,
             "rate_limit_info": {"five_hour": {"utilization": .25}},
             "apiKeySource": "synthetic source", "nested": [{"accountUuid": "synthetic account"}]}
    clean = sanitize(event)
    assert clean == {"usage": event["usage"], "total_cost_usd": .03, "nested": [{}]}
    assert privacy_errors(clean) == []


def test_codex_account_containers_are_removed_but_run_token_counts_survive():
    fields = ("rate_limits", "rateLimits", "rateLimitsByLimitId", "rate_limits_by_limit_id",
              "plan_type", "planType", "account", "oauthAccount", "authMode")
    event = {field: {"synthetic_private_metadata": True} for field in fields}
    token_count = {"total_token_usage": {"input_tokens": 120, "output_tokens": 30,
                                         "total_tokens": 150}}
    event.update({"type": "token_count", "token_count": token_count,
                  "usage": {"input_tokens": 120, "output_tokens": 30}})
    clean = sanitize(event)
    assert clean == {"type": "token_count", "token_count": token_count, "usage": event["usage"]}
    assert len(privacy_errors(event)) == len(fields)
    assert privacy_errors(clean) == []


def test_private_home_paths_are_masked_inside_structured_and_plain_text():
    event = {"cwd": "/Users/synthetic/fixture", "content": json.dumps({
        "path": "/home/synthetic/project/file.py", "windows": "C:\\Users\\synthetic\\project"})}
    clean = sanitize(event)
    assert clean["cwd"] == "<operator-home>/fixture"
    assert json.loads(clean["content"]) == {
        "path": "<operator-home>/project/file.py", "windows": "<operator-home>\\project"}
    assert privacy_errors(clean) == []
    assert privacy_errors(event)


def test_embedded_json_and_jsonl_are_filtered_without_losing_events():
    lines = [json.dumps({"message": json.dumps({"email": "owner@example.test", "content": "done"})}),
             json.dumps({"session_id": "11111111-2222-3333-4444-555555555555"}),
             json.dumps({"result": "11111111-2222-3333-4444-555555555555"}), "plain log"]
    clean = sanitize_text("\n".join(lines) + "\n")
    retained = clean.splitlines()
    assert len(retained) == 4
    assert json.loads(json.loads(retained[0])["message"]) == {"content": "done"}
    assert json.loads(retained[1])["session_id"] == json.loads(retained[2])["result"]
    assert sanitize_text(clean) == clean
    assert privacy_errors(clean) == []


def test_secrets_in_free_text_and_nested_values_are_omitted():
    secret = "sk-ant-" + "a" * 30
    event = {"content": ["email owner@example.test", secret, "Bearer synthetic-token",
                         "access_token=synthetic-token", "-----BEGIN PRIVATE KEY-----\nsynthetic\n-----END PRIVATE KEY-----"],
             "signature": "synthetic signature", "access_token": "synthetic token"}
    clean = sanitize(event)
    text = json.dumps(clean)
    for private in (secret, "owner@example.test", "synthetic-token", "synthetic signature", "synthetic token"):
        assert private not in text
    assert "PRIVATE KEY" not in text
    assert privacy_errors(clean) == []


def test_validator_does_not_print_values_or_private_dictionary_keys():
    event = {"owner@example.test": "sk-proj-" + "b" * 30,
             "account_id": "private account", "signature": "private signature"}
    errors = privacy_errors(event)
    assert len(errors) == 4
    assert all(error.startswith("$.field[") for error in errors)
    assert not any(private in "\n".join(errors) for private in
                   ("owner@example.test", "private account", "private signature", "sk-proj-"))


def test_literal_redactions_and_scalar_events_are_preserved():
    assert sanitize({"text": "/synthetic/operator/log"}, {"/synthetic/operator": "<operator>"}) == {"text": "<operator>/log"}
    for value in (None, 42, False, ["safe", 42], {"status": "PASS"}):
        assert sanitize(value) == value
    assert sanitize("Fixture <fixture@example.invalid>") == "Fixture <fixture@example.invalid>"


def test_retained_receipts_contain_no_recognized_private_data():
    errors = []
    for path in sorted((ROOT / "evals/receipts").rglob("*")):
        if path.suffix in {".json", ".jsonl"}:
            errors.extend(f"{path.relative_to(ROOT)}: {error}"
                          for error in privacy_errors(path.read_text(encoding="utf-8")))
    assert errors == [], "\n".join(errors)
