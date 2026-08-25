"""Authority, filesystem, redaction, ownership, and audit enforcement."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


class PermissionProfile(str, Enum):
    READ_ONLY = "read-only"
    WRITER = "writer"
    REVIEWER = "reviewer"


@dataclass(frozen=True)
class PermissionSet:
    read_files: bool
    write_files: bool
    network: bool
    remote_read: bool
    remote_mutation: bool
    merge: bool
    credentials: bool


PROFILE_PERMISSIONS: Mapping[PermissionProfile, PermissionSet] = {
    PermissionProfile.READ_ONLY: PermissionSet(True, False, False, False, False, False, False),
    PermissionProfile.WRITER: PermissionSet(True, True, False, False, False, False, False),
    PermissionProfile.REVIEWER: PermissionSet(True, False, True, True, False, False, False),
}


class Permission(str, Enum):
    READ_FILES = "read-files"
    WRITE_FILES = "write-files"
    NETWORK = "network"
    REMOTE_READ = "remote-read"
    REMOTE_MUTATION = "remote-mutation"
    MERGE = "merge"
    CREDENTIALS = "credentials"


_PERMISSION_FIELDS = {
    Permission.READ_FILES: "read_files",
    Permission.WRITE_FILES: "write_files",
    Permission.NETWORK: "network",
    Permission.REMOTE_READ: "remote_read",
    Permission.REMOTE_MUTATION: "remote_mutation",
    Permission.MERGE: "merge",
    Permission.CREDENTIALS: "credentials",
}


def check_permission(profile: PermissionProfile, permission: Permission) -> AuthorizationDecision:
    allowed = bool(getattr(PROFILE_PERMISSIONS[profile], _PERMISSION_FIELDS[permission]))
    if allowed:
        return AuthorizationDecision(True, f"{profile.value} profile grants {permission.value}")
    return AuthorizationDecision(False, f"{profile.value} profile denies {permission.value}")


class ProtectedAction(str, Enum):
    PRODUCTION_DEPLOYMENT = "production-deployment"
    PRODUCTION_DATABASE_MIGRATION = "production-database-migration"
    PAYMENT_OR_REFUND = "payment-or-refund"
    CREDENTIAL_CHANGE = "credential-change"
    PRIVACY_DATA_EXPORT = "privacy-data-export"
    PRIVACY_DATA_DELETE = "privacy-data-delete"
    IRREVERSIBLE_REMOTE_DELETE = "irreversible-remote-delete"
    PUBLIC_RELEASE = "public-release"
    PROTECTED_BRANCH_MERGE = "protected-branch-merge"


class ContentOrigin(str, Enum):
    """Origin labels used instead of trying to detect prompt injection by wording."""

    OWNER_REQUEST = "owner-request"
    SAVED_POLICY = "saved-policy"
    REPOSITORY_CONTENT = "repository-content"
    TRACKER_CONTENT = "tracker-content"
    WEB_CONTENT = "web-content"
    TEST_OUTPUT = "test-output"
    GENERATED_ARTIFACT = "generated-artifact"
    WORKER_SUMMARY = "worker-summary"


@dataclass(frozen=True)
class AuthorityGrant:
    """Explicit grants from the owner or saved repository policy."""

    actor: str
    protected_actions: frozenset[ProtectedAction] = frozenset()
    source: str = "request"


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str


def check_protected_action(
    action: ProtectedAction,
    grant: AuthorityGrant | None,
) -> AuthorizationDecision:
    """Deny protected actions unless an explicit grant names the exact action."""

    if grant is None:
        return AuthorizationDecision(False, f"{action.value} requires explicit authority")
    if action not in grant.protected_actions:
        return AuthorizationDecision(
            False, f"{grant.source} does not grant {action.value} authority"
        )
    return AuthorizationDecision(True, f"{action.value} authorized by {grant.source}")


def check_instruction_authority(origin: ContentOrigin) -> AuthorizationDecision:
    """Treat external and generated text as evidence, never as new authority."""

    if origin in {ContentOrigin.OWNER_REQUEST, ContentOrigin.SAVED_POLICY}:
        return AuthorizationDecision(True, f"{origin.value} may provide instructions")
    return AuthorizationDecision(False, f"{origin.value} is untrusted evidence, not authority")


@dataclass(frozen=True)
class ArtifactProvenance:
    """Facts required before executing a downloaded dependency or tool."""

    name: str
    version: str
    source: str
    sha256: str | None
    signature_verified: bool = False


@dataclass(frozen=True)
class SupplyChainPolicy:
    allowed_sources: frozenset[str]
    expected_sha256: Mapping[tuple[str, str], str] = field(default_factory=dict)
    require_signature: bool = False

    def check(self, artifact: ArtifactProvenance) -> AuthorizationDecision:
        if artifact.source not in self.allowed_sources:
            return AuthorizationDecision(False, "artifact source is not allowed")
        expected = self.expected_sha256.get((artifact.name, artifact.version))
        if expected is None:
            return AuthorizationDecision(False, "artifact version has no pinned digest")
        if artifact.sha256 is None or not re.fullmatch(r"[a-fA-F0-9]{64}", artifact.sha256):
            return AuthorizationDecision(False, "artifact has no valid SHA-256 digest")
        if not hmac.compare_digest(expected.lower(), artifact.sha256.lower()):
            return AuthorizationDecision(False, "artifact digest does not match the pin")
        if self.require_signature and not artifact.signature_verified:
            return AuthorizationDecision(False, "artifact signature is not verified")
        return AuthorizationDecision(True, "artifact source and digest match policy")


class FilesystemAccessError(PermissionError):
    pass


@dataclass(frozen=True)
class FilesystemPolicy:
    """Resolved allowlists for one worker or controller process."""

    read_roots: tuple[Path, ...]
    write_roots: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "read_roots", self._normalize_roots(self.read_roots))
        object.__setattr__(self, "write_roots", self._normalize_roots(self.write_roots))
        for root in self.write_roots:
            if not any(self._inside(root, read_root) for read_root in self.read_roots):
                raise ValueError("every write root must also be inside a read root")

    @staticmethod
    def _normalize_roots(roots: Iterable[Path]) -> tuple[Path, ...]:
        normalized = tuple(Path(root).resolve(strict=False) for root in roots)
        if not normalized:
            return ()
        return tuple(dict.fromkeys(normalized))

    @staticmethod
    def _inside(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
        except ValueError:
            return False
        return True

    @staticmethod
    def _resolved_target(path: Path) -> Path:
        """Resolve existing ancestors too, so symlinks cannot escape the allowlist."""

        target = Path(path)
        missing: list[str] = []
        cursor = target
        while not cursor.exists() and not cursor.is_symlink() and cursor != cursor.parent:
            missing.append(cursor.name)
            cursor = cursor.parent
        resolved = cursor.resolve(strict=False)
        for component in reversed(missing):
            resolved = resolved / component
        return resolved

    def check(self, path: Path, profile: PermissionProfile, *, write: bool = False) -> Path:
        permissions = PROFILE_PERMISSIONS[profile]
        if write and not permissions.write_files:
            raise FilesystemAccessError(f"{profile.value} profile cannot write files")
        if not write and not permissions.read_files:
            raise FilesystemAccessError(f"{profile.value} profile cannot read files")
        target = self._resolved_target(path)
        roots = self.write_roots if write else self.read_roots
        if not any(self._inside(target, root) for root in roots):
            operation = "write" if write else "read"
            raise FilesystemAccessError(f"{operation} target is outside the filesystem allowlist")
        return target


class ResourceKind(str, Enum):
    WORKTREE = "worktree"
    BRANCH = "branch"
    TEMPORARY_FILE = "temporary-file"
    REMOTE_RECORD = "remote-record"


@dataclass(frozen=True)
class OwnedResource:
    kind: ResourceKind
    identifier: str
    owner_run_id: str
    created_by_system: bool
    registered_at: datetime


class OwnershipRegistry:
    """Cleanup authority for resources created and registered by SkipHow."""

    def __init__(self) -> None:
        self._resources: dict[tuple[ResourceKind, str], OwnedResource] = {}

    def register(
        self,
        kind: ResourceKind,
        identifier: str,
        owner_run_id: str,
        *,
        created_by_system: bool,
        registered_at: datetime | None = None,
    ) -> OwnedResource:
        if not identifier.strip() or not owner_run_id.strip():
            raise ValueError("identifier and owner_run_id must be non-empty")
        key = (kind, identifier)
        if key in self._resources:
            raise ValueError("resource is already registered")
        resource = OwnedResource(
            kind,
            identifier,
            owner_run_id,
            created_by_system,
            registered_at or datetime.now(timezone.utc),
        )
        if resource.registered_at.tzinfo is None:
            raise ValueError("registered_at must be timezone-aware")
        self._resources[key] = resource
        return resource

    def may_cleanup(
        self, kind: ResourceKind, identifier: str, *, requesting_run_id: str
    ) -> AuthorizationDecision:
        resource = self._resources.get((kind, identifier))
        if resource is None:
            return AuthorizationDecision(False, "resource is not in the ownership registry")
        if not resource.created_by_system:
            return AuthorizationDecision(False, "resource predates or belongs outside SkipHow")
        if resource.owner_run_id != requesting_run_id:
            return AuthorizationDecision(False, "resource belongs to another run")
        return AuthorizationDecision(True, "resource is system-owned by the requesting run")

    def release(self, kind: ResourceKind, identifier: str, *, requesting_run_id: str) -> None:
        decision = self.may_cleanup(kind, identifier, requesting_run_id=requesting_run_id)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        del self._resources[(kind, identifier)]

    def resources(self) -> tuple[OwnedResource, ...]:
        return tuple(self._resources.values())


class SecretRedactor:
    """Redact common credentials while preserving enough context for diagnosis."""

    _patterns = (
        re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----", re.DOTALL),
        re.compile(r"\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]{16,}\b"),
        re.compile(r"\b(?:sk|rk|pk)-(?:live|test|proj)-[A-Za-z0-9_-]{12,}\b"),
        re.compile(r"\b(?:Bearer\s+)[A-Za-z0-9._~+/=-]{12,}\b", re.IGNORECASE),
        re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
        re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
        re.compile(
            r"(?i)(\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|refresh[_-]?token|client[_-]?secret|secret[_-]?access[_-]?key|password|passwd|secret|token)\b\s*[:=]\s*)([^\s,;]+)"
        ),
        re.compile(r"(?i)(://[^\s/:]+:)([^@\s/]+)(@)"),
    )
    _secret_key = re.compile(
        r"(?i)^(?:api[_-]?key|access[_-]?token|auth[_-]?token|refresh[_-]?token|client[_-]?secret|secret[_-]?access[_-]?key|authorization|password|passwd|secret|token|private[_-]?key)$"
    )

    def redact_text(self, value: str) -> str:
        result = value
        for index, pattern in enumerate(self._patterns):
            if index == 6:
                result = pattern.sub(r"\1[REDACTED]", result)
            elif index == 7:
                result = pattern.sub(r"\1[REDACTED]\3", result)
            else:
                result = pattern.sub("[REDACTED]", result)
        return result

    def redact(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.redact_text(value)
        if isinstance(value, Mapping):
            return {
                str(key): "[REDACTED]" if self._secret_key.match(str(key)) else self.redact(item)
                for key, item in value.items()
            }
        if isinstance(value, tuple):
            return tuple(self.redact(item) for item in value)
        if isinstance(value, list):
            return [self.redact(item) for item in value]
        return value


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    timestamp: datetime
    actor: str
    action: str
    target: str
    outcome: str
    details: Mapping[str, Any]
    previous_digest: str | None
    digest: str


class AuditLog:
    """Append-only, redacted, hash-linked security events."""

    def __init__(self, redactor: SecretRedactor | None = None) -> None:
        self.redactor = redactor or SecretRedactor()
        self._events: list[AuditEvent] = []

    def append(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        outcome: str,
        details: Mapping[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> AuditEvent:
        if not all(value.strip() for value in (actor, action, target, outcome)):
            raise ValueError("audit actor, action, target, and outcome must be non-empty")
        event_time = timestamp or datetime.now(timezone.utc)
        if event_time.tzinfo is None:
            raise ValueError("audit timestamp must be timezone-aware")
        safe_actor = self.redactor.redact_text(actor)
        safe_action = self.redactor.redact_text(action)
        safe_target = self.redactor.redact_text(target)
        safe_outcome = self.redactor.redact_text(outcome)
        safe_details = self.redactor.redact(dict(details or {}))
        previous_digest = self._events[-1].digest if self._events else None
        payload = {
            "sequence": len(self._events) + 1,
            "timestamp": event_time.isoformat(),
            "actor": safe_actor,
            "action": safe_action,
            "target": safe_target,
            "outcome": safe_outcome,
            "details": safe_details,
            "previous_digest": previous_digest,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()
        event = AuditEvent(
            sequence=len(self._events) + 1,
            timestamp=event_time,
            actor=safe_actor,
            action=safe_action,
            target=safe_target,
            outcome=safe_outcome,
            details=safe_details,
            previous_digest=previous_digest,
            digest=digest,
        )
        self._events.append(event)
        return event

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def verify(self) -> bool:
        previous: str | None = None
        for event in self._events:
            payload = {
                "sequence": event.sequence,
                "timestamp": event.timestamp.isoformat(),
                "actor": event.actor,
                "action": event.action,
                "target": event.target,
                "outcome": event.outcome,
                "details": event.details,
                "previous_digest": previous,
            }
            digest = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
            ).hexdigest()
            if event.previous_digest != previous or event.digest != digest:
                return False
            previous = event.digest
        return True
