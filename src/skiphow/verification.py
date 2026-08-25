"""Environment-derived verification for supervised campaign tasks."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import threading
from typing import Any, Mapping, Sequence

from .adapters.base import StreamEvent
from .schemas import Task


class VerificationConfigError(ValueError):
    """Raised when a verification plan is unsafe or malformed."""


@dataclass(frozen=True, slots=True)
class VerificationResult:
    passed: bool
    checks: tuple[dict[str, Any], ...]
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": list(self.checks),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class VerificationBaseline:
    forbidden: dict[str, str]
    commands: tuple["_CommandBaseline", ...] = ()


@dataclass(frozen=True, slots=True)
class _CommandBaseline:
    argv: tuple[str, ...]
    executable: str
    executable_fingerprint: str
    trusted_artifacts: tuple[tuple[str, str], ...]


def _relative_path(root: Path, raw: object, field: str) -> tuple[str, Path]:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise VerificationConfigError(f"{field} must be a non-empty POSIX path")
    relative = Path(raw)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise VerificationConfigError(f"{field} must stay inside the project")
    resolved = (root / relative).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise VerificationConfigError(f"{field} escapes the project") from exc
    return relative.as_posix(), resolved


def _fingerprint(path: Path) -> str:
    if not path.exists() and not path.is_symlink():
        return "missing"
    if path.is_symlink():
        return "symlink:" + os.readlink(path)
    if path.is_file():
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return "file:" + digest.hexdigest()
    if path.is_dir():
        digest = hashlib.sha256()
        for child in sorted(path.rglob("*"), key=lambda item: item.as_posix()):
            relative = child.relative_to(path).as_posix()
            digest.update(relative.encode("utf-8", errors="surrogateescape"))
            digest.update(b"\0")
            digest.update(_fingerprint(child).encode("ascii", errors="backslashreplace"))
            digest.update(b"\0")
        return "directory:" + digest.hexdigest()
    return "other"


def _file_contains(path: Path, text: str) -> bool:
    needle = text.encode("utf-8")
    if not needle:
        return True
    overlap = b""
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(64 * 1024), b""):
                data = overlap + chunk
                if needle in data:
                    return True
                overlap_size = len(needle) - 1
                overlap = data[-overlap_size:] if overlap_size else b""
    except OSError:
        return False
    return False


def _drain(stream: Any, limit: int, result: list[bytes]) -> None:
    kept = bytearray()
    for chunk in iter(lambda: stream.read(64 * 1024), b""):
        if len(kept) < limit:
            kept.extend(chunk[: limit - len(kept)])
    result.append(bytes(kept))


class EnvironmentVerifier:
    """Check trusted filesystem and command assertions after provider execution."""

    MAX_TIMEOUT_SECONDS = 300.0
    MAX_OUTPUT_BYTES = 64 * 1024

    def __init__(self, root: Path, tasks: Mapping[str, Mapping[str, Any]]) -> None:
        self.root = root.resolve()
        self.tasks = {str(key): dict(value) for key, value in tasks.items()}
        self._validate_plan()

    @classmethod
    def from_file(cls, root: Path, path: Path) -> "EnvironmentVerifier":
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise VerificationConfigError("verification plan schema_version must be 1")
        tasks = value.get("tasks")
        if not isinstance(tasks, dict) or not all(
            isinstance(key, str) and isinstance(item, dict)
            for key, item in tasks.items()
        ):
            raise VerificationConfigError("verification plan tasks must be an object")
        return cls(root, tasks)

    def prepare(self, task: Task) -> VerificationBaseline:
        spec = self._spec(task)
        forbidden: dict[str, str] = {}
        for raw in self._list(spec, "forbidden_mutations"):
            relative, path = _relative_path(self.root, raw, "forbidden_mutations")
            forbidden[relative] = _fingerprint(path)
        commands = tuple(
            self._prepare_command(item) for item in self._list(spec, "commands")
        )
        return VerificationBaseline(forbidden, commands)

    def verify(
        self,
        task: Task,
        events: Sequence[StreamEvent],
        baseline: VerificationBaseline,
    ) -> VerificationResult:
        del events
        spec = self._spec(task)
        checks: list[dict[str, Any]] = []
        evidence: list[str] = []

        for relative, before in baseline.forbidden.items():
            after = _fingerprint(self.root / relative)
            checks.append(
                {
                    "kind": "forbidden_mutation",
                    "path": relative,
                    "passed": before == after,
                    "before": before,
                    "after": after,
                }
            )

        expected = spec.get("expected_filesystem", [])
        if not isinstance(expected, list):
            raise VerificationConfigError("expected_filesystem must be an array")
        for item in expected:
            checks.append(self._check_path(item))

        commands = spec.get("commands", [])
        if not isinstance(commands, list):
            raise VerificationConfigError("commands must be an array")
        if len(commands) != len(baseline.commands):
            raise VerificationConfigError("verification command baseline is incomplete")
        for command, command_baseline in zip(commands, baseline.commands, strict=True):
            checks.append(self._check_command(command, command_baseline))

        for raw in self._list(spec, "evidence"):
            relative, path = _relative_path(self.root, raw, "evidence")
            passed = path.exists() and path.is_file()
            checks.append({"kind": "evidence", "path": relative, "passed": passed})
            if passed:
                evidence.append(relative)

        if not checks:
            checks.append(
                {
                    "kind": "configuration",
                    "passed": False,
                    "reason": "task declares no environment-derived checks",
                }
            )
        return VerificationResult(
            all(bool(item["passed"]) for item in checks), tuple(checks), tuple(evidence)
        )

    def _spec(self, task: Task) -> dict[str, Any]:
        spec = self.tasks.get(task.task_id, self.tasks.get("*"))
        if spec is None:
            return {}
        allowed = {"expected_filesystem", "forbidden_mutations", "commands", "evidence"}
        unknown = sorted(set(spec) - allowed)
        if unknown:
            raise VerificationConfigError(
                "unknown verification task fields: " + ", ".join(unknown)
            )
        return spec

    def _validate_plan(self) -> None:
        allowed = {"expected_filesystem", "forbidden_mutations", "commands", "evidence"}
        for task_id, spec in self.tasks.items():
            if not task_id:
                raise VerificationConfigError("verification task ids must not be empty")
            unknown = sorted(set(spec) - allowed)
            if unknown:
                raise VerificationConfigError(
                    "unknown verification task fields: " + ", ".join(unknown)
                )
            for field in ("forbidden_mutations", "evidence"):
                for raw in self._list(spec, field):
                    _relative_path(self.root, raw, field)
            expected = spec.get("expected_filesystem", [])
            if not isinstance(expected, list):
                raise VerificationConfigError("expected_filesystem must be an array")
            for item in expected:
                if not isinstance(item, dict):
                    raise VerificationConfigError("expected_filesystem entries must be objects")
                unknown = sorted(set(item) - {"path", "kind", "sha256", "contains"})
                if unknown:
                    raise VerificationConfigError(
                        "unknown filesystem fields: " + ", ".join(unknown)
                    )
                _relative_path(self.root, item.get("path"), "expected path")
                if item.get("kind", "file") not in {"file", "directory", "absent"}:
                    raise VerificationConfigError(
                        "filesystem kind must be file, directory, or absent"
                    )
                expected_hash = item.get("sha256")
                if expected_hash is not None and (
                    not isinstance(expected_hash, str) or len(expected_hash) != 64
                ):
                    raise VerificationConfigError("sha256 must be a 64-character string")
                if item.get("contains") is not None and not isinstance(item["contains"], str):
                    raise VerificationConfigError("contains must be a string")
            commands = spec.get("commands", [])
            if not isinstance(commands, list):
                raise VerificationConfigError("commands must be an array")
            for item in commands:
                if not isinstance(item, dict):
                    raise VerificationConfigError("commands entries must be objects")
                unknown = sorted(
                    set(item)
                    - {
                        "argv",
                        "timeout_seconds",
                        "exit_code",
                        "stdout_contains",
                        "trusted_artifacts",
                    }
                )
                if unknown:
                    raise VerificationConfigError(
                        "unknown command fields: " + ", ".join(unknown)
                    )
                argv = item.get("argv")
                if not isinstance(argv, list) or not argv or not all(
                    isinstance(arg, str) and arg for arg in argv
                ):
                    raise VerificationConfigError(
                        "command argv must be a non-empty string array"
                    )
                timeout = item.get("timeout_seconds", 60)
                if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout <= self.MAX_TIMEOUT_SECONDS:
                    raise VerificationConfigError(
                        "command timeout_seconds must be between 0 and 300"
                    )
                expected_exit = item.get("exit_code", 0)
                if not isinstance(expected_exit, int) or isinstance(expected_exit, bool):
                    raise VerificationConfigError("command exit_code must be an integer")
                if item.get("stdout_contains") is not None and not isinstance(
                    item["stdout_contains"], str
                ):
                    raise VerificationConfigError(
                        "command stdout_contains must be a string"
                    )
                trusted = item.get("trusted_artifacts")
                if not isinstance(trusted, list) or not trusted:
                    raise VerificationConfigError(
                        "command trusted_artifacts must be a non-empty array"
                    )
                for raw in trusted:
                    _, path = _relative_path(
                        self.root, raw, "command trusted_artifacts"
                    )
                    if not path.exists():
                        raise VerificationConfigError(
                            f"command trusted artifact does not exist: {raw}"
                        )

    @staticmethod
    def _list(spec: Mapping[str, Any], key: str) -> list[Any]:
        value = spec.get(key, [])
        if not isinstance(value, list):
            raise VerificationConfigError(f"{key} must be an array")
        return value

    def _check_path(self, item: object) -> dict[str, Any]:
        if not isinstance(item, dict):
            raise VerificationConfigError("expected_filesystem entries must be objects")
        allowed = {"path", "kind", "sha256", "contains"}
        unknown = sorted(set(item) - allowed)
        if unknown:
            raise VerificationConfigError("unknown filesystem fields: " + ", ".join(unknown))
        relative, path = _relative_path(self.root, item.get("path"), "expected path")
        kind = item.get("kind", "file")
        if kind not in {"file", "directory", "absent"}:
            raise VerificationConfigError("filesystem kind must be file, directory, or absent")
        passed = (
            path.is_file() if kind == "file" else path.is_dir() if kind == "directory" else not path.exists()
        )
        reasons: list[str] = []
        expected_hash = item.get("sha256")
        contains = item.get("contains")
        if expected_hash is not None:
            if not isinstance(expected_hash, str) or len(expected_hash) != 64:
                raise VerificationConfigError("sha256 must be a 64-character string")
            actual_hash = _fingerprint(path).removeprefix("file:") if path.is_file() else None
            passed = passed and actual_hash == expected_hash.lower()
            reasons.append(f"sha256={actual_hash}")
        if contains is not None:
            if not isinstance(contains, str):
                raise VerificationConfigError("contains must be a string")
            found = _file_contains(path, contains) if path.is_file() else False
            passed = passed and found
            reasons.append("required text found" if found else "required text missing")
        return {
            "kind": "filesystem",
            "path": relative,
            "expected": kind,
            "passed": passed,
            "details": reasons,
        }

    @staticmethod
    def _command_environment() -> dict[str, str]:
        return {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "LANG", "LC_ALL", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP"}
        }

    def _prepare_command(self, item: object) -> _CommandBaseline:
        if not isinstance(item, dict):
            raise VerificationConfigError("commands entries must be objects")
        argv = item.get("argv")
        if not isinstance(argv, list) or not argv or not all(
            isinstance(arg, str) and arg for arg in argv
        ):
            raise VerificationConfigError("command argv must be a non-empty string array")
        raw_executable = Path(argv[0])
        if raw_executable.is_absolute():
            executable = str(raw_executable)
        elif os.sep in argv[0] or (os.altsep is not None and os.altsep in argv[0]):
            _, executable_path = _relative_path(
                self.root, argv[0], "command executable"
            )
            executable = str(executable_path)
        else:
            executable = shutil.which(
                argv[0], path=self._command_environment().get("PATH")
            )
        if executable is None or not Path(executable).is_file():
            raise VerificationConfigError(f"command executable is unavailable: {argv[0]}")
        executable_path = Path(executable).resolve(strict=True)
        trusted: list[tuple[str, str]] = []
        for raw in item["trusted_artifacts"]:
            relative, path = _relative_path(
                self.root, raw, "command trusted_artifacts"
            )
            trusted.append((relative, _fingerprint(path)))
        return _CommandBaseline(
            tuple(argv),
            str(executable_path),
            _fingerprint(executable_path),
            tuple(trusted),
        )

    def _check_command(
        self, item: object, baseline: _CommandBaseline
    ) -> dict[str, Any]:
        if not isinstance(item, dict):
            raise VerificationConfigError("commands entries must be objects")
        allowed = {
            "argv",
            "timeout_seconds",
            "exit_code",
            "stdout_contains",
            "trusted_artifacts",
        }
        unknown = sorted(set(item) - allowed)
        if unknown:
            raise VerificationConfigError("unknown command fields: " + ", ".join(unknown))
        argv = item.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) and arg for arg in argv):
            raise VerificationConfigError("command argv must be a non-empty string array")
        timeout = item.get("timeout_seconds", 60)
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout <= self.MAX_TIMEOUT_SECONDS:
            raise VerificationConfigError("command timeout_seconds must be between 0 and 300")
        expected_exit = item.get("exit_code", 0)
        if not isinstance(expected_exit, int) or isinstance(expected_exit, bool):
            raise VerificationConfigError("command exit_code must be an integer")
        stdout_contains = item.get("stdout_contains")
        if stdout_contains is not None and not isinstance(stdout_contains, str):
            raise VerificationConfigError("command stdout_contains must be a string")
        if tuple(argv) != baseline.argv:
            raise VerificationConfigError("verification command changed after prepare")
        trust_failures: list[str] = []
        executable_path = Path(baseline.executable)
        if _fingerprint(executable_path) != baseline.executable_fingerprint:
            trust_failures.append("executable changed after provider execution")
        for relative, before in baseline.trusted_artifacts:
            if _fingerprint(self.root / relative) != before:
                trust_failures.append(f"trusted artifact changed: {relative}")
        if trust_failures:
            return {
                "kind": "command",
                "argv": argv,
                "passed": False,
                "exit_code": None,
                "timed_out": False,
                "stdout": "",
                "stderr": "",
                "reason": "; ".join(trust_failures),
            }
        environment = self._command_environment()
        trusted_argv = [baseline.executable, *argv[1:]]
        try:
            process = subprocess.Popen(
                trusted_argv,
                cwd=self.root,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=os.name == "posix",
            )
        except OSError as exc:
            return {
                "kind": "command",
                "argv": argv,
                "passed": False,
                "exit_code": None,
                "timed_out": False,
                "stdout": "",
                "stderr": f"{type(exc).__name__}: {exc}",
            }
        timed_out = False
        stdout_result: list[bytes] = []
        stderr_result: list[bytes] = []
        assert process.stdout is not None and process.stderr is not None
        stdout_thread = threading.Thread(
            target=_drain,
            args=(process.stdout, self.MAX_OUTPUT_BYTES, stdout_result),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_drain,
            args=(process.stderr, self.MAX_OUTPUT_BYTES, stderr_result),
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()
        try:
            process.wait(timeout=float(timeout))
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            process.wait()
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)
        process.stdout.close()
        process.stderr.close()
        stdout = (stdout_result[0] if stdout_result else b"").decode(
            "utf-8", errors="replace"
        )
        stderr = (stderr_result[0] if stderr_result else b"").decode(
            "utf-8", errors="replace"
        )
        passed = not timed_out and process.returncode == expected_exit
        if stdout_contains is not None:
            passed = passed and stdout_contains in stdout
        return {
            "kind": "command",
            "argv": argv,
            "passed": passed,
            "exit_code": process.returncode,
            "timed_out": timed_out,
            "stdout": stdout,
            "stderr": stderr,
        }


class FailClosedVerifier:
    """Reject mutation-capable tasks that lack an environment contract."""

    def prepare(self, task: Task) -> None:
        del task

    def verify(
        self, task: Task, events: Sequence[StreamEvent], baseline: None
    ) -> VerificationResult:
        del task, events, baseline
        return VerificationResult(
            False,
            (
                {
                    "kind": "configuration",
                    "passed": False,
                    "reason": "mutation-capable task has no environment verifier",
                },
            ),
            (),
        )
