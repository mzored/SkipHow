"""Small host adapters for an explicitly authorized live run."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import tempfile
from typing import Any


CREDENTIAL_ENV = {"codex": "OPENAI_API_KEY", "claude": "ANTHROPIC_API_KEY"}
MAX_OUTPUT_BYTES = 16 * 1024 * 1024


class HostError(RuntimeError):
    pass


def _run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 900) -> tuple[int, str, str]:
    try:
        with tempfile.TemporaryFile(mode="w+t", encoding="utf-8", errors="replace") as stdout_file, tempfile.TemporaryFile(mode="w+t", encoding="utf-8", errors="replace") as stderr_file:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                start_new_session=os.name == "posix",
            )
            try:
                process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                _terminate_process_group(process)
                process.wait(timeout=5)
                raise HostError(f"host process timed out after {timeout} seconds")
            finally:
                _terminate_process_group(process)
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read(MAX_OUTPUT_BYTES + 1)
            stderr = stderr_file.read(MAX_OUTPUT_BYTES + 1)
            if len(stdout.encode("utf-8")) > MAX_OUTPUT_BYTES or len(stderr.encode("utf-8")) > MAX_OUTPUT_BYTES:
                raise HostError("host output exceeded the evaluator limit")
    except OSError as exc:
        raise HostError(str(exc)) from exc
    return process.returncode, stdout, stderr


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Stop descendants before final-state collection, including background tools."""
    if os.name == "posix":
        for requested_signal in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, requested_signal)
            except ProcessLookupError:
                return
    elif process.poll() is None:
        process.terminate()


def executable(host: str) -> str:
    value = shutil.which(host)
    if value is None:
        raise HostError(f"{host} executable is unavailable")
    return value


def identity(host: str) -> dict[str, str]:
    """Capture the installed host binary identity before a live trial starts."""
    binary = executable(host)
    code, stdout, stderr = _run([binary, "--version"], cwd=Path.cwd(), env=os.environ.copy(), timeout=30)
    if code:
        raise HostError(f"cannot identify {host} host")
    return {"name": host, "version": (stdout or stderr).strip()}


def fresh_config(
    host: str,
    trial_root: Path,
    *,
    credential: str,
    github_token: str | None = None,
) -> tuple[Path, dict[str, str]]:
    config = trial_root / "host-config"
    config.mkdir(mode=0o700, parents=True, exist_ok=False)
    environment = {
        name: os.environ[name]
        for name in ("PATH", "LANG", "LC_ALL", "TMPDIR", "SSL_CERT_FILE", "SSL_CERT_DIR")
        if os.environ.get(name)
    }
    environment[CREDENTIAL_ENV[host]] = credential
    if github_token:
        environment["GH_TOKEN"] = github_token
    environment["CODEX_HOME" if host == "codex" else "CLAUDE_CONFIG_DIR"] = str(config)
    return config, environment


def _payload(root: Path) -> dict[str, str]:
    """Hash a plain package and reject repositories, links, and special files."""
    if not root.is_dir() or root.is_symlink():
        raise HostError(f"package directory is unavailable: {root}")
    result: dict[str, str] = {}
    for path in root.rglob("*"):
        mode = path.lstat().st_mode
        if path.name == ".git":
            raise HostError("marketplace source must not contain a repository")
        if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise HostError("marketplace source must contain ordinary files and directories only")
        if stat.S_ISREG(mode):
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not result:
        raise HostError("package payload is empty")
    return result


def _payload_id(payload: dict[str, str]) -> str:
    serialized = "".join(f"{name}\0{digest}\n" for name, digest in sorted(payload.items()))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def verify_codex_plain_source(candidate: Path, source: str | None) -> tuple[Path, str]:
    """Require an external plain marketplace snapshot of the exact candidate."""
    if not source:
        raise HostError("Codex requires --codex-marketplace-source with a plain local snapshot")
    if "://" in source:
        raise HostError("Codex marketplace source must be a plain local snapshot, not a remote URL")
    marketplace = Path(source).expanduser().resolve()
    candidate = candidate.resolve()
    if marketplace == candidate or marketplace.is_relative_to(candidate) or candidate.is_relative_to(marketplace):
        raise HostError("Codex marketplace snapshot must stay outside the candidate checkout")
    marketplace_payload = _payload(marketplace)
    manifest = marketplace / ".agents/plugins/marketplace.json"
    candidate_manifest = candidate / ".agents/plugins/marketplace.json"
    if not manifest.is_file() or manifest.read_bytes() != candidate_manifest.read_bytes():
        raise HostError("Codex marketplace manifest does not match the candidate")
    source_plugin = marketplace / "plugins/skiphow"
    candidate_payload = _payload(candidate / "plugins/skiphow")
    if _payload(source_plugin) != candidate_payload:
        raise HostError("Codex marketplace plugin payload does not match the candidate")
    expected_marketplace = {
        ".agents/plugins/marketplace.json": hashlib.sha256(candidate_manifest.read_bytes()).hexdigest(),
        **{f"plugins/skiphow/{name}": digest for name, digest in candidate_payload.items()},
    }
    if marketplace_payload != expected_marketplace:
        raise HostError("Codex marketplace snapshot contains files outside the exact candidate package")
    return marketplace, _payload_id(candidate_payload)


