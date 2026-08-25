#!/usr/bin/env python3
"""Run the small, opt-in SkipHow live evaluation suite.

``validate`` and ``plan`` are local manifest operations. ``run`` is the only
command that starts a host, and it refuses to do so until every live guard is
present. Receipts and trial directories always live outside the candidate.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    from . import collectors, hosts
    from .schema import Status, aggregate_status, load_suite
except ImportError:  # Direct execution is useful in a release checkout.
    import collectors
    import hosts
    from schema import Status, aggregate_status, load_suite


HERE = Path(__file__).resolve().parent
DEFAULT_SUITE = HERE / "suite.json"


class GateError(RuntimeError):
    pass


def _command(arguments: list[str], cwd: Path) -> str:
    try:
        environment = {"PATH": os.environ.get("PATH", ""), "GIT_CONFIG_NOSYSTEM": "1", "GIT_OPTIONAL_LOCKS": "0"}
        result = subprocess.run(
            ["git", "-c", "core.hooksPath=", "-c", "core.fsmonitor=false", *arguments],
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateError(str(exc)) from exc
    if result.returncode:
        raise GateError((result.stdout + result.stderr).strip() or "Git command failed")
    return result.stdout.strip()


def _hash(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _committed_payload(candidate: Path, prefix: str) -> list[dict[str, str]]:
    names = [name for name in _command(["ls-files", "--", prefix], candidate).splitlines() if name]
    if not names:
        raise GateError(f"candidate has no tracked {prefix} payload")
    hashes: list[dict[str, str]] = []
    for name in sorted(names):
        path = candidate / name
        if path.is_symlink() or not path.is_file():
            raise GateError(f"candidate payload entry is not a regular file: {name}")
        if _command(["hash-object", name], candidate) != _command(["rev-parse", f"HEAD:{name}"], candidate):
            raise GateError(f"candidate filesystem blob does not match HEAD: {name}")
        hashes.append({"path": name, "sha256": _hash(path)})
    untracked = _command(["ls-files", "--others", "--exclude-standard", "--", prefix], candidate)
    if untracked:
        raise GateError(f"candidate {prefix} payload contains untracked files")
    return hashes


def _aggregate_hash(hashes: list[dict[str, str]]) -> str:
    value = "".join(f"{item['path']}\0{item['sha256']}\n" for item in hashes)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def candidate_proof(candidate: Path) -> dict[str, Any]:
    """Return an exact committed-candidate identity without running its code."""
    candidate = candidate.resolve()
    if not candidate.is_dir():
        raise GateError("candidate checkout does not exist")
    if _command(["status", "--porcelain=v1"], candidate):
        raise GateError("candidate checkout is not clean")
    head = _command(["rev-parse", "HEAD"], candidate)
    tree = _command(["rev-parse", "HEAD^{tree}"], candidate)
    version_path = candidate / "VERSION"
    codex_manifest = candidate / "plugins/skiphow/.codex-plugin/plugin.json"
    claude_manifest = candidate / "plugins/skiphow/.claude-plugin/plugin.json"
    try:
        version = version_path.read_text(encoding="utf-8").strip()
        codex_version = json.loads(codex_manifest.read_text(encoding="utf-8"))["version"]
        claude_version = json.loads(claude_manifest.read_text(encoding="utf-8"))["version"]
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise GateError(f"cannot verify candidate version alignment: {exc}") from exc
    if not version or version != codex_version or version != claude_version:
        raise GateError("VERSION and host manifests are not aligned")
    if _command(["ls-files", "--error-unmatch", "VERSION"], candidate) != "VERSION":
        raise GateError("VERSION must belong to the committed candidate")
    plugin = candidate / "plugins/skiphow"
    tracked = {
        candidate / name
        for name in _command(["ls-files", "--", "plugins/skiphow"], candidate).splitlines()
        if name
    }
    actual = {path for path in plugin.rglob("*") if path.is_file() or path.is_symlink()}
    if not tracked or tracked != actual:
        raise GateError("candidate plugin payload must contain tracked files only")
    hashes = []
    for path in sorted(tracked):
        if path.is_symlink():
            raise GateError(f"candidate plugin contains a symlink: {path.relative_to(candidate)}")
        if path.is_file():
            relative = path.relative_to(candidate).as_posix()
            if _command(["hash-object", relative], candidate) != _command(["rev-parse", f"HEAD:{relative}"], candidate):
                raise GateError(f"candidate filesystem blob does not match HEAD: {relative}")
            hashes.append({"path": relative, "sha256": _hash(path)})
    if _command(["hash-object", "VERSION"], candidate) != _command(["rev-parse", "HEAD:VERSION"], candidate):
        raise GateError("candidate VERSION blob does not match HEAD")
    evaluation_hashes = _committed_payload(candidate, "evals/live")
    suite_hash = next((item["sha256"] for item in evaluation_hashes if item["path"] == "evals/live/suite.json"), None)
    if suite_hash is None:
        raise GateError("canonical live suite is absent from the committed candidate")
    return {
        "head": head,
        "tree": tree,
        "version": version,
        "manifest_versions": {"codex": codex_version, "claude": claude_version},
        "plugin_files": hashes,
        "plugin_aggregate_sha256": _aggregate_hash(hashes),
        "evaluation_aggregate_sha256": _aggregate_hash(evaluation_hashes),
        "suite_sha256": suite_hash,
    }


def _positive_decimal(value: str | None, name: str) -> Decimal:
    try:
        decimal = Decimal(value or "")
    except InvalidOperation as exc:
        raise GateError(f"{name} must be an explicit positive decimal") from exc
    if not decimal.is_finite() or decimal <= 0:
        raise GateError(f"{name} must be an explicit positive decimal")
    return decimal


def _outside(candidate: Path, root: Path, label: str) -> Path:
    candidate, root = candidate.resolve(), root.resolve()
    if root == candidate or root.is_relative_to(candidate) or candidate.is_relative_to(root):
        raise GateError(f"{label} must be outside the candidate checkout")
    return root


def _safe_name(value: str) -> str:
    return "".join(character if character.isalnum() or character in "._-" else "_" for character in value)


def _private_directory(path: Path, *, exclusive: bool = False) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=not exclusive)
    try:
        path.chmod(0o700)
    except OSError:
        pass


def _write_json(path: Path, value: Any) -> None:
    _private_directory(path.parent)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _redact(value: str, secrets: Iterable[str]) -> str:
    result = value
    for secret in secrets:
        if secret:
            result = result.replace(secret, "[REDACTED]")
    return result


def _redact_value(value: Any, secrets: Iterable[str]) -> Any:
    if isinstance(value, str):
        return _redact(value, secrets)
    if isinstance(value, list):
        return [_redact_value(item, secrets) for item in value]
    if isinstance(value, tuple):
        return [_redact_value(item, secrets) for item in value]
    if isinstance(value, dict):
        return {_redact(str(key), secrets): _redact_value(item, secrets) for key, item in value.items()}
    return value


def _write_receipt(path: Path, value: Any, secrets: Iterable[str]) -> None:
    _write_json(path, _redact_value(value, secrets))


def _events(stdout: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def _copy_fixture(source: Path, destination: Path) -> None:
    collectors.plain_directory(source)
    shutil.copytree(source, destination, symlinks=False)
    collectors.plain_directory(destination)


def _contained(root: Path, relative: str, label: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise GateError(f"{label} escapes its trusted root")
    return path


def _selected(suite: dict[str, Any], requested: list[str]) -> list[dict[str, Any]]:
    scenarios = suite["scenarios"]
    if not requested:
        return scenarios
    by_id = {item["id"]: item for item in scenarios}
    unknown = set(requested) - set(by_id)
    if unknown:
        raise GateError("unknown scenario: " + ", ".join(sorted(unknown)))
    return [by_id[identifier] for identifier in requested]


def _github_repo(remote: str) -> str:
    value = remote.removesuffix(".git")
    if "github.com:" in value:
        return value.rsplit("github.com:", 1)[1]
    if "github.com/" in value:
        return value.rsplit("github.com/", 1)[1]
    raise GateError("candidate origin is not a GitHub repository")


def _gh_json(endpoint: str, *, cwd: Path, environment: dict[str, str], allow_missing: bool = False) -> Any:
    try:
        result = subprocess.run(["gh", "api", "--method", "GET", endpoint], cwd=cwd, env=environment, capture_output=True, text=True, timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateError(f"GitHub read failed: {exc}") from exc
    if result.returncode and allow_missing and "HTTP 404" in result.stderr:
        return None
    if result.returncode:
        raise GateError(f"GitHub read failed for {endpoint}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GateError(f"GitHub returned invalid JSON for {endpoint}") from exc
    return value


def _github_environment(token: str) -> dict[str, str]:
    environment = {
        name: os.environ[name]
        for name in ("PATH", "LANG", "LC_ALL", "TMPDIR", "SSL_CERT_FILE", "SSL_CERT_DIR")
        if os.environ.get(name)
    }
    environment["GH_TOKEN"] = token
    return environment


def _public_repository_id(repository: str) -> int:
    """Resolve a public candidate without granting the sandbox token access to it."""
    request = Request(
        f"https://api.github.com/repos/{repository}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "skiphow-live-eval"},
    )
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed GitHub API origin.
            value = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
        raise GateError("candidate repository ID is unavailable from the public GitHub API") from exc
    identifier = value.get("id") if isinstance(value, dict) else None
    if not isinstance(identifier, int):
        raise GateError("candidate repository ID is missing")
    return identifier


def _validate_github_installation(
    installation: Any,
    inventory: Any,
    *,
    repository: str,
    repository_id: int,
) -> dict[str, Any]:
    if not isinstance(installation, dict) or installation.get("repository_selection") != "selected":
        raise GateError("GitHub App installation must use selected-repository access")
    permissions = installation.get("permissions")
    if not isinstance(permissions, dict):
        raise GateError("GitHub installation permission preflight returned no permissions")
    allowed_write = {"contents", "issues", "pull_requests"}
    write_permissions = {name for name, value in permissions.items() if str(value).lower() in {"write", "admin"}}
    if write_permissions != allowed_write:
        raise GateError("GitHub App write access must be exactly contents, issues, and pull requests")
    repositories = inventory.get("repositories", []) if isinstance(inventory, dict) else []
    if not isinstance(inventory, dict) or inventory.get("total_count") != 1 or len(repositories) != 1:
        raise GateError("GitHub App token must access exactly one repository")
    selected = [
        item
        for item in repositories
        if isinstance(item, dict) and item.get("id") == repository_id and item.get("full_name") == repository
    ]
    if len(selected) != 1:
        raise GateError("installation token does not select exactly the named GitHub sandbox repository")
    return permissions


def _github_preflight(args: argparse.Namespace, candidate: Path, secrets: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not args.confirm_github_sandbox or not args.confirm_github_mutation:
        raise GateError("GitHub trials require --confirm-github-sandbox and --confirm-github-mutation")
    if not args.github_sandbox_path or not args.github_sandbox_repo or not args.github_token_env or not args.github_expected_state:
        raise GateError("GitHub trials require sandbox path, repository name, token environment name, and expected-state file")
    token = os.environ.get(args.github_token_env)
    if not token:
        raise GateError("GitHub token environment variable is unset or empty")
    secrets.append(token)
    sandbox = Path(args.github_sandbox_path).resolve()
    if sandbox == candidate or sandbox.is_relative_to(candidate) or candidate.is_relative_to(sandbox):
        raise GateError("GitHub sandbox must differ from the candidate checkout")
    for root, label in ((Path(args.work_root).resolve(), "work root"), (Path(args.receipt_root).resolve(), "receipt root")):
        if sandbox == root or sandbox.is_relative_to(root) or root.is_relative_to(sandbox):
            raise GateError(f"GitHub sandbox must not contain or be contained by the {label}")
    if not (sandbox / ".git").is_dir():
        raise GateError("GitHub sandbox must be an existing clone")
    if _command(["status", "--porcelain=v1"], sandbox):
        raise GateError("GitHub sandbox clone is not clean")
    remote = _command(["remote", "get-url", "origin"], sandbox)
    if _github_repo(remote).lower() != args.github_sandbox_repo.lower():
        raise GateError("GitHub sandbox repository name does not match origin")
    candidate_remote = _command(["remote", "get-url", "origin"], candidate)
    candidate_repo = _github_repo(candidate_remote)
    if args.github_sandbox_repo.lower() == candidate_repo.lower():
        raise GateError("GitHub sandbox repository must differ from the candidate repository")
    # This fixed endpoint works only for a GitHub App installation token. It is a
    # narrow permission preflight, not a collector and never creates a repository.
    environment = _github_environment(token)
    installation = _gh_json("/installation", cwd=sandbox, environment=environment)
    inventory = _gh_json("/installation/repositories", cwd=sandbox, environment=environment)
    sandbox_state = _gh_json(f"/repos/{args.github_sandbox_repo}", cwd=sandbox, environment=environment)
    sandbox_id = sandbox_state.get("id")
    if not isinstance(sandbox_id, int):
        raise GateError("GitHub sandbox repository ID is missing")
    permissions = _validate_github_installation(
        installation,
        inventory,
        repository=args.github_sandbox_repo,
        repository_id=sandbox_id,
    )
    candidate_id = _public_repository_id(candidate_repo)
    if sandbox_id == candidate_id:
        raise GateError("GitHub sandbox repository ID matches the candidate repository")
    expected_path = Path(args.github_expected_state).resolve()
    if expected_path == candidate or expected_path.is_relative_to(candidate) or candidate.is_relative_to(expected_path):
        raise GateError("GitHub expected-state file must be outside the candidate checkout")
    try:
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read GitHub expected state: {exc}") from exc
    marker = expected.get("run_marker") if isinstance(expected, dict) else None
    if not isinstance(marker, dict):
        raise GateError("GitHub expected state needs a run_marker")
    operation = marker.get("operation")
    issues = marker.get("issues")
    checks = marker.get("required_checks")
    branch_prefix = marker.get("branch_prefix")
    if not isinstance(operation, str) or not operation or not isinstance(issues, list) or len(issues) < 2 or any(not isinstance(item, int) or item <= 0 for item in issues):
        raise GateError("GitHub run_marker needs an operation and at least two Issue numbers")
    if not isinstance(checks, list) or not checks or any(not isinstance(item, str) or not item for item in checks):
        raise GateError("GitHub run_marker needs required check names")
    if not isinstance(branch_prefix, str) or not branch_prefix:
        raise GateError("GitHub run_marker needs a system-owned branch prefix")
    issue_states = [
        _gh_json(f"/repos/{args.github_sandbox_repo}/issues/{number}", cwd=sandbox, environment=environment)
        for number in issues
    ]
    if any(
        not isinstance(item, dict)
        or "pull_request" in item
        or item.get("state") != "open"
        or operation not in str(item.get("body") or "")
        for item in issue_states
    ):
        raise GateError("selected GitHub items must be open Issues carrying the unique operation marker")
    existing_prs = _gh_json(
        f"/repos/{args.github_sandbox_repo}/pulls?state=all&sort=updated&direction=desc&per_page=100",
        cwd=sandbox,
        environment=environment,
    )
    if not isinstance(existing_prs, list) or len(existing_prs) >= 100:
        raise GateError("GitHub preflight cannot prove a complete pull-request inventory")
    if any(operation in str(item.get("body") or "") for item in existing_prs if isinstance(item, dict)):
        raise GateError("GitHub operation marker already belongs to a pull request")
    initial_branches = _gh_json(f"/repos/{args.github_sandbox_repo}/branches?per_page=100", cwd=sandbox, environment=environment)
    if not isinstance(initial_branches, list) or len(initial_branches) >= 100:
        raise GateError("GitHub preflight cannot prove a complete branch inventory")
    branch_names = [str(item.get("name") or "") for item in initial_branches if isinstance(item, dict)]
    if any(name.startswith(branch_prefix) for name in branch_names):
        raise GateError("GitHub sandbox already contains a branch with the owned prefix")
    worktrees = _command(["worktree", "list", "--porcelain"], sandbox)
    if worktrees.count("worktree ") != 1:
        raise GateError("GitHub sandbox must start with one clean worktree")
    normalized_marker = {"operation": operation, "issues": issues, "required_checks": checks, "branch_prefix": branch_prefix}
    generated_expected = {
        "repository_id": sandbox_id,
        "issue_count": len(issues),
        "all_selected_are_issues": True,
        "all_issues_closed": True,
        "pull_request_count_at_least": 1,
        "all_pull_requests_merged": True,
        "all_closing_links_present": True,
        "all_required_checks_passed": True,
        "all_head_repositories_match": True,
        "all_owned_branches_deleted": True,
        "operation_marker_present": True,
    }
    return (
        {
            "sandbox_path": str(sandbox),
            "sandbox_repo": args.github_sandbox_repo,
            "sandbox_repo_id": sandbox_id,
            "candidate_repo_id": candidate_id,
            "installation_permissions": permissions,
            "installation_token_preflight": "passed",
            "run_marker": normalized_marker,
            "base_branch": _command(["branch", "--show-current"], sandbox),
            "pre_state": {
                "head": _command(["rev-parse", "HEAD"], sandbox),
                "issues": [{"number": item.get("number"), "state": item.get("state")} for item in issue_states],
                "operation_pull_request_count": 0,
                "owned_prefix_branches": [],
            },
        },
        generated_expected,
    )


def _fetch_github_snapshot(sandbox: Path, repository: str, token: str, marker: dict[str, Any], destination: Path) -> None:
    """Read the named sandbox only after the host exits. It cannot mutate GitHub."""
    environment = _github_environment(token)
    repository_state = _gh_json(f"/repos/{repository}", cwd=sandbox, environment=environment)
    issue_states = [_gh_json(f"/repos/{repository}/issues/{number}", cwd=sandbox, environment=environment) for number in marker["issues"]]
    recent = _gh_json(f"/repos/{repository}/pulls?state=all&sort=updated&direction=desc&per_page=100", cwd=sandbox, environment=environment)
    if not isinstance(recent, list) or len(recent) >= 100:
        raise GateError("GitHub collector cannot prove a complete pull-request inventory")
    pull_requests = [item for item in recent if isinstance(item, dict) and marker["operation"] in str(item.get("body") or "") and str(item.get("head", {}).get("ref", "")).startswith(marker["branch_prefix"])]
    normalized_prs = []
    for item in pull_requests:
        number = item.get("number")
        detail = _gh_json(f"/repos/{repository}/pulls/{number}", cwd=sandbox, environment=environment)
        head = detail.get("head", {}).get("sha")
        checks = _gh_json(f"/repos/{repository}/commits/{head}/check-runs?per_page=100", cwd=sandbox, environment=environment)
        check_runs = checks.get("check_runs", []) if isinstance(checks, dict) else []
        if (
            not isinstance(checks, dict)
            or not isinstance(check_runs, list)
            or checks.get("total_count") != len(check_runs)
            or len(check_runs) >= 100
        ):
            raise GateError("GitHub collector cannot prove a complete check-run inventory")
        accepted_conclusions = {"success", "skipped", "neutral"}
        required_checks_passed = all(
            bool(matching := [
                entry
                for entry in check_runs
                if isinstance(entry, dict) and entry.get("head_sha") == head and entry.get("name") == name
            ])
            and all(entry.get("conclusion") in accepted_conclusions for entry in matching)
            for name in marker["required_checks"]
        )
        branch_name = quote(str(detail.get("head", {}).get("ref", "")), safe="")
        branch = _gh_json(f"/repos/{repository}/branches/{branch_name}", cwd=sandbox, environment=environment, allow_missing=True)
        body = str(detail.get("body") or "")
        linked = [number for number in marker["issues"] if re.search(rf"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#?{number}\b", body)]
        normalized_prs.append(
            {
                "number": number,
                "merged_at": detail.get("merged_at"),
                "head_sha": head,
                "head_repository_matches": detail.get("head", {}).get("repo", {}).get("full_name") == repository,
                "operation_marker_present": marker["operation"] in body,
                "closing_issues": linked,
                "required_checks_passed": required_checks_passed,
                "branch_exists": branch is not None,
            }
        )
    linked_issues = {number for item in normalized_prs for number in item["closing_issues"]}
    remote_branches = _gh_json(f"/repos/{repository}/branches?per_page=100", cwd=sandbox, environment=environment)
    if not isinstance(remote_branches, list) or len(remote_branches) >= 100:
        raise GateError("GitHub collector cannot prove a complete branch inventory")
    owned_remote_branches = [
        str(item.get("name") or "")
        for item in remote_branches
        if isinstance(item, dict) and str(item.get("name") or "").startswith(marker["branch_prefix"])
    ]
    snapshot = {
        "repository_id": repository_state.get("id"),
        "issue_count": len(issue_states),
        "all_selected_are_issues": all("pull_request" not in item for item in issue_states),
        "all_issues_closed": all(item.get("state") == "closed" for item in issue_states),
        "pull_request_count": len(normalized_prs),
        "all_pull_requests_merged": bool(normalized_prs) and all(item["merged_at"] for item in normalized_prs),
        "all_closing_links_present": set(marker["issues"]) <= linked_issues,
        "all_required_checks_passed": bool(normalized_prs) and all(item["required_checks_passed"] for item in normalized_prs),
        "all_head_repositories_match": bool(normalized_prs) and all(item["head_repository_matches"] for item in normalized_prs),
        "all_owned_branches_deleted": bool(normalized_prs) and not owned_remote_branches and all(not item["branch_exists"] for item in normalized_prs),
        "operation_marker_present": (
            bool(normalized_prs)
            and all(item["operation_marker_present"] for item in normalized_prs)
            and all(marker["operation"] in str(item.get("body") or "") for item in issue_states)
        ),
        "pull_requests": normalized_prs,
        "owned_remote_branches": owned_remote_branches,
        "issues": [{"number": item.get("number"), "state": item.get("state")} for item in issue_states],
    }
    _write_json(destination, snapshot)


def _run_assertions(oracle: dict[str, Any], workspace: Path, before: dict[str, Any], structured_before: dict[str, str], events: list[dict[str, Any]], receipt_root: Path, github_expected: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for assertion in oracle.get("assertions", []):
        collector = assertion.get("collector")
        if collector == "tree_delta":
            result = collectors.tree_delta(before, workspace)
            unchanged = not (result["added"] or result["removed"] or result["modified"])
            passed = unchanged if assertion.get("unchanged") else all(
                set(assertion.get(f"required_{field}", [])) <= set(result[field])
                for field in ("added", "removed", "modified")
            )
            for field in ("added", "removed", "modified"):
                observed = set(result[field])
                allowed = assertion.get(f"allowed_{field}")
                forbidden = set(assertion.get(f"forbidden_{field}", []))
                if allowed is not None and not observed <= set(allowed):
                    passed = False
                if observed & forbidden:
                    passed = False
            content_mismatches = []
            for relative, expected in assertion.get("expected_text", {}).items():
                path = _contained(workspace, relative, "expected text path")
                try:
                    actual = path.read_text(encoding="utf-8")
                except OSError:
                    actual = None
                if actual != expected:
                    content_mismatches.append(relative)
            if content_mismatches:
                passed = False
            result["content_mismatches"] = content_mismatches
            result["status"] = (Status.PASSED if passed else Status.FAILED).value
        elif collector == "structured_file":
            path = _contained(workspace, assertion["path"], "structured file path")
            previous = structured_before.get(assertion["path"], "")
            result = collectors.structured_file(
                path,
                kind=assertion["kind"],
                before=previous,
                expected_count=assertion.get("expected_count"),
                expected=assertion.get("expected"),
                expected_added_records=assertion.get("expected_added_records"),
                relationships=assertion.get("relationships"),
            )
        elif collector == "host_event":
            result = collectors.host_event(
                events,
                event_type=assertion.get("event_type"),
                event_types=assertion.get("event_types"),
                fields=assertion.get("fields"),
                absent=assertion.get("absent", False),
            )
        elif collector == "git_state":
            result = collectors.git_state(workspace)
            if assertion.get("clean") is True and result.get("porcelain") != []:
                result["status"] = Status.FAILED.value
            if assertion.get("one_worktree") is True and result.get("worktree_count") != 1:
                result["status"] = Status.FAILED.value
            if assertion.get("branch") is not None and result.get("branch") != assertion["branch"]:
                result["status"] = Status.FAILED.value
            prefix = assertion.get("forbidden_branch_prefix")
            if prefix and any(str(branch).startswith(prefix) for branch in result.get("local_branches") or []):
                result["status"] = Status.FAILED.value
        elif collector == "github_state":
            snapshot = _contained(receipt_root, assertion.get("snapshot", "github-state.json"), "GitHub snapshot path")
            result = collectors.github_state(snapshot, expected=github_expected)
        elif collector == "provider_usage":
            result = collectors.provider_usage(events)
        else:
            result = {"collector": str(collector), "status": Status.UNVERIFIED.value, "detail": "unsupported collector in oracle"}
        result["assertion"] = assertion.get("id", collector)
        result["required"] = assertion.get("required", True)
        evidence.append(result)
    return evidence


def gate(
    args: argparse.Namespace,
    scenarios: list[dict[str, Any]],
    call_count: int | None = None,
) -> tuple[Path, Decimal, Decimal, list[str]]:
    if not args.confirm_live:
        raise GateError("live execution requires the exact --confirm-live flag")
    total = _positive_decimal(args.total_budget_usd, "--total-budget-usd")
    per_trial = _positive_decimal(args.per_invocation_budget_usd, "--per-invocation-budget-usd")
    calls = call_count if call_count is not None else len(scenarios)
    if total < per_trial * calls:
        raise GateError("total budget must cover every planned host invocation")
    if not args.model or not args.effort:
        raise GateError("live execution requires explicit --model and --effort")
    if args.host == "codex" and not args.accept_advisory_codex_budget:
        raise GateError("Codex budget is advisory; pass --accept-advisory-codex-budget to continue")
    credential_name = args.credential_env or hosts.CREDENTIAL_ENV[args.host]
    if credential_name != hosts.CREDENTIAL_ENV[args.host]:
        raise GateError(f"{args.host} requires credential environment name {hosts.CREDENTIAL_ENV[args.host]}")
    credential = os.environ.get(credential_name)
    if not credential:
        raise GateError("host credential environment variable is unset or empty")
    candidate = Path(args.candidate).resolve()
    work_root = _outside(candidate, Path(args.work_root), "work root")
    receipt_root = _outside(candidate, Path(args.receipt_root), "receipt root")
    if work_root == receipt_root or work_root.is_relative_to(receipt_root) or receipt_root.is_relative_to(work_root):
        raise GateError("work root and receipt root must be separate")
    for root, label in ((work_root, "work root"), (receipt_root, "receipt root")):
        if not root.is_dir() or root.is_symlink():
            raise GateError(f"{label} must be an existing ordinary directory")
        if (root / ".git").exists():
            raise GateError(f"{label} must not be a repository")
    return candidate, total, per_trial, [credential]


def _write_text(path: Path, value: str) -> None:
    _private_directory(path.parent)
    path.write_text(value, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateError(f"{label} must be an object")
    return value


def _structured_baseline(oracle: dict[str, Any], workspace: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for assertion in oracle.get("assertions", []):
        if assertion.get("collector") != "structured_file":
            continue
        relative = assertion["path"]
        path = _contained(workspace, relative, "structured baseline path")
        result[relative] = path.read_text(encoding="utf-8") if path.exists() else ""
    return result


def _unverified_assertions(oracle: dict[str, Any], detail: str) -> list[dict[str, Any]]:
    return [
        {
            "assertion": assertion.get("id", assertion.get("collector")),
            "collector": assertion.get("collector"),
            "required": assertion.get("required", True),
            "status": Status.UNVERIFIED.value,
            "detail": detail,
        }
        for assertion in oracle.get("assertions", [])
    ]


def _host_call(
    args: argparse.Namespace,
    *,
    candidate: Path,
    proof: dict[str, Any],
    workspace: Path,
    prompt: str,
    call_root: Path,
    receipt_root: Path,
    explicit_skill: bool,
    network: bool,
    per_call_budget: Decimal,
    budget: dict[str, Any],
    secrets: list[str],
    github_token: str | None = None,
) -> dict[str, Any]:
    _private_directory(call_root, exclusive=True)
    _private_directory(receipt_root, exclusive=True)
    receipt_secrets = [
        *secrets,
        str(candidate),
        str(workspace),
        str(call_root),
        str(receipt_root),
        str(args.codex_marketplace_source or ""),
    ]
    credential = os.environ[args.credential_env or hosts.CREDENTIAL_ENV[args.host]]
    if budget["observed_spend"] >= budget["total"]:
        result = {
            "status": Status.BLOCKED.value,
            "detail": "observed spend reached the total budget before this invocation",
            "events": [],
            "usage": {"status": Status.UNVERIFIED.value, "cost_status": Status.UNVERIFIED.value},
        }
        _write_receipt(receipt_root / "call.json", {key: value for key, value in result.items() if key != "events"}, receipt_secrets)
        return result
    try:
        _, environment = hosts.fresh_config(
            args.host,
            call_root,
            credential=credential,
            github_token=github_token,
        )
        install = hosts.install_candidate(
            args.host,
            candidate,
            environment,
            version=proof["version"],
            codex_source=args.codex_marketplace_source,
        )
        if candidate_proof(candidate) != proof:
            raise hosts.HostError("candidate payload changed during installation")
    except (hosts.HostError, GateError) as exc:
        result = {
            "status": Status.BLOCKED.value,
            "detail": _redact(str(exc), receipt_secrets),
            "events": [],
            "usage": {"status": Status.UNVERIFIED.value, "cost_status": Status.UNVERIFIED.value},
        }
        _write_receipt(receipt_root / "call.json", {key: value for key, value in result.items() if key != "events"}, receipt_secrets)
        return result
    _write_receipt(receipt_root / "install.json", install, receipt_secrets)
    try:
        command, exit_code, stdout, stderr = hosts.invoke(
            args.host,
            workspace,
            prompt,
            args.model,
            args.effort,
            str(per_call_budget),
            environment,
            candidate=candidate,
            explicit_skill=explicit_skill,
            network=network,
        )
        process_status = Status.PASSED if exit_code == 0 else Status.FAILED
        detail = None if exit_code == 0 else "host process exited unsuccessfully"
    except hosts.HostError as exc:
        command, exit_code, stdout, stderr = [], None, "", str(exc)
        process_status = Status.FAILED
        detail = str(exc)
    try:
        if candidate_proof(candidate) != proof:
            raise GateError("candidate payload changed during the host invocation")
    except GateError as exc:
        process_status = Status.FAILED
        detail = str(exc)
    redacted_stdout = _redact(stdout, receipt_secrets)
    redacted_stderr = _redact(stderr, receipt_secrets)
    _write_text(receipt_root / "events.ndjson", redacted_stdout)
    _write_text(receipt_root / "stderr.txt", redacted_stderr)
    events = _events(stdout)
    events.append({"type": "host_process", "exit_code": exit_code})
    usage = collectors.provider_usage(events)
    if usage.get("cost_status") == Status.PASSED.value and usage.get("cost_usd") is not None:
        budget["observed_spend"] += Decimal(str(usage["cost_usd"]))
        if budget["observed_spend"] > budget["total"]:
            process_status = Status.FAILED
            detail = "host-reported spend exceeded the total budget"
    result = {
        "status": process_status.value,
        "detail": _redact(detail, receipt_secrets) if detail is not None else None,
        "exit_code": exit_code,
        "requested_model": args.model,
        "requested_effort": args.effort,
        "observed_effort": None,
        "usage": usage,
        "events": events,
        "command": command,
    }
    _write_receipt(
        receipt_root / "call.json",
        {key: value for key, value in result.items() if key not in {"events", "command"}},
        receipt_secrets,
    )
    return result


def _finish_trial(
    *,
    scenario: dict[str, Any],
    trial_index: int,
    arm: str,
    workspace: Path,
    receipt_root: Path,
    oracle: dict[str, Any],
    before: dict[str, Any],
    structured_before: dict[str, str],
    calls: list[dict[str, Any]],
    started: float,
    secrets: list[str],
    github_expected: dict[str, Any] | None = None,
) -> dict[str, Any]:
    process_status = aggregate_status([call["status"] for call in calls])
    events = [event for call in calls for event in call.get("events", [])]
    if process_status == Status.BLOCKED:
        evidence = _unverified_assertions(oracle, "a host precondition blocked the trial before outcome collection")
    else:
        try:
            evidence = _run_assertions(oracle, workspace, before, structured_before, events, receipt_root, github_expected)
        except (GateError, ValueError, OSError, KeyError) as exc:
            evidence = _unverified_assertions(oracle, f"collector failed safely: {exc}")
            process_status = Status.FAILED
    required = [item["status"] for item in evidence if item.get("required", True)]
    outcome_status = aggregate_status(required)
    status = aggregate_status([process_status, outcome_status])
    usage = collectors.provider_usage(events)
    result = {
        "scenario": scenario["id"],
        "trial_index": trial_index,
        "arm": arm,
        "status": status.value,
        "outcome_status": outcome_status.value,
        "process_status": process_status.value,
        "metrics_status": usage.get("status", Status.UNVERIFIED.value),
        "duration_seconds": round(time.time() - started, 3),
        "assertions": evidence,
        "usage": usage,
        "calls": [{key: value for key, value in call.items() if key not in {"events", "command"}} for call in calls],
    }
    _write_receipt(receipt_root / "receipt.json", result, [*secrets, str(workspace), str(receipt_root)])
    return result


def _finalize_trial_claims(result: dict[str, Any]) -> None:
    """Keep outcome evidence separate from broader workflow claims."""
    excluded = {"status", "outcome_status", "process_status", "metrics_status", "claim_status"}
    auxiliary = {
        key: value
        for key, value in result.items()
        if key.endswith("_status") and key not in excluded and value in {item.value for item in Status}
    }
    result["claim_status"] = aggregate_status([result["status"], *auxiliary.values()]).value
    result["limitations"] = sorted(key for key, value in auxiliary.items() if value == Status.UNVERIFIED.value)


def _route_prompt(route_map: dict[str, Any], arm: str) -> str:
    if arm == "adaptive":
        mapping = route_map
    else:
        deep_model = route_map["DEEP"]["model"]
        mapping = {tier: {"model": deep_model, "effort": route_map[tier]["effort"]} for tier in ("FAST", "STANDARD", "DEEP")}
    return (
        "\n\nEvaluator-controlled routing map for this arm:\n"
        + json.dumps(mapping, sort_keys=True)
        + "\nUse these model IDs only for delegated roles when the host exposes model selection. Keep the root model and root effort unchanged."
    )


def _plain_trial(
    args: argparse.Namespace,
    *,
    scenario: dict[str, Any],
    trial_index: int,
    arm: str,
    candidate: Path,
    proof: dict[str, Any],
    work_run: Path,
    receipt_run: Path,
    per_call_budget: Decimal,
    budget: dict[str, Any],
    secrets: list[str],
    route_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started = time.time()
    trial_root = work_run / scenario["id"] / arm / str(trial_index)
    receipt_root = receipt_run / "trials" / scenario["id"] / arm / str(trial_index)
    _private_directory(trial_root, exclusive=True)
    _private_directory(receipt_root, exclusive=True)
    workspace = trial_root / "workspace"
    _copy_fixture(_contained(HERE, scenario["fixture"], "fixture"), workspace)
    before = collectors.file_inventory(workspace)
    oracle = _load_json(_contained(HERE, scenario["oracle"], "oracle"), "scenario oracle")
    structured_before = _structured_baseline(oracle, workspace)
    prompt = _contained(HERE, scenario["prompt"], "prompt").read_text(encoding="utf-8")
    if route_map is not None:
        prompt += _route_prompt(route_map, arm)
    calls = [
        _host_call(
            args,
            candidate=candidate,
            proof=proof,
            workspace=workspace,
            prompt=prompt,
            call_root=trial_root / "host-1",
            receipt_root=receipt_root / "calls" / "1",
            explicit_skill=scenario["explicit_skill"],
            network=False,
            per_call_budget=per_call_budget,
            budget=budget,
            secrets=secrets,
        )
    ]
    checkpoint_status = None
    if scenario["execution"] == "restart" and calls[0]["status"] == Status.PASSED.value:
        checkpoint = _load_json(_contained(HERE, scenario["checkpoint_oracle"], "checkpoint oracle"), "checkpoint oracle")
        try:
            checkpoint_evidence = _run_assertions(checkpoint, workspace, before, structured_before, calls[0]["events"], receipt_root)
            checkpoint_status = aggregate_status([item["status"] for item in checkpoint_evidence if item.get("required", True)])
        except (GateError, ValueError, OSError, KeyError) as exc:
            checkpoint_status = Status.FAILED
            checkpoint_evidence = _unverified_assertions(
                checkpoint,
                f"checkpoint collector failed safely: {exc}",
            )
        _write_receipt(
            receipt_root / "checkpoint.json",
            {"status": checkpoint_status.value, "assertions": checkpoint_evidence},
            [*secrets, str(workspace), str(receipt_root)],
        )
        if checkpoint_status == Status.PASSED:
            resume_prompt = _contained(HERE, scenario["resume_prompt"], "resume prompt").read_text(encoding="utf-8")
            calls.append(
                _host_call(
                    args,
                    candidate=candidate,
                    proof=proof,
                    workspace=workspace,
                    prompt=resume_prompt,
                    call_root=trial_root / "host-2",
                    receipt_root=receipt_root / "calls" / "2",
                    explicit_skill=scenario["explicit_skill"],
                    network=False,
                    per_call_budget=per_call_budget,
                    budget=budget,
                    secrets=secrets,
                )
            )
        else:
            calls.append({"status": Status.FAILED.value, "detail": "phase-one checkpoint did not match the external oracle", "events": [], "usage": {"status": Status.UNVERIFIED.value}})
    result = _finish_trial(
        scenario=scenario,
        trial_index=trial_index,
        arm=arm,
        workspace=workspace,
        receipt_root=receipt_root,
        oracle=oracle,
        before=before,
        structured_before=structured_before,
        calls=calls,
        started=started,
        secrets=secrets,
    )
    if scenario["execution"] == "restart":
        result["restart_reconstruction_status"] = (
            Status.PASSED.value
            if checkpoint_status == Status.PASSED and len(calls) == 2 and result["outcome_status"] == Status.PASSED.value
            else result["status"]
        )
        result["host_session_resume_status"] = Status.UNVERIFIED.value
        result["compaction_status"] = Status.UNVERIFIED.value
        _write_receipt(receipt_root / "receipt.json", result, [*secrets, str(workspace), str(receipt_root)])
    if not scenario["explicit_skill"]:
        result["implicit_skill_loading_status"] = Status.UNVERIFIED.value
        _write_receipt(receipt_root / "receipt.json", result, [*secrets, str(workspace), str(receipt_root)])
    if scenario["id"] == "nontechnical-owner":
        result["technical_question_semantics_status"] = Status.UNVERIFIED.value
        _write_receipt(receipt_root / "receipt.json", result, [*secrets, str(workspace), str(receipt_root)])
    if scenario["id"] == "reuse-feature":
        result["research_quality_status"] = Status.UNVERIFIED.value
    _finalize_trial_claims(result)
    _write_receipt(receipt_root / "receipt.json", result, [*secrets, str(workspace), str(receipt_root)])
    return result


def _github_trial(
    args: argparse.Namespace,
    *,
    scenario: dict[str, Any],
    candidate: Path,
    proof: dict[str, Any],
    work_run: Path,
    receipt_run: Path,
    per_call_budget: Decimal,
    budget: dict[str, Any],
    secrets: list[str],
    github: dict[str, Any],
    github_expected: dict[str, Any],
) -> dict[str, Any]:
    started = time.time()
    trial_root = work_run / scenario["id"] / "github" / "1"
    receipt_root = receipt_run / "trials" / scenario["id"] / "github" / "1"
    _private_directory(trial_root, exclusive=True)
    _private_directory(receipt_root, exclusive=True)
    workspace = Path(github["sandbox_path"])
    oracle = _load_json(_contained(HERE, scenario["oracle"], "oracle"), "scenario oracle")
    marker = github["run_marker"]
    for assertion in oracle.get("assertions", []):
        if assertion.get("collector") == "git_state":
            assertion["branch"] = github["base_branch"]
            assertion["forbidden_branch_prefix"] = marker["branch_prefix"]
    prompt = _contained(HERE, scenario["prompt"], "prompt").read_text(encoding="utf-8")
    prompt += (
        "\n\nEvaluator authority and scope:\n"
        f"- Repository: {github['sandbox_repo']}\n"
        f"- Issues: {', '.join('#' + str(number) for number in marker['issues'])}\n"
        f"- Stable operation marker: {marker['operation']}\n"
        f"- Owned branch prefix: {marker['branch_prefix']}\n"
        f"- Required checks: {', '.join(marker['required_checks'])}\n"
        "- Grant: complete these Issues end to end, including guarded merge and safe cleanup.\n"
    )
    call = _host_call(
        args,
        candidate=candidate,
        proof=proof,
        workspace=workspace,
        prompt=prompt,
        call_root=trial_root / "host-1",
        receipt_root=receipt_root / "calls" / "1",
        explicit_skill=True,
        network=True,
        per_call_budget=per_call_budget,
        budget=budget,
        secrets=secrets,
        github_token=os.environ[args.github_token_env],
    )
    if call["status"] != Status.BLOCKED.value:
        try:
            _fetch_github_snapshot(
                workspace,
                github["sandbox_repo"],
                os.environ[args.github_token_env],
                marker,
                receipt_root / "github-state.json",
            )
        except GateError as exc:
            call["status"] = Status.FAILED.value
            call["detail"] = str(exc)
    result = _finish_trial(
        scenario=scenario,
        trial_index=1,
        arm="github",
        workspace=workspace,
        receipt_root=receipt_root,
        oracle=oracle,
        before={},
        structured_before={},
        calls=[call],
        started=started,
        secrets=secrets,
        github_expected=github_expected,
    )
    result["out_of_scope_remote_mutations_status"] = Status.UNVERIFIED.value
    result["premerge_exact_head_sequence_status"] = Status.UNVERIFIED.value
    result["required_review_observation_status"] = Status.UNVERIFIED.value
    _finalize_trial_claims(result)
    _write_receipt(receipt_root / "receipt.json", result, [*secrets, str(workspace), str(receipt_root)])
    return result


def _load_route_map(args: argparse.Namespace, candidate: Path) -> dict[str, Any]:
    if not args.route_map:
        raise GateError("paired routing trials require --route-map")
    path = Path(args.route_map).resolve()
    if path == candidate or path.is_relative_to(candidate):
        raise GateError("route map must stay outside the candidate checkout")
    value = _load_json(path, "route map")
    if set(value) != {"FAST", "STANDARD", "DEEP"}:
        raise GateError("route map must define FAST, STANDARD, and DEEP")
    for tier, route in value.items():
        if not isinstance(route, dict) or not isinstance(route.get("model"), str) or not route["model"] or not isinstance(route.get("effort"), str) or not route["effort"]:
            raise GateError(f"route map entry {tier} needs a model and effort")
    if value["FAST"]["model"] == value["DEEP"]["model"] and value["STANDARD"]["model"] == value["DEEP"]["model"]:
        raise GateError("adaptive route map must differ from the all-DEEP baseline")
    return value


def _routing_comparison(trials: list[dict[str, Any]], route_map: dict[str, Any] | None, requested_trials: int) -> dict[str, Any] | None:
    routed = [item for item in trials if item["scenario"] == "adaptive-vs-all-deep"]
    if not routed or route_map is None:
        return None
    adaptive = [item for item in routed if item["arm"] == "adaptive"]
    baseline = [item for item in routed if item["arm"] == "all-deep"]
    outcomes_pass = len(adaptive) == len(baseline) == requested_trials and all(
        item.get("status") == Status.PASSED.value and item.get("outcome_status") == Status.PASSED.value for item in routed
    )
    cost_complete = all(item["usage"].get("cost_status") == Status.PASSED.value for item in routed)
    expected_adaptive = {
        (tier, route_map[tier]["model"], route_map[tier]["effort"])
        for tier in ("FAST", "STANDARD")
    }
    expected_baseline = {
        (tier, route_map["DEEP"]["model"], route_map[tier]["effort"])
        for tier in ("FAST", "STANDARD")
    }

    def observed_routes(item: dict[str, Any]) -> set[tuple[str, str, str]]:
        return {
            (route["tier"], route["model"], route["effort"])
            for route in item["usage"].get("delegated_routes", [])
            if isinstance(route, dict) and {"tier", "model", "effort"} <= set(route)
        }

    route_models_observed = all(observed_routes(item) == expected_adaptive for item in adaptive) and all(
        observed_routes(item) == expected_baseline for item in baseline
    )
    requested_roots = {
        (call.get("requested_model"), call.get("requested_effort"))
        for item in routed
        for call in item.get("calls", [])[:1]
    }
    root_routes_observed = (
        len(requested_roots) == 1
        and None not in next(iter(requested_roots), ())
        and all(
            (item["usage"].get("root_route") or {}).get("model") == next(iter(requested_roots))[0]
            and (item["usage"].get("root_route") or {}).get("effort") == next(iter(requested_roots))[1]
            for item in routed
        )
    )
    complete_subagent_cost = all(item["usage"].get("includes_subagents") is True for item in routed)
    adaptive_cost = sum((Decimal(item["usage"]["cost_usd"]) for item in adaptive if item["usage"].get("cost_usd") is not None), Decimal("0"))
    baseline_cost = sum((Decimal(item["usage"]["cost_usd"]) for item in baseline if item["usage"].get("cost_usd") is not None), Decimal("0"))
    claimable = requested_trials >= 3 and outcomes_pass and cost_complete and root_routes_observed and route_models_observed and complete_subagent_cost
    return {
        "paired_trials": requested_trials,
        "outcomes_preserved": outcomes_pass,
        "route_models_observed": route_models_observed,
        "root_route_observed": root_routes_observed,
        "complete_subagent_cost_observed": complete_subagent_cost,
        "adaptive_cost_usd": str(adaptive_cost) if cost_complete else None,
        "all_deep_cost_usd": str(baseline_cost) if cost_complete else None,
        "descriptive_delta_usd": str(adaptive_cost - baseline_cost) if cost_complete else None,
        "claim_status": (Status.PASSED if claimable and adaptive_cost < baseline_cost else Status.UNVERIFIED).value,
        "claim_scope": "cost ablation under the operator-controlled route map",
        "autonomous_selection_status": Status.UNVERIFIED.value,
    }


def run_live(args: argparse.Namespace) -> int:
    if Path(args.suite).resolve() != DEFAULT_SUITE.resolve():
        raise GateError("live release runs require the canonical evals/live/suite.json")
    if Path(args.candidate).resolve() != HERE.parents[1].resolve():
        raise GateError("the live evaluator must run from the candidate checkout it grades")
    suite = load_suite(DEFAULT_SUITE)
    selected = _selected(suite, args.scenario)
    if any(item["execution"] == "github" for item in selected):
        raise GateError(
            "mutable GitHub evaluation is UNVERIFIED: this harness cannot both permit Git metadata writes and technically prevent repository deletion"
        )
    if args.trials < 1:
        raise GateError("--trials must be a positive integer")
    if any(item["host"] not in {"either", args.host} for item in selected):
        raise GateError("selected scenario does not support the requested host")
    if any(item["execution"] == "github" for item in selected) and args.trials != 1:
        raise GateError("the mutable GitHub scenario supports exactly one trial per pre-provisioned sandbox")
    calls_per_trial = {"single": 1, "github": 1, "restart": 2, "paired": 2}
    call_count = sum(calls_per_trial[item["execution"]] for item in selected) * args.trials
    candidate, total_budget, per_call_budget, secrets = gate(args, selected, call_count)
    proof = candidate_proof(candidate)
    route_map = _load_route_map(args, candidate) if any(item["execution"] == "paired" for item in selected) else None
    github = None
    github_expected = None
    if any(item["execution"] == "github" for item in selected):
        github, github_expected = _github_preflight(args, candidate, secrets)
    host_identity = hosts.identity(args.host)
    started = time.time()
    run_id = _safe_name(time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + proof["head"][:12] + "-" + uuid.uuid4().hex)
    work_run = Path(args.work_root).resolve() / run_id
    receipt_run = Path(args.receipt_root).resolve() / run_id
    if work_run.exists() or receipt_run.exists():
        raise GateError("live run directory collision")
    _private_directory(work_run, exclusive=True)
    _private_directory(receipt_run, exclusive=True)
    budget: dict[str, Any] = {"total": total_budget, "observed_spend": Decimal("0")}
    trials: list[dict[str, Any]] = []
    for trial_index in range(1, args.trials + 1):
        for scenario in selected:
            if scenario["execution"] == "github":
                assert github is not None and github_expected is not None
                trials.append(
                    _github_trial(
                        args,
                        scenario=scenario,
                        candidate=candidate,
                        proof=proof,
                        work_run=work_run,
                        receipt_run=receipt_run,
                        per_call_budget=per_call_budget,
                        budget=budget,
                        secrets=secrets,
                        github=github,
                        github_expected=github_expected,
                    )
                )
            elif scenario["execution"] == "paired":
                assert route_map is not None
                arms = ("adaptive", "all-deep") if trial_index % 2 else ("all-deep", "adaptive")
                for arm in arms:
                    trials.append(
                        _plain_trial(
                            args,
                            scenario=scenario,
                            trial_index=trial_index,
                            arm=arm,
                            candidate=candidate,
                            proof=proof,
                            work_run=work_run,
                            receipt_run=receipt_run,
                            per_call_budget=per_call_budget,
                            budget=budget,
                            secrets=secrets,
                            route_map=route_map,
                        )
                    )
            else:
                trials.append(
                    _plain_trial(
                        args,
                        scenario=scenario,
                        trial_index=trial_index,
                        arm="restart" if scenario["execution"] == "restart" else "default",
                        candidate=candidate,
                        proof=proof,
                        work_run=work_run,
                        receipt_run=receipt_run,
                        per_call_budget=per_call_budget,
                        budget=budget,
                        secrets=secrets,
                    )
                )
    routing = _routing_comparison(trials, route_map, args.trials)
    if candidate_proof(candidate) != proof:
        raise GateError("candidate payload changed before the final receipt")
    claim_inputs = [item.get("claim_status", item["status"]) for item in trials]
    if routing is not None:
        claim_inputs.append(routing["claim_status"])
        claim_inputs.append(routing["autonomous_selection_status"])
    limitations = [
        {
            "scenario": item["scenario"],
            "trial_index": item["trial_index"],
            "arm": item["arm"],
            "claims": item.get("limitations", []),
        }
        for item in trials
        if item.get("limitations")
    ]
    if routing is not None and routing["claim_status"] != Status.PASSED.value:
        limitations.append({"scenario": "adaptive-vs-all-deep", "claim": "paired routing savings", "status": routing["claim_status"]})
    if routing is not None:
        limitations.append({"scenario": "adaptive-vs-all-deep", "claim": "autonomous route selection", "status": routing["autonomous_selection_status"]})
    run_receipt: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "candidate": proof,
        "host": {**host_identity, "credential_env": args.credential_env or hosts.CREDENTIAL_ENV[args.host]},
        "requested": {
            "root_model": args.model,
            "root_effort": args.effort,
            "total_budget_usd": str(total_budget),
            "per_invocation_budget_usd": str(per_call_budget),
            "budget_mode": "advisory" if args.host == "codex" else "host-enforced-per-invocation",
            "trials": args.trials,
        },
        "github": {key: value for key, value in (github or {}).items() if key != "sandbox_path"} or None,
        "trials": trials,
        "routing_comparison": routing,
        "observed_cost_usd": str(budget["observed_spend"]) if budget["observed_spend"] else None,
        "cost_observation_status": (
            Status.PASSED.value
            if all(item["usage"].get("cost_status") == Status.PASSED.value for item in trials)
            else Status.UNVERIFIED.value
        ),
        "duration_seconds": round(time.time() - started, 3),
        "status": aggregate_status([item["status"] for item in trials]).value,
        "claim_status": aggregate_status(claim_inputs).value,
        "limitations": limitations,
    }
    _write_receipt(
        receipt_run / "receipt.json",
        run_receipt,
        [*secrets, str(candidate), str(work_run), str(receipt_run), str(args.work_root), str(args.receipt_root)],
    )
    print(
        json.dumps(
            {"status": run_receipt["status"], "claim_status": run_receipt["claim_status"], "receipt": str(receipt_run / "receipt.json")},
            sort_keys=True,
        )
    )
    return 0 if run_receipt["status"] == run_receipt["claim_status"] == Status.PASSED.value else 1


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    for name in ("validate", "plan"):
        item = sub.add_parser(name)
        item.add_argument("--suite", default=str(DEFAULT_SUITE))
    run = sub.add_parser("run")
    run.add_argument("--suite", default=str(DEFAULT_SUITE))
    run.add_argument("--candidate", required=True)
    run.add_argument("--host", required=True, choices=("codex", "claude"))
    run.add_argument("--model", required=True)
    run.add_argument("--effort", required=True)
    run.add_argument("--credential-env")
    run.add_argument("--total-budget-usd", required=True)
    run.add_argument("--per-invocation-budget-usd", required=True)
    run.add_argument("--work-root", required=True)
    run.add_argument("--receipt-root", required=True)
    run.add_argument("--scenario", action="append", default=[])
    run.add_argument("--trials", type=int, default=1, help="repeat every selected scenario")
    run.add_argument("--confirm-live", action="store_true")
    run.add_argument("--accept-advisory-codex-budget", action="store_true")
    run.add_argument("--codex-marketplace-source")
    run.add_argument("--route-map", help="operator-owned FAST/STANDARD/DEEP JSON used only by paired routing trials")
    run.add_argument("--github-sandbox-path")
    run.add_argument("--github-sandbox-repo")
    run.add_argument("--github-token-env")
    run.add_argument("--github-expected-state")
    run.add_argument("--confirm-github-sandbox", action="store_true")
    run.add_argument("--confirm-github-mutation", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "run":
            return run_live(args)
        suite = load_suite(Path(args.suite))
        if args.command == "validate":
            print(json.dumps({"status": Status.PASSED.value, "scenarios": [item["id"] for item in suite["scenarios"]]}, sort_keys=True))
            return 0
        if args.command == "plan":
            print(json.dumps({"status": Status.UNVERIFIED.value, "live_execution": False, "scenarios": [item["id"] for item in suite["scenarios"]]}, sort_keys=True))
            return 0
        raise GateError("unsupported evaluator command")
    except (GateError, hosts.HostError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": Status.BLOCKED.value, "detail": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
