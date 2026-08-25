from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skiphow.security import (  # noqa: E402
    AuditLog,
    ArtifactProvenance,
    AuthorityGrant,
    ContentOrigin,
    FilesystemAccessError,
    FilesystemPolicy,
    OwnershipRegistry,
    Permission,
    PermissionProfile,
    ProtectedAction,
    ResourceKind,
    SecretRedactor,
    SupplyChainPolicy,
    check_instruction_authority,
    check_permission,
    check_protected_action,
)


def test_protected_action_requires_exact_explicit_grant() -> None:
    grant = AuthorityGrant(
        actor="owner",
        protected_actions=frozenset({ProtectedAction.PUBLIC_RELEASE}),
        source="saved-policy",
    )
    assert check_protected_action(ProtectedAction.PUBLIC_RELEASE, grant).allowed
    denied = check_protected_action(ProtectedAction.PROTECTED_BRANCH_MERGE, grant)
    assert not denied.allowed
    assert "does not grant" in denied.reason
    assert not check_protected_action(ProtectedAction.PAYMENT_OR_REFUND, None).allowed


@pytest.mark.parametrize(
    "origin",
    [
        ContentOrigin.REPOSITORY_CONTENT,
        ContentOrigin.TRACKER_CONTENT,
        ContentOrigin.WEB_CONTENT,
        ContentOrigin.TEST_OUTPUT,
        ContentOrigin.GENERATED_ARTIFACT,
        ContentOrigin.WORKER_SUMMARY,
    ],
)
def test_untrusted_content_cannot_grant_instruction_authority(origin: ContentOrigin) -> None:
    decision = check_instruction_authority(origin)
    assert not decision.allowed
    assert "evidence" in decision.reason


def test_supply_chain_policy_requires_source_and_exact_digest() -> None:
    digest = "a" * 64
    policy = SupplyChainPolicy(
        allowed_sources=frozenset({"approved-registry"}),
        expected_sha256={("runner", "1.2.3"): digest},
    )
    approved = ArtifactProvenance("runner", "1.2.3", "approved-registry", digest)
    changed = ArtifactProvenance("runner", "1.2.3", "approved-registry", "b" * 64)
    unpinned = ArtifactProvenance("runner", "1.2.4", "approved-registry", digest)
    assert policy.check(approved).allowed
    assert not policy.check(changed).allowed
    assert not policy.check(unpinned).allowed


def test_permission_profiles_deny_mutation_by_default() -> None:
    assert check_permission(PermissionProfile.WRITER, Permission.WRITE_FILES).allowed
    assert not check_permission(PermissionProfile.READ_ONLY, Permission.WRITE_FILES).allowed
    assert not check_permission(PermissionProfile.REVIEWER, Permission.MERGE).allowed
    assert check_permission(PermissionProfile.REVIEWER, Permission.REMOTE_READ).allowed
    assert not check_permission(PermissionProfile.READ_ONLY, Permission.REMOTE_READ).allowed


def test_filesystem_profiles_and_allowlist(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    worktree = workspace / "worktree"
    outside = tmp_path / "outside"
    worktree.mkdir(parents=True)
    outside.mkdir()
    policy = FilesystemPolicy(read_roots=(workspace,), write_roots=(worktree,))

    assert policy.check(worktree / "new.py", PermissionProfile.WRITER, write=True)
    with pytest.raises(FilesystemAccessError, match="cannot write"):
        policy.check(worktree / "new.py", PermissionProfile.REVIEWER, write=True)
    with pytest.raises(FilesystemAccessError, match="outside"):
        policy.check(outside / "stolen.py", PermissionProfile.WRITER, write=True)


def test_filesystem_allowlist_stops_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (workspace / "escape").symlink_to(outside, target_is_directory=True)
    policy = FilesystemPolicy(read_roots=(workspace,), write_roots=(workspace,))
    with pytest.raises(FilesystemAccessError, match="outside"):
        policy.check(workspace / "escape" / "file", PermissionProfile.WRITER, write=True)


def test_filesystem_allowlist_stops_broken_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (workspace / "escape").symlink_to(outside / "not-created")
    policy = FilesystemPolicy(read_roots=(workspace,), write_roots=(workspace,))
    with pytest.raises(FilesystemAccessError, match="outside"):
        policy.check(workspace / "escape", PermissionProfile.WRITER, write=True)


def test_cleanup_only_allows_resources_owned_by_requesting_run() -> None:
    registry = OwnershipRegistry()
    registry.register(
        ResourceKind.WORKTREE,
        "/temporary/worktree",
        "run-1",
        created_by_system=True,
    )
    registry.register(
        ResourceKind.BRANCH,
        "user-branch",
        "run-1",
        created_by_system=False,
    )
    assert registry.may_cleanup(
        ResourceKind.WORKTREE, "/temporary/worktree", requesting_run_id="run-1"
    ).allowed
    assert not registry.may_cleanup(
        ResourceKind.WORKTREE, "/temporary/worktree", requesting_run_id="run-2"
    ).allowed
    assert not registry.may_cleanup(
        ResourceKind.BRANCH, "user-branch", requesting_run_id="run-1"
    ).allowed


def test_redactor_covers_tokens_credentials_and_nested_secret_keys() -> None:
    redactor = SecretRedactor()
    payload = {
        "authorization": "Bearer abcdefghijklmnopqrstuvwxyz",
        "nested": {"password": "correct-horse", "message": "api_key=visible-no-more"},
        "url": "https://user:password@example.test/path",
    }
    safe = redactor.redact(payload)
    rendered = repr(safe)
    assert "abcdefghijklmnopqrstuvwxyz" not in rendered
    assert "correct-horse" not in rendered
    assert "visible-no-more" not in rendered
    assert "user:password" not in rendered
    assert rendered.count("[REDACTED]") >= 4


@pytest.mark.parametrize(
    "secret",
    [
        "sk-proj-abcdefghijklmnopqrstuv",
        "client_secret=abcdefghijklmnop",
        "refresh_token=abcdefghijklmnop",
        "secret_access_key=abcdefghijklmnop",
        "token=abcdefghijklmnop",
    ],
)
def test_redactor_covers_common_credential_forms(secret: str) -> None:
    assert secret not in SecretRedactor().redact_text(f"failure: {secret}")


def test_audit_log_redacts_and_hash_links_diagnostic_events() -> None:
    audit = AuditLog()
    first = audit.append(
        actor="controller",
        action="protected-action-check",
        target="release",
        outcome="denied",
        details={"reason": "missing authority", "access_token": "plain-secret"},
        timestamp=datetime(2026, 8, 25, tzinfo=timezone.utc),
    )
    second = audit.append(
        actor="controller",
        action="filesystem-check",
        target="/workspace/file",
        outcome="allowed",
    )
    assert first.details["access_token"] == "[REDACTED]"
    assert second.previous_digest == first.digest
    assert audit.verify()