def install_candidate(
    host: str,
    candidate: Path,
    config_env: dict[str, str],
    *,
    version: str,
    codex_source: str | None = None,
) -> dict[str, Any]:
    binary = executable(host)
    if host == "codex":
        marketplace, payload_id = verify_codex_plain_source(candidate, codex_source)
        commands = [
            [binary, "plugin", "marketplace", "add", str(marketplace), "--json"],
            [binary, "plugin", "add", "skiphow@skiphow", "--json"],
            [binary, "plugin", "list", "--json"],
        ]
    elif host == "claude":
        plugin = candidate / "plugins/skiphow"
        payload_id = _payload_id(_payload(plugin))
        code, _, _ = _run([binary, "plugin", "validate", "--strict", str(plugin)], cwd=candidate, env=config_env)
        if code:
            raise HostError("Claude package validation failed before direct loading")
        return {"load_mode": "plugin-dir", "payload_sha256": payload_id, "version": version}
    else:
        raise HostError(f"unsupported host: {host}")
    transcript: list[dict[str, Any]] = []
    for command in commands:
        code, stdout, stderr = _run(command, cwd=candidate, env=config_env)
        transcript.append({"command": command, "exit_code": code, "stdout": stdout, "stderr": stderr})
        if code:
            raise HostError(f"host installation failed: {' '.join(command[:3])}")
    try:
        inventory = _installed_skiphow(host, transcript[-1]["stdout"])
    except (ValueError, KeyError, TypeError) as exc:
        raise HostError(f"host inventory cannot prove the SkipHow installation: {exc}") from exc
    if inventory.get("version") != version or inventory.get("enabled") is not True or inventory.get("installed") is not True:
        raise HostError("host inventory does not show the exact enabled SkipHow candidate")
    installed_path = Path(str(inventory.pop("path"))).resolve()
    if _payload(installed_path) != _payload(candidate / "plugins/skiphow"):
        raise HostError("installed SkipHow payload does not match the candidate")
    return {"inventory": inventory, "payload_sha256": payload_id}


def _installed_skiphow(host: str, raw: str) -> dict[str, Any]:
    value = json.loads(raw)
    entries = value.get("installed") if host == "codex" and isinstance(value, dict) else value
    if not isinstance(entries, list):
        raise ValueError("plugin inventory is not a list")
    matches = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        identifier = item.get("pluginId") if host == "codex" else item.get("id")
        if identifier == "skiphow@skiphow":
            matches.append(item)
    if len(matches) != 1:
        raise ValueError("expected one skiphow@skiphow inventory item")
    item = matches[0]
    source = item.get("source") if host == "codex" else None
    path = source.get("path") if isinstance(source, dict) else item.get("installPath")
    if not isinstance(path, str) or not path:
        raise ValueError("installed package path is missing")
    return {
        "id": "skiphow@skiphow",
        "version": item.get("version"),
        "enabled": item.get("enabled") is True,
        "installed": item.get("installed", True) is True,
        "path": path,
    }


def invoke(
    host: str,
    workspace: Path,
    prompt: str,
    model: str,
    effort: str,
    budget: str,
    config_env: dict[str, str],
    *,
    candidate: Path,
    explicit_skill: bool,
    network: bool,
) -> tuple[list[str], int, str, str]:
    binary = executable(host)
    request = (("$skiphow\n\n" if host == "codex" else "/skiphow:skiphow\n\n") if explicit_skill else "") + prompt
    if host == "codex":
        command = [binary, "exec", "--json", "--ephemeral", "--skip-git-repo-check", "--sandbox", "workspace-write", "--model", model, "-c", f'model_reasoning_effort="{effort}"']
        if network:
            command.extend(["-c", "sandbox_workspace_write.network_access=true"])
        command.extend(["-C", str(workspace), request])
    elif host == "claude":
        settings_path = Path(config_env["CLAUDE_CONFIG_DIR"]) / "live-settings.json"
        settings_path.write_text(
            json.dumps(
                {
                    "sandbox": {
                        "enabled": True,
                        "allowUnsandboxedCommands": False,
                        "failIfUnavailable": True,
                        "network": {"allowedDomains": ["api.github.com", "github.com"] if network else []},
                    }
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        command = [binary, "--bare", "--settings", str(settings_path), "--print", "--verbose", "--output-format", "stream-json", "--no-session-persistence", "--plugin-dir", str(candidate / "plugins/skiphow"), "--model", model, "--effort", effort, "--max-budget-usd", budget, "--permission-mode", "acceptEdits"]
        if not network:
            command.extend(["--disallowed-tools", "WebFetch,WebSearch"])
        command.append(request)
    else:
        raise HostError(f"unsupported host: {host}")
    code, stdout, stderr = _run(command, cwd=workspace, env=config_env)
    return command, code, stdout, stderr
