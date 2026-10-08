"""Host queue integration remains optional and precedes check execution budgets."""

import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("admitted_check", ROOT / "scripts/check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def test_off_host_runs_without_admission():
    with patch.object(check.shutil, "which", return_value=None), \
         patch.object(check.subprocess, "run", side_effect=AssertionError("unexpected subprocess")):
        assert check.host_admission([]) is None


@pytest.mark.parametrize("probe, expected", [(0, None), (78, 78), (-15, 78)])
def test_only_a_validated_live_grant_skips_the_queue(probe, expected):
    with patch.object(check.shutil, "which", return_value="adapter"), \
         patch.object(check.subprocess, "run", return_value=subprocess.CompletedProcess([], probe)) as run, \
         patch.object(check.os, "execv", side_effect=AssertionError("unexpected re-exec")):
        assert check.host_admission([]) == expected
        assert run.call_args.args[0] == ["adapter", "inherited", "--memory", "4", "--cpus", "4"]


def test_queue_replaces_the_process_before_execution_budgets_begin():
    class ReplacedProcess(BaseException):
        pass

    arguments = ["--pytest", "tests/test_checks.py", "-k", "two words"]
    with patch.object(check.shutil, "which", return_value="adapter"), \
         patch.object(check.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)) as run, \
         patch.object(check.os, "execv", side_effect=ReplacedProcess) as execute:
        with pytest.raises(ReplacedProcess):
            check.main(arguments)
        # No pytest subprocess, capture buffer or execution deadline exists while queued.
        assert run.call_count == 1
        command = execute.call_args.args[1]
        assert command[-len(arguments):] == arguments
        assert command[:9] == ["adapter", "--memory", "4", "--cpus", "4", "--timeout", "2700",
                              "--label", "skiphow-check"]


def test_discovered_broken_adapter_does_not_bypass_admission():
    with patch.object(check.shutil, "which", return_value="adapter"), \
         patch.object(check.subprocess, "run", side_effect=OSError("unavailable")):
        assert check.host_admission([]) == 78


@pytest.fixture
def adapter_directory():
    with tempfile.TemporaryDirectory(prefix="verification-admission-") as directory:
        yield Path(directory)


@pytest.mark.skipif(os.name != "posix", reason="POSIX exec and signal lifecycle")
def test_queued_adapter_status_and_cancellation_reach_the_caller(adapter_directory):
    """A real exec has no checker parent left to swallow status or retain a child."""
    adapter = adapter_directory / "agent-verify"
    marker = adapter_directory / "started"
    adapter.write_text(f"#!{sys.executable}\nimport os, pathlib, sys, time\n"
                       "if sys.argv[1] == 'inherited': sys.exit(1)\n"
                       "if os.environ.get('REFUSE'):\n    print('queued', flush=True)\n    sys.exit(75)\n"
                       f"pathlib.Path({str(marker)!r}).write_text(str(os.getpid()))\n"
                       "print('queued', flush=True)\n"
                       "time.sleep(60)\nraise AssertionError('queued command started')\n")
    adapter.chmod(0o755)
    environment = dict(os.environ, PATH=str(adapter_directory), REFUSE="1")
    command = [sys.executable, str(ROOT / "scripts/check.py"), "--pytest", "unused"]
    result = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=10)
    assert result.returncode == 75
    assert "queued" in result.stdout
    assert not marker.exists()
    environment.pop("REFUSE")
    process = subprocess.Popen(command, env=environment, stdout=subprocess.PIPE, text=True)
    try:
        assert process.stdout.readline().strip() == "queued"
        assert int(marker.read_text()) == process.pid
        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=10) == -signal.SIGTERM
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdout.close()
