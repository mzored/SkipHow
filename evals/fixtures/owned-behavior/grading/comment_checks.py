"""Grader-only checks for owned-rule-reused-for-new-guard. Run from the fixture root."""

from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from comments import post_comment

ROOT = Path.cwd()


@pytest.mark.parametrize("account", [
    {"id": "t1", "status": "terminated"},
    {"id": "t2", "status": "closed"},
    {"id": "t3", "status": "active", "closed_at": "2026-01-31"},
])
def test_behavior_terminated_accounts_cannot_comment(account):
    with pytest.raises(Exception):
        post_comment(account, "hello")


def test_structure_comment_guard_follows_the_owned_rule(tmp_path):
    # Extend the owner's rule in a scratch copy; a guard that calls it follows, a copied rule does not.
    copy = tmp_path / "project"
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns("grading", "tests", "__pycache__"))
    with (copy / "accounts.py").open("a", encoding="utf-8") as stream:
        stream.write(
            "\n\n_owned_rule = is_terminated\n\n\n"
            "def is_terminated(account):\n"
            "    return bool(account.get('banned')) or _owned_rule(account)\n"
        )
    probe = (
        "from comments import post_comment\n"
        "try:\n"
        "    post_comment({'id': 'b1', 'status': 'active', 'banned': True}, 'hello')\n"
        "except Exception:\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(1)\n"
    )
    result = subprocess.run([sys.executable, "-B", "-c", probe], cwd=copy, capture_output=True,
                            text=True, check=False, timeout=20)
    assert result.returncode == 0, "post_comment did not follow accounts.is_terminated"
