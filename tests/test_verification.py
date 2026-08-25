from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skiphow.schemas import Task
from skiphow.verification import EnvironmentVerifier, VerificationConfigError


def task() -> Task:
    return Task.create("run", "Verify it", task_id="task")


def test_forbidden_mutation_is_derived_from_before_and_after_filesystem(
    tmp_path: Path,
) -> None:
    protected = tmp_path / "protected.txt"
    protected.write_text("before", encoding="utf-8")
    verifier = EnvironmentVerifier(
        tmp_path,
        {"task": {"forbidden_mutations": ["protected.txt"]}},
    )
    baseline = verifier.prepare(task())
    protected.write_text("after", encoding="utf-8")

    result = verifier.verify(task(), (), baseline)

    assert result.passed is False
    assert result.checks[0]["before"] != result.checks[0]["after"]


def test_command_timeout_fails_and_kills_the_process_group(tmp_path: Path) -> None:
    verifier_script = tmp_path / "verifier.py"
    verifier_script.write_text("import time; time.sleep(10)\n", encoding="utf-8")
    verifier = EnvironmentVerifier(
        tmp_path,
        {
            "task": {
                "commands": [
                    {
                        "argv": [sys.executable, "verifier.py"],
                        "trusted_artifacts": ["verifier.py"],
                        "timeout_seconds": 0.05,
                    }
                ]
            }
        },
    )

    result = verifier.verify(task(), (), verifier.prepare(task()))

    assert result.passed is False
    assert result.checks[0]["timed_out"] is True


@pytest.mark.parametrize(
    "spec, message",
    (
        ({"evidence": ["../secret"]}, "inside the project"),
        ({"commands": [{"argv": "pytest"}]}, "argv"),
        ({"commands": [{"argv": ["pytest"], "timeout_seconds": 301}]}, "between"),
        (
            {"commands": [{"argv": ["pytest"]}]},
            "trusted_artifacts",
        ),
        ({"unexpected": []}, "unknown verification"),
    ),
)
def test_plan_rejects_unsafe_or_unknown_configuration(
    tmp_path: Path, spec: dict[str, object], message: str
) -> None:
    with pytest.raises(VerificationConfigError, match=message):
        EnvironmentVerifier(tmp_path, {"task": spec})


def test_empty_task_contract_fails_closed(tmp_path: Path) -> None:
    verifier = EnvironmentVerifier(tmp_path, {})

    result = verifier.verify(task(), (), verifier.prepare(task()))

    assert result.passed is False
    assert result.checks[0]["kind"] == "configuration"


def test_provider_modified_verifier_artifact_is_not_executed(tmp_path: Path) -> None:
    script = tmp_path / "verify.py"
    marker = tmp_path / "executed"
    script.write_text("raise SystemExit(1)\n", encoding="utf-8")
    verifier = EnvironmentVerifier(
        tmp_path,
        {
            "task": {
                "commands": [
                    {
                        "argv": [sys.executable, "verify.py"],
                        "trusted_artifacts": ["verify.py"],
                    }
                ]
            }
        },
    )
    baseline = verifier.prepare(task())
    script.write_text(
        f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')\n",
        encoding="utf-8",
    )

    result = verifier.verify(task(), (), baseline)

    assert result.passed is False
    assert result.checks[0]["exit_code"] is None
    assert result.checks[0]["reason"] == "trusted artifact changed: verify.py"
    assert not marker.exists()


def test_command_uses_executable_resolved_before_provider_changes_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trusted_bin = tmp_path / "trusted-bin"
    provider_bin = tmp_path / "provider-bin"
    trusted_bin.mkdir()
    provider_bin.mkdir()
    trusted_command = trusted_bin / "verify-command"
    trusted_command.write_text("#!/bin/sh\nprintf trusted\n", encoding="utf-8")
    trusted_command.chmod(0o755)
    artifact = tmp_path / "verifier.lock"
    artifact.write_text("trusted", encoding="utf-8")
    monkeypatch.setenv("PATH", str(trusted_bin))
    verifier = EnvironmentVerifier(
        tmp_path,
        {
            "task": {
                "commands": [
                    {
                        "argv": ["verify-command"],
                        "trusted_artifacts": ["verifier.lock"],
                        "stdout_contains": "trusted",
                    }
                ]
            }
        },
    )
    baseline = verifier.prepare(task())
    malicious_command = provider_bin / "verify-command"
    malicious_command.write_text("#!/bin/sh\nprintf provider\n", encoding="utf-8")
    malicious_command.chmod(0o755)
    monkeypatch.setenv("PATH", str(provider_bin))

    result = verifier.verify(task(), (), baseline)

    assert result.passed is True
    assert result.checks[0]["stdout"] == "trusted"


def test_provider_modified_command_executable_is_not_run(tmp_path: Path) -> None:
    command = tmp_path / "verify-command"
    marker = tmp_path / "executed"
    command.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    command.chmod(0o755)
    artifact = tmp_path / "verifier.lock"
    artifact.write_text("trusted", encoding="utf-8")
    verifier = EnvironmentVerifier(
        tmp_path,
        {
            "task": {
                "commands": [
                    {
                        "argv": ["./verify-command"],
                        "trusted_artifacts": ["verifier.lock"],
                    }
                ]
            }
        },
    )
    baseline = verifier.prepare(task())
    command.write_text(
        f"#!/bin/sh\ntouch {str(marker)!r}\nexit 0\n", encoding="utf-8"
    )
    command.chmod(0o755)

    result = verifier.verify(task(), (), baseline)

    assert result.passed is False
    assert result.checks[0]["reason"] == "executable changed after provider execution"
    assert not marker.exists()
