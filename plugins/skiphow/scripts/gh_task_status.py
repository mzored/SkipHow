#!/usr/bin/env python3
"""Compact GitHub issue and Project v2 lifecycle operations for SkipHow."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any, Iterable


TIMEOUT_SECONDS = 20
BRANCH_RE = re.compile(r"^(\d+)-")
ISSUE_REF_RE = re.compile(
    r"^(?:https://github\.com/)?(?P<repo>[^/\s]+/[^/#\s]+)(?:/issues/|#)(?P<number>\d+)$"
)
REMOTE_RE = re.compile(r"github\.com[:/]+([^/]+)/(.+?)(?:\.git)?$")
STARTED = {"In Progress", "In Review", "Done", "Blocked"}
OPTION_FIELDS = {
    "Todo": "Status",
    "In Progress": "Status",
    "In Review": "Status",
    "Done": "Status",
    "Blocked": "Status",
    "No": "Human Gate",
    "Deploy": "Human Gate",
    "Product decision": "Human Gate",
    "External": "Human Gate",
}
REQUIRED_BOARD_OPTIONS = {
    "Status": {"Todo", "In Progress", "Done", "Blocked"},
    "Human Gate": {"No", "Deploy", "Product decision", "External"},
}
MINIMUM_GH_VERSION = (2, 93, 0)


LINKED_PROJECTS_QUERY = """
query($owner:String!,$repo:String!,$cursor:String){
  repository(owner:$owner,name:$repo){
    projectsV2(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{number owner{
      ... on User{login}
      ... on Organization{login}
    }}}
  }
}
"""

PROJECT_REPOS_QUERY = """
query($login:String!,$number:Int!,$cursor:String){
  HOLDER(login:$login){projectV2(number:$number){id
    items(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{content{
      ... on Issue{repository{nameWithOwner}}
      ... on PullRequest{repository{nameWithOwner}}
    }}}
  }}
}
"""

OWNER_PROJECTS_QUERY = """
query($login:String!,$cursor:String){
  HOLDER(login:$login){projectsV2(first:100,after:$cursor){
    pageInfo{hasNextPage endCursor}
    nodes{number}
  }}
}
"""

PROJECT_FIELDS_QUERY = """
query($login:String!,$number:Int!,$cursor:String){
  HOLDER(login:$login){projectV2(number:$number){id
    fields(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{
      ... on ProjectV2SingleSelectField{id name options{id name}}
    }}
  }}
}
"""

ISSUE_ITEM_QUERY = """
query($owner:String!,$repo:String!,$number:Int!,$cursor:String){
  repository(owner:$owner,name:$repo){issue(number:$number){
    projectItems(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{id project{id}
      status:fieldValueByName(name:"Status"){
        ... on ProjectV2ItemFieldSingleSelectValue{
          name field{... on ProjectV2FieldCommon{name}}
        }
      }
      gate:fieldValueByName(name:"Human Gate"){
        ... on ProjectV2ItemFieldSingleSelectValue{
          name field{... on ProjectV2FieldCommon{name}}
        }
      }
    }}
  }}
}
"""

QUEUE_QUERY = """
query($login:String!,$number:Int!,$cursor:String){
  HOLDER(login:$login){projectV2(number:$number){id
    items(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{
      content{
        ... on Issue{number title repository{nameWithOwner} issueType{name} labels(first:100){nodes{name}}}
      }
      status:fieldValueByName(name:"Status"){
        ... on ProjectV2ItemFieldSingleSelectValue{
          name field{... on ProjectV2FieldCommon{name}}
        }
      }
      gate:fieldValueByName(name:"Human Gate"){
        ... on ProjectV2ItemFieldSingleSelectValue{
          name field{... on ProjectV2FieldCommon{name}}
        }
      }
    }}
  }}
}
"""


class LifecycleError(RuntimeError):
    """A concise user-facing lifecycle failure."""


class UntrackedLifecycle(LifecycleError):
    """The repository or issue is not part of an adopted Project lifecycle."""


@dataclass(frozen=True)
class IssueRef:
    repo: str
    number: int


def run(args: list[str], *, cwd: str | None = None) -> str:
    """Run one deterministic host command and return stripped stdout."""
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except OSError as exc:
        raise LifecycleError(f"cannot run {args[0]}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise LifecycleError(f"timed out running {' '.join(args[:3])}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise LifecycleError(detail[-1] if detail else f"{' '.join(args[:2])} failed")
    return result.stdout.strip()


def run_json(args: list[str], *, cwd: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(run(args, cwd=cwd))
    except json.JSONDecodeError as exc:
        raise LifecycleError(f"{args[0]} returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise LifecycleError(f"{args[0]} returned an unexpected JSON value")
    return value


def graphql(query: str, variables: dict[str, str | int]) -> dict[str, Any]:
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for name, value in variables.items():
        flag = "-F" if isinstance(value, int) else "-f"
        args.extend([flag, f"{name}={value}"])
    return run_json(args)


def repo_at(cwd: str = ".") -> str:
    try:
        remote = run(["git", "-C", cwd, "remote", "get-url", "origin"])
    except LifecycleError:
        remote = ""
    match = REMOTE_RE.search(remote)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
        cwd=cwd,
    )


def default_branch(repo: str) -> str:
    branch = run(
        [
            "gh",
            "repo",
            "view",
            repo,
            "--json",
            "defaultBranchRef",
            "--jq",
            ".defaultBranchRef.name",
        ]
    )
    if not branch:
        raise LifecycleError(f"{repo} has no default branch")
    return branch


def viewer() -> str:
    return run(["gh", "api", "user", "--jq", ".login"])


def project_query(owner: str, number: int, query: str, **extra: str) -> dict[str, Any]:
    login = viewer() if owner == "@me" else owner
    last_error: LifecycleError | None = None
    for holder in ("organization", "user"):
        try:
            payload = graphql(
                query.replace("HOLDER", holder),
                {"login": login, "number": number, **extra},
            )
        except LifecycleError as exc:
            last_error = exc
            continue
        project = ((payload.get("data") or {}).get(holder) or {}).get("projectV2")
        if isinstance(project, dict):
            return project
    if last_error:
        raise last_error
    raise LifecycleError(f"cannot read project {owner}/{number}")


@dataclass(frozen=True)
class Board:
    owner: str
    number: int
    base: str


def candidate_projects(owner: str) -> Iterable[tuple[str, int]]:
    login = viewer() if owner == "@me" else owner
    last_error: LifecycleError | None = None
    for holder in ("organization", "user"):
        cursor: str | None = None
        found_holder = False
        while True:
            variables: dict[str, str | int] = {"login": login}
            if cursor is not None:
                variables["cursor"] = cursor
            try:
                payload = graphql(OWNER_PROJECTS_QUERY.replace("HOLDER", holder), variables)
            except LifecycleError as exc:
                last_error = exc
                break
            connection = ((payload.get("data") or {}).get(holder) or {}).get("projectsV2")
            if not isinstance(connection, dict):
                break
            found_holder = True
            for project in connection.get("nodes") or []:
                number = project.get("number")
                if isinstance(number, int):
                    yield owner, number
            page = connection.get("pageInfo") or {}
            if not page.get("hasNextPage") or not page.get("endCursor"):
                return
            cursor = str(page["endCursor"])
        if found_holder:
            return
    if last_error:
        raise last_error


def board_for(repo: str) -> Board:
    owner, name = repo.split("/", 1)
    nodes: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        variables: dict[str, str | int] = {"owner": owner, "repo": name}
        if cursor is not None:
            variables["cursor"] = cursor
        payload = graphql(LINKED_PROJECTS_QUERY, variables)
        connection = (
            ((payload.get("data") or {}).get("repository") or {}).get("projectsV2") or {}
        )
        nodes.extend(connection.get("nodes") or [])
        page = connection.get("pageInfo") or {}
        if not page.get("hasNextPage") or not page.get("endCursor"):
            break
        cursor = str(page["endCursor"])
    linked = [
        (str((node.get("owner") or {}).get("login")), int(node["number"]))
        for node in nodes
        if (node.get("owner") or {}).get("login") and isinstance(node.get("number"), int)
    ]
    if len(linked) > 1:
        choices = ", ".join(f"{item_owner}/{number}" for item_owner, number in linked)
        raise LifecycleError(f"multiple linked projects match {repo}: {choices}")
    if len(linked) == 1:
        return Board(linked[0][0], linked[0][1], default_branch(repo))

    owners = [owner]
    current_viewer = viewer()
    if current_viewer != owner:
        owners.append(current_viewer)
    matches: list[tuple[str, int]] = []
    for candidate_owner in owners:
        for project_owner, number in candidate_projects(candidate_owner):
            repos: set[str | None] = set()
            cursor = None
            while True:
                extra = {} if cursor is None else {"cursor": cursor}
                project = project_query(project_owner, number, PROJECT_REPOS_QUERY, **extra)
                items = project.get("items") or {}
                repos.update(
                    ((node.get("content") or {}).get("repository") or {}).get("nameWithOwner")
                    for node in items.get("nodes") or []
                )
                page = items.get("pageInfo") or {}
                if not page.get("hasNextPage") or not page.get("endCursor"):
                    break
                cursor = str(page["endCursor"])
            if repo in repos:
                matches.append((project_owner, number))
    matches = list(dict.fromkeys(matches))
    if not matches:
        raise UntrackedLifecycle(f"no Project v2 board contains {repo}")
    if len(matches) > 1:
        choices = ", ".join(f"{item_owner}/{number}" for item_owner, number in matches)
        raise LifecycleError(f"multiple projects contain {repo}: {choices}")
    return Board(matches[0][0], matches[0][1], default_branch(repo))


def field_values(nodes: Iterable[dict[str, Any]]) -> dict[str, str]:
    values: dict[str, str] = {}
    for node in nodes:
        field_name = ((node or {}).get("field") or {}).get("name")
        value = (node or {}).get("name")
        if field_name and value:
            values[str(field_name)] = str(value)
    return values


def lifecycle_values(item: dict[str, Any]) -> dict[str, str]:
    """Read only lifecycle fields requested by name from one Project v2 item."""
    return field_values(
        value for value in (item.get("status"), item.get("gate")) if isinstance(value, dict)
    )


@dataclass
class Task:
    repo: str
    board: Board
    project_id: str
    item_id: str
    values: dict[str, str]

    @property
    def status(self) -> str:
        return self.values.get("Status", "")

    @property
    def gate(self) -> str:
        return self.values.get("Human Gate", "")


def project_fields(board: Board) -> tuple[str, dict[str, tuple[str, dict[str, str]]]]:
    project_id: str | None = None
    fields: dict[str, tuple[str, dict[str, str]]] = {}
    cursor: str | None = None
    while True:
        extra = {} if cursor is None else {"cursor": cursor}
        project = project_query(board.owner, board.number, PROJECT_FIELDS_QUERY, **extra)
        project_id = str(project.get("id") or project_id or "")
        connection = project.get("fields") or {}
        for field in connection.get("nodes") or []:
            if not field or not field.get("id") or not field.get("name"):
                continue
            fields[str(field["name"])] = (
                str(field["id"]),
                {
                    str(option["name"]): str(option["id"])
                    for option in field.get("options") or []
                    if option.get("name") and option.get("id")
                },
            )
        page = connection.get("pageInfo") or {}
        if not page.get("hasNextPage") or not page.get("endCursor"):
            break
        cursor = str(page["endCursor"])
    if not project_id:
        raise LifecycleError(f"project {board.owner}/{board.number} has no id")
    return project_id, fields


def issue_item(repo: str, number: int, project_id: str) -> tuple[str, dict[str, str]]:
    owner, name = repo.split("/", 1)
    cursor: str | None = None
    while True:
        variables: dict[str, str | int] = {
            "owner": owner,
            "repo": name,
            "number": number,
        }
        if cursor is not None:
            variables["cursor"] = cursor
        payload = graphql(ISSUE_ITEM_QUERY, variables)
        issue = ((payload.get("data") or {}).get("repository") or {}).get("issue")
        if not issue:
            raise UntrackedLifecycle(f"issue #{number} does not exist in {repo}")
        connection = issue.get("projectItems") or {}
        for node in connection.get("nodes") or []:
            if ((node.get("project") or {}).get("id")) != project_id:
                continue
            values = lifecycle_values(node)
            return str(node["id"]), values
        page = connection.get("pageInfo") or {}
        if not page.get("hasNextPage") or not page.get("endCursor"):
            break
        cursor = str(page["endCursor"])
    raise UntrackedLifecycle(f"issue #{number} is not on project {project_id}")


def resolve_task(repo: str, number: int) -> tuple[Task, dict[str, tuple[str, dict[str, str]]]]:
    board = board_for(repo)
    project_id, fields = project_fields(board)
    item_id, values = issue_item(repo, number, project_id)
    return Task(repo, board, project_id, item_id, values), fields


def branch_name(cwd: str = ".") -> str:
    return run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"])


def issue_ref(value: str | None, cwd: str = ".") -> IssueRef:
    if value:
        digits = value.lstrip("#")
        if digits.isdigit():
            return IssueRef(repo_at(cwd), int(digits))
        match = ISSUE_REF_RE.match(value)
        if match:
            return IssueRef(match.group("repo"), int(match.group("number")))
        raise LifecycleError(f"invalid issue reference: {value}")
    match = BRANCH_RE.match(branch_name(cwd))
    if not match:
        raise LifecycleError("pass an issue number or use a branch named <N>-<slug>")
    return IssueRef(repo_at(cwd), int(match.group(1)))


def command_board(repo: str | None) -> int:
    resolved_repo = repo or repo_at()
    board = board_for(resolved_repo)
    print(f"{board.owner}\t{board.number}\t{board.base}")
    return 0


def command_show(number_value: str | None) -> int:
    target = issue_ref(number_value)
    task, _ = resolve_task(target.repo, target.number)
    print(
        f"{target.repo}#{target.number} status={task.status or 'unset'} gate={task.gate or '—'} "
        f"board={task.board.owner}/{task.board.number}"
    )
    return 0


def command_queue(repo: str | None) -> int:
    resolved_repo = repo or repo_at()
    board = board_for(resolved_repo)
    cursor: str | None = None
    rows: list[str] = []
    while True:
        extra = {} if cursor is None else {"cursor": cursor}
        project = project_query(board.owner, board.number, QUEUE_QUERY, **extra)
        items = project.get("items") or {}
        for item in items.get("nodes") or []:
            content = item.get("content") or {}
            if not content.get("number") or not content.get("title"):
                continue
            values = lifecycle_values(item)
            if values.get("Status") != "Todo":
                continue
            labels = {node.get("name") for node in ((content.get("labels") or {}).get("nodes") or [])}
            issue_type = ((content.get("issueType") or {}).get("name") or "").lower()
            if issue_type == "epic" or "epic" in {str(label).lower() for label in labels if label}:
                continue
            item_repo = ((content.get("repository") or {}).get("nameWithOwner")) or resolved_repo
            rows.append(f"{item_repo}#{content['number']}\t{content['title']}")
        page = items.get("pageInfo") or {}
        if not page.get("hasNextPage") or not page.get("endCursor"):
            break
        cursor = str(page["endCursor"])
    for row in rows:
        print(row)
    return 0


def set_option(repo: str, number: int, option: str) -> None:
    task, fields = resolve_task(repo, number)
    if option == "In Progress" and task.gate != "No":
        raise LifecycleError(f"issue #{number} has Human Gate={task.gate}")
    field_name = OPTION_FIELDS.get(option)
    if not field_name:
        raise LifecycleError(f"unsupported lifecycle option {option!r}")
    field = fields.get(field_name)
    if not field or option not in field[1]:
        raise LifecycleError(f"field {field_name!r} has no option named {option!r}")
    field_id, options = field
    option_id = options[option]
    if task.values.get(field_name) != option:
        run(
            [
                "gh",
                "project",
                "item-edit",
                "--id",
                task.item_id,
                "--project-id",
                task.project_id,
                "--field-id",
                field_id,
                "--single-select-option-id",
                option_id,
            ]
        )


def command_set(number_value: str | None, option: str) -> int:
    target = issue_ref(number_value)
    set_option(target.repo, target.number, option)
    print(f"{target.repo}#{target.number} set {option}")
    return 0


def command_verify(number_value: str | None) -> int:
    target = issue_ref(number_value)
    issue = run_json(
        ["gh", "issue", "view", str(target.number), "--repo", target.repo, "--json", "state"]
    )
    task, _ = resolve_task(target.repo, target.number)
    closed = issue.get("state") == "CLOSED"
    done = task.status == "Done"
    if closed and done:
        print(
            f"{target.repo}#{target.number} issue=closed status=Done "
            f"board={task.board.owner}/{task.board.number}"
        )
        return 0
    repairs: list[str] = []
    if not closed:
        repairs.append(
            f"close issue {target.repo}#{target.number} through the repository integration path"
        )
    if not done:
        repairs.append(
            f"run gh-task-status set {target.repo}#{target.number} Done after the issue is closed"
        )
    print(f"{target.repo}#{target.number} drift: {'; '.join(repairs)}", file=sys.stderr)
    return 1


def version_parts(value: str) -> tuple[int, int, int] | None:
    """Extract a semantic CLI version without adding a package dependency."""
    match = re.search(r"(?:version\s+)?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def preflight_report(repo: str | None = None, *, cwd: str = ".") -> tuple[list[str], list[str]]:
    """Check local prerequisites and the adopted board without changing either."""
    failures: list[str] = []
    notes: list[str] = []
    if sys.version_info < (3, 10):
        failures.append("Python 3.10 or newer is required")
    else:
        notes.append(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    if not shutil.which("git"):
        failures.append("install git and retry")
    else:
        try:
            run(["git", "-C", cwd, "rev-parse", "--show-toplevel"])
            notes.append("git repository detected")
        except LifecycleError as exc:
            failures.append(f"open a git repository before preflight: {exc}")
    if not shutil.which("gh"):
        failures.append("install GitHub CLI 2.93.0 or newer and authenticate with gh auth login")
    else:
        try:
            gh_version = version_parts(run(["gh", "--version"]))
            if gh_version is None or gh_version < MINIMUM_GH_VERSION:
                failures.append("upgrade GitHub CLI to version 2.93.0 or newer")
            else:
                notes.append("gh " + ".".join(str(part) for part in gh_version))
            run(["gh", "auth", "status"])
            notes.append("gh authentication verified")
        except LifecycleError as exc:
            failures.append(f"authenticate GitHub CLI with gh auth login: {exc}")
    if not failures or not any("GitHub CLI" in failure or "authenticate" in failure for failure in failures):
        try:
            resolved_repo = repo or repo_at(cwd)
            board = board_for(resolved_repo)
            _, fields = project_fields(board)
            for field_name, options in REQUIRED_BOARD_OPTIONS.items():
                available = set((fields.get(field_name) or ("", {}))[1])
                missing = sorted(options - available)
                if missing:
                    failures.append(
                        f"board {board.owner}/{board.number} field {field_name!r} is missing options: "
                        + ", ".join(missing)
                    )
            if not any("board " in failure for failure in failures):
                notes.append(f"board {board.owner}/{board.number} lifecycle schema verified")
        except LifecycleError as exc:
            failures.append(f"repair or select an adopted Project v2 board: {exc}")
    hook_path = Path(__file__).resolve().parents[1] / "hooks" / "hooks.json"
    try:
        hooks = json.loads(hook_path.read_text(encoding="utf-8"))
        if set((hooks.get("hooks") or {})) != {"PreToolUse", "Stop"}:
            raise ValueError("expected PreToolUse and Stop")
        notes.append("shared lifecycle hooks are present")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"repair plugin hooks at {hook_path}: {exc}")
    host_commands = {"codex": ["plugin", "--help"], "claude": ["plugin", "--help"]}
    for host, command_args in host_commands.items():
        executable = shutil.which(host)
        if not executable:
            notes.append(f"{host} not found; its host validation is skipped")
            continue
        try:
            run([executable, *command_args])
            notes.append(f"{host} plugin command interface is available")
        except LifecycleError as exc:
            failures.append(f"repair {host} before running host checks: {exc}")
    return failures, notes


def command_preflight(repo: str | None) -> int:
    failures, notes = preflight_report(repo)
    for note in notes:
        print(f"PASS {note}")
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    if failures:
        print("Preflight made no changes. Fix the listed items, then rerun this command.", file=sys.stderr)
        return 1
    print("Preflight passed. No files, hooks, board items, or remote state were changed.")
    return 0


def hook_command(event: dict[str, Any]) -> str:
    tool_input = event.get("tool_input") or {}
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    return str(command)


def standalone_shell_tokens(command: str) -> list[str] | None:
    """Parse one simple shell invocation and reject compound shell syntax."""
    if "\n" in command or "\r" in command:
        return None
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return None
    if not tokens or any(token and set(token) <= set(";&|<>") for token in tokens):
        return None
    return tokens


def normalize_repo(value: str) -> str:
    remote_match = REMOTE_RE.search(value)
    if remote_match:
        return f"{remote_match.group(1)}/{remote_match.group(2)}"
    parts = value.removesuffix(".git").split("/")
    if len(parts) == 2 and all(parts):
        return "/".join(parts)
    if len(parts) == 3 and "." in parts[0] and all(parts):
        return "/".join(parts[-2:])
    raise LifecycleError(f"unsupported GitHub repository reference: {value}")


def develop_target(command: str, cwd: str) -> IssueRef | None:
    """Return the issue for one standalone branch-creation command."""
    tokens = standalone_shell_tokens(command)
    if not tokens or tokens[:3] != ["gh", "issue", "develop"]:
        return None
    value_flags = {"-b", "--base", "--branch-repo", "-n", "--name", "-R", "--repo"}
    boolean_flags = {"-c", "--checkout"}
    repo_override: str | None = None
    issue_value: str | None = None
    index = 3
    while index < len(tokens):
        token = tokens[index]
        if token in {"-l", "--list", "--help"}:
            return None
        if token in boolean_flags:
            index += 1
            continue
        if token.startswith("--repo="):
            repo_override = normalize_repo(token.split("=", 1)[1])
            index += 1
            continue
        if token.startswith("--") and "=" in token:
            flag, _ = token.split("=", 1)
            if flag not in value_flags:
                return None
            index += 1
            continue
        if token in value_flags:
            if index + 1 >= len(tokens):
                return None
            if token in {"-R", "--repo"}:
                repo_override = normalize_repo(tokens[index + 1])
            index += 2
            continue
        if token.startswith("-") or issue_value is not None:
            return None
        issue_value = token
        index += 1
    if issue_value is None:
        return None
    if issue_value.lstrip("#").isdigit():
        return IssueRef(repo_override or repo_at(cwd), int(issue_value.lstrip("#")))
    target = issue_ref(issue_value, cwd)
    if repo_override and repo_override != target.repo:
        raise LifecycleError("issue URL and --repo select different repositories")
    return target


def linked_branch_names(target: IssueRef) -> set[str]:
    output = run(
        [
            "gh",
            "issue",
            "develop",
            "--list",
            str(target.number),
            "--repo",
            target.repo,
        ]
    )
    return {
        line.split("\t", 1)[0].strip()
        for line in output.splitlines()
        if line.split("\t", 1)[0].strip()
    }


def hook_pre() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    command = hook_command(event)
    cwd = str(event.get("cwd") or ".")
    try:
        target = develop_target(command, cwd)
        if target is None:
            return 0
        task, _ = resolve_task(target.repo, target.number)
    except UntrackedLifecycle:
        # The hook is global, but lifecycle enforcement applies only when the
        # repository and issue can be proven to belong to an adopted board.
        return 0
    except LifecycleError as exc:
        print(f"Cannot verify GitHub lifecycle before branch creation: {exc}", file=sys.stderr)
        return 2
    if task.gate != "No":
        print(
            f"Issue {target.repo}#{target.number} has Human Gate={task.gate or 'unset'}. "
            "Set it to No or resolve the gate before creating a linked branch.",
            file=sys.stderr,
        )
        return 2
    return 0


def hook_stop() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    if event.get("stop_hook_active"):
        return 0
    cwd = str(event.get("cwd") or ".")
    try:
        match = BRANCH_RE.match(branch_name(cwd))
        if not match:
            return 0
        number = int(match.group(1))
        repo = repo_at(cwd)
        target = IssueRef(repo, number)
        if branch_name(cwd) not in linked_branch_names(target):
            return 0
        task, _ = resolve_task(repo, number)
    except LifecycleError:
        return 0
    if task.status in STARTED:
        return 0
    reason = (
        f"Issue #{number} is linked to this branch but its Project status is "
        f"{task.status or 'unset'}. Confirm Human Gate=No, then run gh-task-status set {number} "
        "'In Progress', or repair the linked branch before stopping."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="gh-task-status")
    commands = root.add_subparsers(dest="command", required=True)
    board = commands.add_parser("board")
    board.add_argument("repo", nargs="?")
    queue = commands.add_parser("queue")
    queue.add_argument("repo", nargs="?")
    show = commands.add_parser("show")
    show.add_argument("number", nargs="?")
    set_parser = commands.add_parser("set")
    set_parser.add_argument("number")
    set_parser.add_argument("option")
    verify = commands.add_parser("verify")
    verify.add_argument("number", nargs="?")
    preflight = commands.add_parser("preflight")
    preflight.add_argument("repo", nargs="?")
    hook = commands.add_parser("hook")
    hook.add_argument("event", choices=("pre", "stop"))
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "board":
            return command_board(args.repo)
        if args.command == "queue":
            return command_queue(args.repo)
        if args.command == "show":
            return command_show(args.number)
        if args.command == "set":
            return command_set(args.number, args.option)
        if args.command == "verify":
            return command_verify(args.number)
        if args.command == "preflight":
            return command_preflight(args.repo)
        if args.command == "hook" and args.event == "pre":
            return hook_pre()
        if args.command == "hook" and args.event == "stop":
            return hook_stop()
    except LifecycleError as exc:
        print(f"gh-task-status: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
