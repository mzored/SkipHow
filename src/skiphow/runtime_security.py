"""Runtime security gates and durable redacted audit records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Mapping, Sequence

from .adapters.base import PermissionMode
from .security import (
    AuthorityGrant,
    FilesystemAccessError,
    FilesystemPolicy,
    Permission,
    PermissionProfile,
    ProtectedAction,
    SecretRedactor,
    check_permission,
    check_protected_action,
)
from .store import ConflictError, RunnerStore


AUDIT_APPEND_MAX_ATTEMPTS = 100
AUDIT_APPEND_MAX_BACKOFF_SECONDS = 0.02


@dataclass(frozen=True, slots=True)
class RuntimeSecurityDecision:
    allowed: bool
    reason: str
    profile: PermissionProfile
    required_permissions: tuple[Permission, ...]
    protected_actions: tuple[ProtectedAction, ...]


class RuntimeSecurityPolicy:
    """Resolve provider permissions against saved run authority and task facts."""

    def __init__(
        self,
        cwd: Path,
        *,
        filesystem: FilesystemPolicy | None = None,
    ) -> None:
        self.cwd = cwd.resolve()
        self.filesystem = filesystem or FilesystemPolicy(
            read_roots=(self.cwd,), write_roots=(self.cwd,)
        )

    def authorize(
        self,
        *,
        authority: Mapping[str, Any],
        constraints: Sequence[str],
        permission_mode: PermissionMode,
        outcome: str = "",
    ) -> RuntimeSecurityDecision:
        profile, error = _resolve_profile(authority, permission_mode)
        required_permissions, protected_actions, constraint_error = _requirements(
            constraints
        )
        protected_actions = tuple(
            dict.fromkeys((*protected_actions, *_classify_protected_actions(outcome)))
        )
        if error or constraint_error:
            return RuntimeSecurityDecision(
                False,
                error or constraint_error or "invalid security policy",
                profile,
                required_permissions,
                protected_actions,
            )

        if permission_mode is PermissionMode.FULL_ACCESS:
            return RuntimeSecurityDecision(
                False,
                "full-access provider mode bypasses the enforced filesystem boundary",
                profile,
                required_permissions,
                protected_actions,
            )
        expected_mode = (
            PermissionMode.WORKSPACE_WRITE
            if profile is PermissionProfile.WRITER
            else PermissionMode.READ_ONLY
        )
        if permission_mode is not expected_mode:
            return RuntimeSecurityDecision(
                False,
                f"{profile.value} profile requires {expected_mode.value} provider mode",
                profile,
                required_permissions,
                protected_actions,
            )

        implicit = [Permission.READ_FILES]
        if permission_mode is PermissionMode.WORKSPACE_WRITE:
            implicit.append(Permission.WRITE_FILES)
        all_permissions = tuple(dict.fromkeys((*implicit, *required_permissions)))
        for permission in all_permissions:
            decision = check_permission(profile, permission)
            if not decision.allowed:
                return RuntimeSecurityDecision(
                    False,
                    decision.reason,
                    profile,
                    all_permissions,
                    protected_actions,
                )
        try:
            self.filesystem.check(self.cwd, profile)
            if permission_mode is PermissionMode.WORKSPACE_WRITE:
                self.filesystem.check(self.cwd, profile, write=True)
        except FilesystemAccessError as exc:
            return RuntimeSecurityDecision(
                False,
                str(exc),
                profile,
                all_permissions,
                protected_actions,
            )

        grant, grant_error = _grant(authority)
        if grant_error:
            return RuntimeSecurityDecision(
                False,
                grant_error,
                profile,
                all_permissions,
                protected_actions,
            )
        for action in protected_actions:
            decision = check_protected_action(action, grant)
            if not decision.allowed:
                return RuntimeSecurityDecision(
                    False,
                    decision.reason,
                    profile,
                    all_permissions,
                    protected_actions,
                )
        return RuntimeSecurityDecision(
            True,
            "provider sandbox, filesystem root, permissions, and authority approved",
            profile,
            all_permissions,
            protected_actions,
        )


class DurableSecurityAudit:
    """Append redacted security decisions to the run's durable checkpoints."""

    def __init__(self, store: RunnerStore, redactor: SecretRedactor | None = None) -> None:
        self.store = store
        self.redactor = redactor or SecretRedactor()

    def append(
        self,
        run_id: str,
        *,
        actor: str,
        action: str,
        target: str,
        outcome: str,
        details: Mapping[str, Any] | None = None,
        task_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        event_time = timestamp or datetime.now(timezone.utc)
        if event_time.tzinfo is None:
            raise ValueError("audit timestamp must be timezone-aware")
        safe_fields = {
            "timestamp": event_time.isoformat(),
            "actor": self.redactor.redact_text(actor),
            "action": self.redactor.redact_text(action),
            "target": self.redactor.redact_text(target),
            "outcome": self.redactor.redact_text(outcome),
            "details": self.redactor.redact(dict(details or {})),
        }
        for attempt in range(AUDIT_APPEND_MAX_ATTEMPTS):
            prior = self.events(run_id)
            previous = prior[-1]["digest"] if prior else None
            payload = {
                "sequence": len(prior) + 1,
                **safe_fields,
                "previous_digest": previous,
            }
            payload["digest"] = _digest(payload)
            try:
                return self.store.append_security_audit(
                    run_id,
                    payload,
                    expected_sequence=len(prior),
                    expected_previous_digest=previous,
                    task_id=task_id,
                )
            except ConflictError:
                if attempt + 1 < AUDIT_APPEND_MAX_ATTEMPTS:
                    time.sleep(
                        min(
                            0.001 * (attempt + 1),
                            AUDIT_APPEND_MAX_BACKOFF_SECONDS,
                        )
                    )
        raise ConflictError("security audit head kept changing during append")

    def events(self, run_id: str) -> list[dict[str, Any]]:
        return self.store.list_security_audit(run_id)

    def verify(self, run_id: str) -> bool:
        previous: str | None = None
        for sequence, event in enumerate(self.events(run_id), 1):
            payload = {
                key: event.get(key)
                for key in (
                    "sequence",
                    "timestamp",
                    "actor",
                    "action",
                    "target",
                    "outcome",
                    "details",
                    "previous_digest",
                )
            }
            if (
                payload["sequence"] != sequence
                or payload["previous_digest"] != previous
                or event.get("digest") != _digest(payload)
            ):
                return False
            previous = str(event["digest"])
        return True


def protected_actions(constraints: Sequence[str]) -> tuple[ProtectedAction, ...]:
    return _requirements(constraints)[1]


_PROTECTED_OUTCOME_PATTERNS: tuple[tuple[ProtectedAction, re.Pattern[str]], ...] = (
    (
        ProtectedAction.PRODUCTION_DEPLOYMENT,
        re.compile(r"\b(?:deploy|deployment|rollout)\b.{0,48}\bproduction\b|\bproduction\b.{0,48}\b(?:deploy|deployment|rollout)\b", re.I),
    ),
    (
        ProtectedAction.PRODUCTION_DATABASE_MIGRATION,
        re.compile(r"\bproduction\b.{0,48}\b(?:database|db)\b.{0,32}\bmigrat(?:e|ion)\b|\bmigrat(?:e|ion)\b.{0,48}\bproduction\b.{0,32}\b(?:database|db)\b", re.I),
    ),
    (
        ProtectedAction.PAYMENT_OR_REFUND,
        re.compile(r"\b(?:issue|send|process|execute)\b.{0,32}\b(?:payment|refund)\b", re.I),
    ),
    (
        ProtectedAction.CREDENTIAL_CHANGE,
        re.compile(r"\b(?:change|rotate|replace|revoke)\b.{0,32}\b(?:credential|secret|api key|access token)s?\b", re.I),
    ),
    (
        ProtectedAction.PRIVACY_DATA_EXPORT,
        re.compile(r"\b(?:export|download)\b.{0,32}\b(?:personal|private|customer|user) data\b", re.I),
    ),
    (
        ProtectedAction.PRIVACY_DATA_DELETE,
        re.compile(r"\b(?:delete|erase|purge)\b.{0,32}\b(?:personal|private|customer|user) data\b", re.I),
    ),
    (
        ProtectedAction.IRREVERSIBLE_REMOTE_DELETE,
        re.compile(r"\b(?:permanently|irreversibly)\b.{0,32}\bdelete\b|\bdelete\b.{0,32}\b(?:remote|production)\b.{0,32}\b(?:resource|data|record)s?\b", re.I),
    ),
    (
        ProtectedAction.PUBLIC_RELEASE,
        re.compile(r"\b(?:publish|ship|make)\b.{0,32}\b(?:public release|release public|publicly available)\b|\brelease publicly\b", re.I),
    ),
    (
        ProtectedAction.PROTECTED_BRANCH_MERGE,
        re.compile(r"\bmerge\b.{0,32}\b(?:protected branch|main|master)\b", re.I),
    ),
)


def _classify_protected_actions(outcome: str) -> tuple[ProtectedAction, ...]:
    """Classify explicit mutation outcomes before provider dispatch."""
    if not isinstance(outcome, str):
        return ()
    return tuple(
        action for action, pattern in _PROTECTED_OUTCOME_PATTERNS if pattern.search(outcome)
    )


def _resolve_profile(
    authority: Mapping[str, Any], permission_mode: PermissionMode
) -> tuple[PermissionProfile, str | None]:
    configured = authority.get("permission_profile")
    if configured is None:
        profile = (
            PermissionProfile.WRITER
            if permission_mode is PermissionMode.WORKSPACE_WRITE
            else PermissionProfile.READ_ONLY
        )
        return profile, None
    try:
        profile = PermissionProfile(configured)
    except (TypeError, ValueError):
        return PermissionProfile.READ_ONLY, "authority has an invalid permission_profile"
    return profile, None


def _requirements(
    constraints: Sequence[str],
) -> tuple[tuple[Permission, ...], tuple[ProtectedAction, ...], str | None]:
    permissions: list[Permission] = []
    actions: list[ProtectedAction] = []
    for constraint in constraints:
        for prefix in ("permission:", "requires-permission:"):
            if constraint.startswith(prefix):
                try:
                    permissions.append(Permission(constraint.removeprefix(prefix)))
                except ValueError:
                    return (), (), f"unknown required permission in constraint: {constraint}"
        if constraint.startswith("protected-action:"):
            try:
                actions.append(
                    ProtectedAction(constraint.removeprefix("protected-action:"))
                )
            except ValueError:
                return (), (), f"unknown protected action in constraint: {constraint}"
    return tuple(dict.fromkeys(permissions)), tuple(dict.fromkeys(actions)), None


def _grant(
    authority: Mapping[str, Any],
) -> tuple[AuthorityGrant | None, str | None]:
    raw = authority.get("protected_actions")
    if raw is None:
        return None, None
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        return None, "authority protected_actions must be an array of action names"
    try:
        actions = frozenset(ProtectedAction(item) for item in raw)
    except ValueError:
        return None, "authority contains an unknown protected action"
    actor = authority.get("actor", "owner")
    source = authority.get("source", "request")
    if not isinstance(actor, str) or not actor.strip():
        return None, "authority actor must be a non-empty string"
    if not isinstance(source, str) or not source.strip():
        return None, "authority source must be a non-empty string"
    return AuthorityGrant(actor, actions, source), None


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
