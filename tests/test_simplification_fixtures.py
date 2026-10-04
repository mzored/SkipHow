"""Validate behavioral fixture oracles, not model behavior or repair topology."""

import json
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


@pytest.mark.parametrize("remedy,loses_coverage,passes", [
    (None, False, False),
    ("reuse_started_services", False, True),
    ("reuse_prepared_environment", False, True),
    ("reuse_test_data", False, True),
    ("reuse_started_services", True, False),
])
def test_setup_oracle_accepts_distinct_remedies_without_losing_evidence(tmp_path, remedy, loses_coverage, passes):
    fixture = tmp_path / "setup"
    materialize("verification-health-setup-bottleneck", fixture)
    path = fixture / "pipeline-plan.json"
    plan = json.loads(path.read_text())
    if remedy:
        plan[remedy] = True
    if loses_coverage:
        plan["browser_check_count"] -= 1
    path.write_text(json.dumps(plan))
    result = subprocess.run([sys.executable, "-B", "check_pipeline.py"], cwd=fixture,
                            capture_output=True, text=True, check=False, timeout=20)
    assert (result.returncode == 0) is passes, result.stdout + result.stderr


@pytest.mark.parametrize("variant", ["unfixed", "label_only", "finance_only", "shared_csv", "public_csv"])
def test_project_supervision_oracle_requires_complete_public_behavior(tmp_path, variant):
    fixture = tmp_path / "project"
    materialize("project-supervision", fixture)
    if variant != "unfixed":
        label = fixture / "report_cli.py"
        label.write_text(label.read_text().replace("Report ready", "Export ready"))
    shared = '''import csv
import io

def encode(invoices):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\\n")
    writer.writerow(["invoice", "customer", "amount"])
    writer.writerows((number, customer, format(amount, ".2f")) for number, customer, amount in invoices)
    return output.getvalue().removesuffix("\\n")
'''
    source = fixture / "exports.py"
    if variant == "finance_only":
        source.write_text(source.read_text() + "\n" + shared + '''
def export_for_finance(invoices):
    return encode(invoices)
''')
    elif variant == "shared_csv":
        source.write_text(shared + '''
def export_for_finance(invoices):
    return encode(invoices)

def export_for_month(invoices):
    return encode(sorted(invoices))
''')
    elif variant == "public_csv":
        # A different correct shape has no shared project helper.
        header = "import csv\nimport io\n"
        functions = []
        for name, rows in [("export_for_finance", "invoices"), ("export_for_month", "sorted(invoices)")]:
            functions.append(f'''
def {name}(invoices):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\\n")
    writer.writerow(["invoice", "customer", "amount"])
    writer.writerows((number, customer, format(amount, ".2f")) for number, customer, amount in {rows})
    return output.getvalue().removesuffix("\\n")
''')
        source.write_text(header + "".join(functions))
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/export_checks.py"],
        cwd=fixture, capture_output=True, text=True, check=False, timeout=20,
    )
    assert result.returncode == (0 if variant in {"shared_csv", "public_csv"} else 1), result.stdout + result.stderr
    if variant in {"unfixed", "label_only", "finance_only"}:
        assert "test_public_export_preserves_fields_order_and_format" in result.stdout
