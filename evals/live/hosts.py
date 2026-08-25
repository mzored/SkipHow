"""Small host adapters for an explicitly authorized live run."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
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
    return {"name": host, "executable": binary, "version": (stdout or stderr).strip()}


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


def candidate_head(candidate: Path) -> str:
    code, output, _ = _git(candidate, "rev-parse", "HEAD")
    if code or not output.strip():
        raise HostError("cannot resolve candidate HEAD")
    return output.strip()


def verify_codex_remote_source(candidate: Path, source: str | None, ref: str | None) -> str:
    """Codex must install a remote ref that resolves to the committed candidate."""
    if not source or not ref:
        raise HostError("Codex requires --codex-marketplace-source and --codex-marketplace-ref")
    if Path(source).expanduser().is_dir():
        raise HostError("Codex live runs require a remote marketplace source, not a local checkout")
    head = candidate_head(candidate)
    code, output, _ = _git(candidate, "ls-remote", source, ref, f"{ref}^{{}}", timeout=45)
    commits = {line.split()[0] for line in output.splitlines() if line.split()}
    if code or head not in commits:
        raise HostError("Codex marketplace ref does not resolve to the candidate HEAD")
    return head


def _git(candidate: Path, *arguments: str, timeout: int = 30) -> tuple[int, str, str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    }
    return _run(
        ["git", "-c", "core.hooksPath=", "-c", "core.fsmonitor=false", *arguments],
        cwd=candidate,
        env=environment,
        timeout=timeout,
    )


def install_candidate(
    host: str,
    candidate: Path,
    config_env: dict[str, str],
    *,
    version: str,
    codex_source: str | None = None,
    codex_ref: str | None = None,
) -> dict[str, Any]:
    binary = executable(host)
    if host == "codex":
        verify_codex_remote_source(candidate, codex_source, codex_ref)
        commands = [
            [binary, "plugin", "marketplace", "add", str(codex_source), "--ref", str(codex_ref), "--json"],
            [binary, "plugin", "add", "skiphow@skiphow", "--json"],
            [binary, "plugin", "list", "--json"],
        ]
    elif host == "claude":
        commands = [
            [binary, "plugin", "marketplace", "add", str(candidate), "--scope", "user"],
            [binary, "plugin", "install", "skiphow@skiphow", "--scope", "user", "--yes"],
            [binary, "plugin", "list", "--json"],
        ]
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
    return {"inventory": inventory}


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
    return {
        "id": "skiphow@skiphow",
        "version": item.get("version"),
        "enabled": item.get("enabled") is True,
        "installed": item.get("installed", True) is True,
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
        command = [binary, "--print", "--verbose", "--output-format", "stream-json", "--plugin-dir", str(candidate / "plugins/skiphow"), "--model", model, "--effort", effort, "--max-budget-usd", budget, "--permission-mode", "acceptEdits"]
        if not network:
            command.extend(["--disallowed-tools", "WebFetch,WebSearch"])
        command.append(request)
    else:
        raise HostError(f"unsupported host: {host}")
    code, stdout, stderr = _run(command, cwd=workspace, env=config_env)
    return command, code, stdout, stderr
