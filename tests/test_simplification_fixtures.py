"""Validate the shared-invariant oracle, not model behavior or repair topology."""

from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from capture_eval import materialize


@pytest.mark.parametrize("variant", ["unfixed", "named_path_only", "shared_guard", "public_guards"])
def test_shared_balance_oracle_distinguishes_complete_repairs(tmp_path: Path, variant: str) -> None:
    fixture = tmp_path / "shared-balance"
    materialize("shared-balance", fixture)
    source = fixture / "ledger.py"
    original = source.read_text(encoding="utf-8")
    candidate = original
    if variant == "shared_guard":
        candidate = candidate.replace(
            "    balances[account] -= amount\n",
            "    if amount > balances[account]:\n"
            "        raise ValueError('insufficient balance')\n"
            "    balances[account] -= amount\n",
        )
    if variant in {"named_path_only", "public_guards"}:
        candidate = candidate.replace(
            "    _debit(balances, source, amount)\n",
            "    if amount > balances[source]:\n"
            "        raise ValueError('insufficient balance')\n"
            "    _debit(balances, source, amount)\n",
        )
    if variant == "public_guards":
        candidate = candidate.replace(
            "    _debit(balances, account, amount)\n",
            "    if amount > balances[account]:\n"
            "        raise ValueError('insufficient balance')\n"
            "    _debit(balances, account, amount)\n",
        )
    source.write_text(candidate, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/balance_checks.py"],
        cwd=fixture, capture_output=True, text=True, check=False, timeout=20,
    )
    if variant in {"unfixed", "named_path_only"}:
        assert result.returncode == 1, result.stdout + result.stderr
        assert "withdraw" in result.stdout
        if variant == "named_path_only":
            assert "FAILED tests/balance_checks.py::test_balance_boundary_is_shared_by_public_operations[101-transfer]" not in result.stdout
    else:
        assert result.returncode == 0, result.stdout + result.stderr
