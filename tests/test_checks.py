"""Tests for deterministic and host package checks."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import threading
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


check = load("skiphow_check", "scripts/check.py")
hosts = load("skiphow_check_hosts", "scripts/check_hosts.py")


def test_local_dependencies_are_pinned() -> None:
    pins = check.pinned_requirements()
    assert {"pytest", "PyYAML", "markdown-it-py"} <= set(pins)
    assert all(re.fullmatch(r"\d+(?:\.\d+)*", value) for value in pins.values())


def test_checker_never_installs_dependencies_or_reaches_a_package_index() -> None:
    """Ordinary checks must not provision anything.

    The checker used to build a virtual environment and run `pip install` when a
    pin was unsatisfied, which put a package index on the path of an ordinary
    deterministic check. It now fails fast and names the one explicit command.
    """
    source = (ROOT / "scripts/check.py").read_text(encoding="utf-8")
    assert "import venv" not in source
    assert "EnvBuilder" not in source
    assert "execve" not in source
    # The only surviving mention of pip is the instruction handed to the operator.
    assert source.count("pip") == 1
    assert "python -m pip install -r {REQUIREMENTS.name}" in source
    assert not hasattr(check, "bootstrap_dependencies")
    assert not hasattr(check, "managed_python")
    assert not hasattr(check, "MANAGED_ENV")


def test_unsatisfied_pins_fail_fast_with_the_explicit_setup_command(capsys) -> None:
    def refuse(*args, **kwargs):
        raise AssertionError("the checker ran a subprocess for missing dependencies")

    with (
        patch.object(check, "requirements_satisfied", return_value=False),
        patch.object(
            check,
            "pinned_requirements",
            return_value={"skiphow-absent-package": "9.9.9"},
        ),
        patch.object(check.subprocess, "run", refuse),
    ):
        assert check.main([]) == 2
    error = capsys.readouterr().err
    assert "python -m pip install -r requirements-dev.txt" in error
    assert "skiphow-absent-package==9.9.9" in error
    assert "not installed" in error


def test_local_package_and_document_checks_pass() -> None:
    assert check.validate_json() == []
    assert check.validate_yaml() == []
    assert check.validate_markdown_links() == []
    assert check.portability_scan() == []
    assert check.validate_version() == []
    assert check.model_id_scan() == []
    assert check.validate_continuity_hook() == []
    assert check.validate_plugin_static() == []


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        (
            '<link rel="canonical" href="https://mzored.github.io/SkipHow/">',
            '<link rel="canonical" href="https://mzored.github.io/SkipHow/other/">',
            "canonical URL must be",
        ),
        (
            '<script type="application/ld+json">',
            '<script src="https://cdn.example.test/runtime.js"></script><script type="application/ld+json">',
            "no client runtime",
        ),
        (
            'href="assets/site.css"',
            'href="assets/missing.css"',
            "broken site link",
        ),
    ],
)
def test_site_validator_rejects_structural_regressions(
    tmp_path: Path, old: str, new: str, expected: str
) -> None:
    """Hard failures are what a reader or a host depends on (spec 11.3 classes 1 and 2)."""
    site = tmp_path / "site"
    shutil.copytree(ROOT / "site", site)
    homepage = site / "index.html"
    text = homepage.read_text(encoding="utf-8")
    assert old in text
    homepage.write_text(text.replace(old, new, 1), encoding="utf-8")

    with patch.object(check, "SITE_ROOT", site):
        assert any(expected in error for error in check.validate_site())


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        (
            '<meta property="og:image:alt" content="',
            '<meta property="og:image:alt" content="" data-was="',
            "og:image:alt",
        ),
        (
            '<div class="contract">',
            '<div class="contract" aria-label="Responsibility split">',
            "should not name a generic div",
        ),
        (
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
            "",
            "responsive viewport",
        ),
    ],
)
def test_site_presentation_preferences_are_non_blocking_lint(
    tmp_path: Path, old: str, new: str, expected: str
) -> None:
    """Presentation details are lint, never a failed run (spec 11.2, 11.3 class 4)."""
    site = tmp_path / "site"
    shutil.copytree(ROOT / "site", site)
    homepage = site / "index.html"
    text = homepage.read_text(encoding="utf-8")
    assert old in text
    homepage.write_text(text.replace(old, new, 1), encoding="utf-8")

    lint: list[str] = []
    with patch.object(check, "SITE_ROOT", site):
        errors = check.validate_site(lint)
    assert errors == []
    assert any(expected in warning for warning in lint), lint


def test_site_copy_is_not_pinned_to_a_category_phrase(tmp_path: Path) -> None:
    """A search-positioning phrase is not a package or host contract (spec 11.2)."""
    site = tmp_path / "site"
    shutil.copytree(ROOT / "site", site)
    for page in site.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        page.write_text(
            re.sub("outcome-first orchestration", "method selection", text, flags=re.IGNORECASE),
            encoding="utf-8",
        )
    with patch.object(check, "SITE_ROOT", site):
        assert check.validate_site() == []


def write_skill(root: Path, name: str, *, description: str = "Handle a focused task.") -> Path:
    skill = root / name
    (skill / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\nDo the task.\n",
        encoding="utf-8",
    )
    (skill / "agents/openai.yaml").write_text(
        "interface:\n"
        f"  display_name: {name}\n"
        "  short_description: Handle one focused project task\n"
        f"  default_prompt: Use ${name} for this request.\n"
        "policy:\n"
        "  allow_implicit_invocation: true\n",
        encoding="utf-8",
    )
    return skill


def test_each_top_level_skill_has_spec_metadata_and_may_ship_resources(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, "diagnosing-bugs")
    for directory in ("references", "scripts", "assets"):
        (skill / directory).mkdir()
        (skill / directory / "resource.txt").write_text("resource\n", encoding="utf-8")
    (skill / "examples").mkdir()
    (skill / "examples/scenario.txt").write_text("example\n", encoding="utf-8")
    (skill / "LICENSE.txt").write_text("local terms\n", encoding="utf-8")
    assert check.validate_skill_directory(skill) == []

    (skill / "SKILL.md").write_text(
        "---\nname: wrong-name\ndescription: x\n---\n\nBody.\n", encoding="utf-8"
    )
    assert any("name must match its directory" in error for error in check.validate_skill_directory(skill))


def test_openai_metadata_is_optional_but_cannot_disable_implicit_use(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, "diagnosing-bugs")
    metadata_path = skill / "agents/openai.yaml"
    metadata_path.unlink()
    (skill / "agents/other-host.yaml").write_text("enabled: true\n", encoding="utf-8")
    assert check.validate_skill_directory(skill) == []

    metadata_path.write_text(
        "policy:\n  allow_implicit_invocation: true\n",
        encoding="utf-8",
    )
    assert check.validate_skill_directory(skill) == []

    metadata_path.write_text(
        "interface:\n"
        "  display_name: Investigate product failures\n"
        "  short_description: Handle one focused project task\n"
        "  default_prompt: Investigate this failure.\n"
        "policy:\n"
        "  allow_implicit_invocation: false\n",
        encoding="utf-8",
    )
    assert any(
        "must not disable implicit invocation" in error
        for error in check.validate_skill_directory(skill)
    )

    metadata_path.write_text(
        "policy:\n  allow_implicit_invocation: true\n"
        "dependencies:\n  tools:\n    - type: mcp\n",
        encoding="utf-8",
    )
    assert any(
        "may contain only interface and policy" in error
        for error in check.validate_skill_directory(skill)
    )


@pytest.mark.parametrize(
    ("extra_frontmatter", "expected"),
    [
        ("license:\n  - MIT\n", "license must be a nonempty string"),
        ("license: null\n", "license must be a nonempty string"),
        (f"compatibility: {'x' * 501}\n", "compatibility must be"),
        ("metadata:\n  version: 2\n", "metadata must map strings to strings"),
        ("allowed-tools:\n  - Bash\n", "allowed-tools must be a nonempty string"),
        ("made-up-field: value\n", "unsupported Agent Skills fields"),
    ],
)
def test_skill_frontmatter_rejects_invalid_optional_fields(
    tmp_path: Path, extra_frontmatter: str, expected: str
) -> None:
    skill = write_skill(tmp_path, "research")
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: research\n"
        "description: Research one uncertain question.\n"
        f"{extra_frontmatter}"
        "---\n\nBody.\n",
        encoding="utf-8",
    )
    assert any(expected in error for error in check.validate_skill_directory(skill))


def test_skill_frontmatter_accepts_valid_optional_fields(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, "research")
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: research\n"
        "description: Research one uncertain question.\n"
        "license: MIT\n"
        "compatibility: Requires access to current primary sources.\n"
        "metadata:\n"
        "  author: example\n"
        "allowed-tools: Read Bash\n"
        "---\n\nBody.\n",
        encoding="utf-8",
    )
    assert check.validate_skill_directory(skill) == []


def test_skill_frontmatter_rejects_non_string_keys_without_crashing(
    tmp_path: Path,
) -> None:
    skill = write_skill(tmp_path, "research")
    (skill / "SKILL.md").write_text(
        "---\nname: research\ndescription: Research carefully.\n1: invalid\n"
        "---\n\nBody.\n",
        encoding="utf-8",
    )
    errors = check.validate_skill_directory(skill)
    assert any("frontmatter keys must be strings" in error for error in errors)


def test_skill_description_uses_the_agent_skills_metadata_limit(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, "research", description="x" * 1025)
    errors = check.validate_skill_directory(skill)
    assert any("at most 1024 characters" in error for error in errors)


def test_plugin_markdown_links_cannot_escape_the_package(tmp_path: Path) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "skiphow")
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        "---\nname: skiphow\ndescription: Owner entry.\n---\n\n"
        "[outside](../../../outside.md)\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        errors = check.validate_plugin_links()
    assert any("escapes package" in error for error in errors)


def test_plugin_markdown_links_validate_image_destinations(tmp_path: Path) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "skiphow")
    (skill / "SKILL.md").write_text(
        "---\nname: skiphow\ndescription: Owner entry.\n---\n\n"
        "![missing preview](assets/missing.png)\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        errors = check.validate_plugin_links()
    assert any("missing.png" in error for error in errors)


def test_markdown_references_must_be_reachable_from_their_skill(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, "research")
    references = skill / "references"
    (references / "nested").mkdir(parents=True)
    (references / "first.md").write_text("[Details](nested/details.md)\n", encoding="utf-8")
    (references / "nested/details.md").write_text("Details.\n", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        "---\nname: research\ndescription: Research one uncertain question.\n---\n\n"
        "Read [the method](references/first.md) when needed.\n",
        encoding="utf-8",
    )
    assert check.validate_skill_directory(skill) == []

    (references / "orphan.md").write_text("Unreachable.\n", encoding="utf-8")
    errors = check.validate_skill_directory(skill)
    assert any("unreachable Markdown reference: references/orphan.md" in error for error in errors)


@pytest.mark.parametrize("filename", ["orphan.MD", "orphan.markdown", "orphan.MARKDOWN"])
def test_markdown_suffixes_cannot_evade_reachability_or_links(
    tmp_path: Path, filename: str,
) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "skiphow")
    references = skill / "references"
    references.mkdir()
    orphan = references / filename
    orphan.write_text("Unreachable.\n", encoding="utf-8")
    errors = check.validate_skill_directory(skill)
    assert any(f"references/{filename}" in error for error in errors)

    orphan.write_text("[missing](missing.txt)\n", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        "---\nname: skiphow\ndescription: Owner entry.\n---\n\n"
        f"Read [the note](references/{filename}).\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        errors = check.validate_plugin_links()
    assert any("missing.txt" in error for error in errors)


@pytest.mark.parametrize(
    "target",
    [
        "file:///etc/passwd",
        "file:../../outside.md",
        "f%69le:///etc/passwd",
        "C:/Windows/win.ini",
        "C:Windows/win.ini",
        "//server/share/outside.md",
        "..%5C..%5Coutside.md",
        "http://[",
        "a%00b.md",
        "javascript:alert(1)",
        "data:text/html,unsafe",
        "%68ttps://example.test/looks-remote",
    ],
)
def test_plugin_markdown_rejects_local_file_uri_and_windows_paths(
    tmp_path: Path, target: str
) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "skiphow")
    (skill / "SKILL.md").write_text(
        "---\nname: skiphow\ndescription: Owner entry.\n---\n\n"
        f"[unsafe]({target})\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        errors = check.validate_plugin_links()
    assert any("local-file link is not allowed" in error for error in errors), target


def test_plugin_markdown_rejects_raw_html_links_and_images(tmp_path: Path) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "skiphow")
    (skill / "SKILL.md").write_text(
        "---\nname: skiphow\ndescription: Owner entry.\n---\n\n"
        '<a href="file:///etc/passwd">unsafe</a>\n'
        '<img src="../../outside.png">\n',
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        errors = check.validate_plugin_links()
    assert any("must not contain raw HTML" in error for error in errors)


def test_plugin_markdown_does_not_treat_innocent_prose_as_a_destination(
    tmp_path: Path,
) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "skiphow")
    references = skill / "references"
    references.mkdir()
    for filename in ("foo&copy.md", "foo&notit.md"):
        (references / filename).write_text("Safe.\n", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        "---\nname: skiphow\ndescription: Owner entry.\n---\n\n"
        "Use \\* to explain a Markdown escape.\n\n"
        "The file: report is ready. C:\\Temp\\x is prose.\n\n"
        "Read [copy](references/foo&copy.md) and [notit](references/foo&notit.md).\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        assert check.validate_plugin_links() == []
    assert check.validate_skill_markdown_reachability(skill) == []


def test_local_links_decode_one_uri_layer_without_rewriting_literal_names(
    tmp_path: Path,
) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "skiphow")
    references = skill / "references"
    references.mkdir()
    (references / "foo&copy;.md").write_text("Safe.\n", encoding="utf-8")
    (references / "foo%20bar.md").write_text("Safe.\n", encoding="utf-8")
    (references / "foo#bar.md").write_text("Safe.\n", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        "---\nname: skiphow\ndescription: Owner entry.\n---\n\n"
        "Read [literal entity](references/foo\\&copy;.md) and "
        "[encoded percent](references/foo%2520bar.md) and "
        "[encoded hash](references/foo%23bar.md).\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        assert check.validate_plugin_links() == []
    assert check.validate_skill_markdown_reachability(skill) == []
    assert check.local_link(skill / "SKILL.md", "references/foo%3Fbar.md").name == (
        "foo?bar.md"
    )


@pytest.mark.parametrize("target", ["http://[", "a%00b.md", "file:///etc/passwd"])
def test_repository_markdown_link_errors_are_reported(
    tmp_path: Path, target: str
) -> None:
    candidate = tmp_path / "README.md"
    candidate.write_text(f"[unsafe]({target})\n", encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "repository_files", return_value=[candidate]),
    ):
        errors = check.validate_markdown_links()
    assert any("local-file link is not allowed" in error for error in errors)


def test_repository_markdown_reports_invalid_utf8(tmp_path: Path) -> None:
    candidate = tmp_path / "README.markdown"
    candidate.write_bytes(b"\xff\xfe")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "repository_files", return_value=[candidate]),
    ):
        errors = check.validate_markdown_links()
    assert any("cannot read Markdown" in error for error in errors)


def test_adapted_source_manifest_validates_provenance_not_upstream_hashes(tmp_path: Path) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "diagnosing-bugs")
    commit = "a" * 40
    repository = "https://example.test/upstream/skills"
    provenance = "Adapted for this package"
    copyright_notice = "Copyright (c) 2026 Example Author"
    (plugin / "THIRD_PARTY_NOTICES.md").write_text(
        f"Source: {repository}\nCommit: {commit}\nLicense: MIT\n{provenance}\n\n"
        f"MIT License\n\n{copyright_notice}\n\n{check.MIT_PERMISSION_PARAGRAPH}\n\n"
        f"{check.MIT_CONDITION_PARAGRAPH}\n\n{check.MIT_WARRANTY_PARAGRAPH}\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "sources": [
            {
                "repository": repository,
                "commit": commit,
                "license": "MIT",
                "copyright": copyright_notice,
                "provenance": provenance,
                "adaptations": [
                    {
                        "skill": "diagnosing-bugs",
                        "source_paths": ["skills/engineering/diagnosing-bugs/SKILL.md"],
                        "files": ["SKILL.md"],
                    }
                ],
            }
        ],
    }
    (plugin / "SOURCES.json").write_text(json.dumps(manifest), encoding="utf-8")
    with patch.object(check, "PLUGIN_ROOT", plugin):
        assert check.validate_third_party_sources({"diagnosing-bugs"}) == []
        (plugin / "THIRD_PARTY_NOTICES.md").write_text(
            f"{repository}\n{commit}\nMIT\n{provenance}\nMIT License\n"
            f"{copyright_notice}\n{check.MIT_PERMISSION_PARAGRAPH}\n"
            f"{check.MIT_CONDITION_PARAGRAPH}\n",
            encoding="utf-8",
        )
        errors = check.validate_third_party_sources({"diagnosing-bugs"})
        assert any("canonical MIT warranty paragraph" in error for error in errors)

        (plugin / "THIRD_PARTY_NOTICES.md").write_text(
            f"{repository}\n{commit}\nMIT\nMIT License\n{copyright_notice}\n"
            f"{check.MIT_PERMISSION_PARAGRAPH}\n{check.MIT_CONDITION_PARAGRAPH}\n"
            f"{check.MIT_WARRANTY_PARAGRAPH}\n",
            encoding="utf-8",
        )
        errors = check.validate_third_party_sources({"diagnosing-bugs"})
        assert any("source provenance" in error for error in errors)

        manifest["sources"][0]["commit"] = "moving-main"
        (plugin / "SOURCES.json").write_text(json.dumps(manifest), encoding="utf-8")
        errors = check.validate_third_party_sources({"diagnosing-bugs"})
    assert any("40-character hexadecimal" in error for error in errors)


def test_adapted_source_schema_is_fail_closed_and_allows_multiple_sources(
    tmp_path: Path,
) -> None:
    plugin = tmp_path / "skiphow"
    write_skill(plugin / "skills", "skiphow")

    def source(index: int) -> dict[str, object]:
        return {
            "repository": f"https://example.test/upstream/{index}",
            "commit": str(index) * 40,
            "license": "MIT",
            "copyright": f"Copyright (c) 2026 Example {index}",
            "adaptations": [
                {
                    "skill": "skiphow",
                    "source_paths": ["skills/skiphow/SKILL.md"],
                    "files": ["SKILL.md"],
                }
            ],
        }

    sources = [source(1), source(2)]
    notices = []
    for item in sources:
        notices.append(
            f"{item['repository']}\n{item['commit']}\nMIT\nMIT License\n\n"
            f"{item['copyright']}\n\n{check.MIT_PERMISSION_PARAGRAPH}\n\n"
            f"{check.MIT_CONDITION_PARAGRAPH}\n\n{check.MIT_WARRANTY_PARAGRAPH}"
        )
    (plugin / "THIRD_PARTY_NOTICES.md").write_text(
        "\n\n".join(notices) + "\n", encoding="utf-8"
    )
    manifest = {"schema_version": 1, "sources": sources}
    sources_path = plugin / "SOURCES.json"
    sources_path.write_text(json.dumps(manifest), encoding="utf-8")
    with patch.object(check, "PLUGIN_ROOT", plugin):
        assert check.validate_third_party_sources({"skiphow"}) == []

        for mutation, expected in (
            (("schema_version", True), "integer 1"),
            (("schema_version", 2), "integer 1"),
            (("files", None), "files must be a nonempty list"),
            (("source_paths", ["https://example.test/x"]), "relative POSIX path"),
            (("source_paths", [r"dir\file.md"]), "relative POSIX path"),
            (("source_paths", ["."]), "relative POSIX path"),
        ):
            candidate = json.loads(json.dumps(manifest))
            field, value = mutation
            if field == "schema_version":
                candidate[field] = value
            elif value is None:
                del candidate["sources"][0]["adaptations"][0][field]
            else:
                candidate["sources"][0]["adaptations"][0][field] = value
            sources_path.write_text(json.dumps(candidate), encoding="utf-8")
            assert any(
                expected in error
                for error in check.validate_third_party_sources({"skiphow"})
            )

        candidates = []
        candidate = json.loads(json.dumps(manifest))
        candidate["unexpected"] = True
        candidates.append(candidate)
        candidate = json.loads(json.dumps(manifest))
        candidate["sources"][0]["unexpected"] = True
        candidates.append(candidate)
        candidate = json.loads(json.dumps(manifest))
        candidate["sources"][0]["adaptations"][0]["unexpected"] = True
        candidates.append(candidate)
        for candidate in candidates:
            sources_path.write_text(json.dumps(candidate), encoding="utf-8")
            assert check.validate_third_party_sources({"skiphow"}) != []

        candidate = json.loads(json.dumps(manifest))
        candidate["sources"][0]["repository"] = "https://["
        sources_path.write_text(json.dumps(candidate), encoding="utf-8")
        assert any(
            "HTTPS source URL" in error
            for error in check.validate_third_party_sources({"skiphow"})
        )

        candidate = json.loads(json.dumps(manifest))
        candidate["sources"][0]["license"] = "MIT License"
        sources_path.write_text(json.dumps(candidate), encoding="utf-8")
        assert any(
            "exact SPDX identifier MIT" in error
            for error in check.validate_third_party_sources({"skiphow"})
        )

        candidate = json.loads(json.dumps(manifest))
        candidate["sources"][0]["adaptations"][0]["files"] = ["a\u0000b.md"]
        sources_path.write_text(json.dumps(candidate), encoding="utf-8")
        assert any(
            "normalized relative POSIX path" in error
            for error in check.validate_third_party_sources({"skiphow"})
        )


def test_mit_source_requires_one_complete_copyright_notice(tmp_path: Path) -> None:
    plugin = tmp_path / "skiphow"
    write_skill(plugin / "skills", "skiphow")
    source = {
        "repository": "https://example.test/source",
        "commit": "a" * 40,
        "license": "MIT",
        "provenance": "Adapted here",
        "adaptations": [
            {
                "skill": "skiphow",
                "source_paths": ["skills/skiphow/SKILL.md"],
                "files": ["SKILL.md"],
            }
        ],
    }
    (plugin / "SOURCES.json").write_text(
        json.dumps({"schema_version": 1, "sources": [source]}), encoding="utf-8"
    )
    (plugin / "THIRD_PARTY_NOTICES.md").write_text(
        f"{source['repository']}\n{source['commit']}\nMIT\nAdapted here\n"
        f"{check.MIT_PERMISSION_PARAGRAPH}\n{check.MIT_CONDITION_PARAGRAPH}\n"
        f"{check.MIT_WARRANTY_PARAGRAPH}\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        errors = check.validate_third_party_sources({"skiphow"})
    assert any("MIT source copyright must be present" in error for error in errors)

    copyright_notice = "Copyright (c) 2026 Example"
    source["copyright"] = copyright_notice
    (plugin / "SOURCES.json").write_text(
        json.dumps({"schema_version": 1, "sources": [source]}), encoding="utf-8"
    )
    (plugin / "THIRD_PARTY_NOTICES.md").write_text(
        f"{source['repository']}\n{source['commit']}\nMIT\nAdapted here\nMIT License\n"
        f"{copyright_notice}\n{check.MIT_PERMISSION_PARAGRAPH}\n"
        f"{check.MIT_WARRANTY_PARAGRAPH}\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        errors = check.validate_third_party_sources({"skiphow"})
    assert any("canonical MIT condition paragraph" in error for error in errors)


def test_current_package_cannot_drop_third_party_provenance(tmp_path: Path) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    (package / "SOURCES.json").unlink()
    (package / "THIRD_PARTY_NOTICES.md").unlink()
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("SOURCES.json" in error and "THIRD_PARTY_NOTICES.md" in error for error in errors)


def validate_hook_payload(tmp_path: Path, payload: object) -> list[str]:
    hooks = tmp_path / "hooks"
    hooks.mkdir(exist_ok=True)
    path = hooks / "hooks.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with patch.object(check, "PLUGIN_ROOT", tmp_path):
        return check.validate_continuity_hook(path)


def real_hook_payload() -> dict[str, object]:
    return {
        "description": "test reminder",
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|clear",
                    "hooks": [{"type": "command", "command": "echo 'test'", "timeout": 10}],
                },
                {
                    "matcher": "compact|resume",
                    "hooks": [{"type": "command", "command": "echo 'resume'", "timeout": 10}],
                },
            ]
        },
    }


def test_continuity_hook_rejects_other_events_and_unsafe_commands(tmp_path: Path) -> None:
    wrong_event = {
        "description": "wrong event",
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {"type": "command", "command": "echo 'wrong'", "timeout": 10}
                    ],
                }
            ]
        },
    }
    assert any("only SessionStart" in error for error in validate_hook_payload(tmp_path, wrong_event))

    unsafe = real_hook_payload()
    unsafe["hooks"]["SessionStart"][0]["hooks"][0]["command"] = "curl https://example.test"
    assert any("safe echo-literal" in error for error in validate_hook_payload(tmp_path, unsafe))

    # Matcher topology is editorial: regrouping the four sources is accepted, an
    # unknown source or a duplicated one is not.
    mixed = real_hook_payload()
    mixed["hooks"]["SessionStart"][0]["matcher"] = "startup|compact"
    mixed["hooks"]["SessionStart"][1]["matcher"] = "clear|resume"
    assert validate_hook_payload(tmp_path, mixed) == []
    one_group = real_hook_payload()
    one_group["hooks"]["SessionStart"] = one_group["hooks"]["SessionStart"][:1]
    one_group["hooks"]["SessionStart"][0]["matcher"] = "startup|clear|compact|resume"
    assert validate_hook_payload(tmp_path, one_group) == []
    unknown = real_hook_payload()
    unknown["hooks"]["SessionStart"][0]["matcher"] = "startup|PreToolUse"
    assert any("distinct SessionStart sources" in error for error in validate_hook_payload(tmp_path, unknown))


def test_continuity_hook_schema_rejects_every_behavioral_escape(tmp_path: Path) -> None:
    mutations: list[tuple[str, object]] = []

    payload = real_hook_payload()
    payload["description"] = False
    mutations.append(("description", payload))
    payload = real_hook_payload()
    payload["commandWindows"] = "danger"
    mutations.append(("unsupported top-level", payload))
    payload = real_hook_payload()
    payload["hooks"]["SessionStart"][0]["extra"] = True
    mutations.append(("unsupported fields", payload))
    payload = real_hook_payload()
    payload["hooks"]["SessionStart"][0]["matcher"] = "startup | clear"
    mutations.append(("distinct SessionStart sources", payload))
    for command in (
        "echo 'Read .skiphow before resuming'",
        "echo 'Read handoff.md before resuming'",
    ):
        payload = real_hook_payload()
        payload["hooks"]["SessionStart"][1]["hooks"][0]["command"] = command
        mutations.append(("must not select handoff state", payload))

    for field in ("commandWindows", "args", "shell", "if", "async", "statusMessage"):
        payload = real_hook_payload()
        payload["hooks"]["SessionStart"][0]["hooks"][0][field] = True
        mutations.append(("unsupported fields", payload))
    for timeout in (True, 0, -1, "10", check.HOOK_TIMEOUT_CEILING + 1):
        payload = real_hook_payload()
        payload["hooks"]["SessionStart"][0]["hooks"][0]["timeout"] = timeout
        mutations.append(("positive integer", payload))
    for field in ("type", "command"):
        payload = real_hook_payload()
        payload["hooks"]["SessionStart"][0]["hooks"][0][field] = False
        mutations.append((f"{field} must", payload))

    for expected, candidate in mutations:
        assert any(
            expected in error for error in validate_hook_payload(tmp_path, candidate)
        ), (expected, candidate)


def test_plugin_change_requires_a_version_bump() -> None:
    with (
        patch.object(
            check,
            "checked_null_paths",
            side_effect=[
                (True, {"plugins/skiphow/skills/skiphow/SKILL.md"}),
                (True, set()),
                (True, set()),
            ],
        ),
        patch.object(
            check,
            "checked",
            return_value=(True, (check.ROOT / "VERSION").read_text(encoding="utf-8")),
        ),
    ):
        assert check.validate_release_version_change("base") == [
            "plugins/skiphow changed without a VERSION bump"
        ]


@pytest.mark.parametrize(
    ("working_tree", "untracked"),
    [
        ("plugins/skiphow/skills/tracked/SKILL.md\n", ""),
        ("", "plugins/skiphow/skills/untracked/SKILL.md\n"),
    ],
)
def test_base_diff_cannot_hide_dirty_plugin_changes(
    working_tree: str, untracked: str
) -> None:
    with (
        patch.object(
            check,
            "checked_null_paths",
            side_effect=[
                (True, {"docs/release-notes.md"}),
                (True, {working_tree.strip()} if working_tree else set()),
                (True, {untracked.strip()} if untracked else set()),
            ],
        ) as checked_paths,
        patch.object(
            check,
            "checked",
            return_value=(True, (check.ROOT / "VERSION").read_text(encoding="utf-8")),
        ),
    ):
        assert check.validate_release_version_change("base") == [
            "plugins/skiphow changed without a VERSION bump"
        ]
    assert [call.args[0] for call in checked_paths.call_args_list] == [
        ["git", "diff", "--name-only", "--no-renames", "-z", "base...HEAD"],
        ["git", "diff", "--name-only", "--no-renames", "-z", "HEAD"],
        ["git", "ls-files", "-z", "--others", "--exclude-standard"],
    ]


def test_working_tree_plugin_change_requires_a_version_bump_without_base() -> None:
    with (
        patch.object(
            check, "infer_stable_release_base", return_value=(True, "v1.0.0")
        ),
        patch.object(
            check,
            "checked_null_paths",
            side_effect=[
                (True, set()),
                (True, {"plugins/skiphow/skills/new-skill/SKILL.md"}),
                (True, {"plugins/skiphow/skills/untracked/SKILL.md"}),
            ],
        ),
        patch.object(
            check,
            "checked",
            return_value=(True, (check.ROOT / "VERSION").read_text(encoding="utf-8")),
        ),
    ):
        assert check.validate_release_version_change(None) == [
            "plugins/skiphow changed without a VERSION bump"
        ]


def test_release_delta_reports_an_unreadable_current_version(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(
            check, "infer_stable_release_base", return_value=(True, "v1.0.0")
        ),
        patch.object(
            check,
            "checked_null_paths",
            side_effect=[
                (True, {"plugins/skiphow/skills/skiphow/SKILL.md"}),
                (True, set()),
                (True, set()),
            ],
        ),
        patch.object(check, "checked", return_value=(True, "1.0.0\n")),
    ):
        errors = check.validate_release_version_change(None)
    assert any("cannot read current VERSION" in error for error in errors)


def test_clean_committed_plugin_change_uses_the_inferred_release_tag(
    tmp_path: Path,
) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(
            check, "infer_stable_release_base", return_value=(True, "v1.0.0")
        ),
        patch.object(
            check,
            "checked_null_paths",
            side_effect=[
                (True, {"plugins/skiphow/skills/skiphow/SKILL.md"}),
                (True, set()),
                (True, set()),
            ],
        ) as checked_paths,
        patch.object(check, "checked", return_value=(True, "1.0.0\n")),
    ):
        assert check.validate_release_version_change(None) == [
            "plugins/skiphow changed without a VERSION bump"
        ]
    assert checked_paths.call_args_list[0].args[0][-1] == "v1.0.0...HEAD"


def test_release_baseline_selects_the_nearest_reachable_stable_tag() -> None:
    def checked(command, **_kwargs):
        if command[:2] == ["git", "tag"]:
            return True, "v1.0.0\nv1.1.0\nv1.2.0-rc.1\nnot-a-version\n"
        distances = {"v1.0.0..HEAD": "4", "v1.1.0..HEAD": "1"}
        return True, distances[command[-1]]

    with patch.object(check, "checked", side_effect=checked):
        assert check.infer_stable_release_base() == (True, "v1.1.0")


def test_release_baseline_excludes_a_stable_tag_pointing_at_head() -> None:
    def checked(command, **_kwargs):
        if command[:2] == ["git", "tag"]:
            return True, "v1.0.0\nv1.1.0\n"
        distances = {"v1.0.0..HEAD": "3", "v1.1.0..HEAD": "0"}
        return True, distances[command[-1]]

    with patch.object(check, "checked", side_effect=checked):
        assert check.infer_stable_release_base() == (True, "v1.0.0")


def test_non_plugin_change_does_not_require_a_version_bump() -> None:
    with patch.object(
        check,
        "checked_null_paths",
        side_effect=[
            (True, {"docs/README.md"}),
            (True, set()),
            (True, set()),
        ],
    ):
        assert check.validate_release_version_change("base") == []


def test_plugin_version_cannot_move_backward() -> None:
    current = (check.ROOT / "VERSION").read_text(encoding="utf-8").strip()
    major, minor, patch_number = (int(part) for part in current.split("."))
    ahead = f"{major + 1}.{minor}.{patch_number}"
    with (
        patch.object(
            check,
            "checked_null_paths",
            side_effect=[
                (True, {"plugins/skiphow/skills/skiphow/SKILL.md"}),
                (True, set()),
                (True, set()),
            ],
        ),
        patch.object(check, "checked", return_value=(True, f"{ahead}\n")),
    ):
        assert check.validate_release_version_change("base") == [
            f"plugin version must increase from {ahead} to a later stable version"
        ]


def test_release_delta_decodes_nul_delimited_unicode_and_newline_paths() -> None:
    raw = (
        "plugins/skiphow/résumé.md\0"
        "plugins/skiphow/line\nbreak.MD\0"
        "docs/outside.md\0"
    ).encode()
    completed = check.subprocess.CompletedProcess(["git"], 0, raw, b"")
    with patch.object(check.subprocess, "run", return_value=completed):
        passed, paths = check.checked_null_paths(
            ["git", "diff", "--name-only", "--no-renames", "-z", "HEAD"]
        )
    assert passed
    assert paths == {
        "plugins/skiphow/résumé.md",
        "plugins/skiphow/line\nbreak.MD",
        "docs/outside.md",
    }


def test_rename_out_still_requires_a_plugin_version_bump() -> None:
    current = (check.ROOT / "VERSION").read_text(encoding="utf-8")
    with (
        patch.object(
            check,
            "checked_null_paths",
            side_effect=[
                (
                    True,
                    {
                        "plugins/skiphow/skills/skiphow/agents/openai.yaml",
                        "docs/openai.yaml",
                    },
                ),
                (True, set()),
                (True, set()),
            ],
        ) as checked_paths,
        patch.object(check, "checked", return_value=(True, current)),
    ):
        assert check.validate_release_version_change("base") == [
            "plugins/skiphow changed without a VERSION bump"
        ]
    assert "--no-renames" in checked_paths.call_args_list[0].args[0]
    assert "-z" in checked_paths.call_args_list[0].args[0]


def test_diff_validation_checks_unstaged_staged_and_candidate_changes() -> None:
    commands: list[list[str]] = []

    def checked(command, **kwargs):
        commands.append(list(command))
        return True, ""

    with patch.object(check, "checked", side_effect=checked):
        assert check.validate_diff("origin/main") == []
    assert commands == [
        ["git", "diff", "--check"],
        ["git", "diff", "--cached", "--check"],
        ["git", "diff", "--check", "origin/main...HEAD"],
    ]


def test_portable_policy_rejects_provider_model_ids(tmp_path: Path) -> None:
    policy = tmp_path / "policy.md"
    policy.write_text("Use gpt-5.6-example for this lane.\n", encoding="utf-8")
    errors = check.model_id_scan([policy])
    assert len(errors) == 1
    assert "gpt-5.6-example" in errors[0]


def test_file_enumeration_asks_git_for_untracked_files() -> None:
    """The scan can only see a new file if the enumerator asks Git for one."""
    with patch.object(check.subprocess, "run") as run:
        run.return_value = check.subprocess.CompletedProcess(["git"], 0, b"", b"")
        list(check.repository_files())
    command = run.call_args.args[0]
    assert command[:2] == ["git", "ls-files"]
    assert {"--others", "--exclude-standard", "--cached"} <= set(command)
    assert run.call_args.kwargs["timeout"]


def test_portability_scan_flags_a_personal_path_in_a_package_file(tmp_path: Path) -> None:
    """The scan reports a file the enumerator yields -- proven off the real package."""
    plugin = tmp_path / "plugins/skiphow"
    plugin.mkdir(parents=True)
    untracked = plugin / "personal-path.txt"
    untracked.write_text("/" + "Users/person/secret\n", encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[untracked]),
    ):
        errors = check.portability_scan()
    assert any("personal-path.txt" in error for error in errors)


def test_portability_scan_catches_a_home_path_with_no_trailing_separator(tmp_path: Path) -> None:
    """`/Users/person` at the end of a sentence used to pass the scan."""
    plugin = tmp_path / "plugins/skiphow"
    plugin.mkdir(parents=True)
    candidate = plugin / "note.md"
    candidate.write_text("Run it from /" + "Users/person.\n", encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[candidate]),
    ):
        assert check.portability_scan() != []


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("escaped.json", '{"path": "/\\u0055sers/alice"}\n'),
        ("escaped.yaml", 'path: "/\\u0055sers/alice"\n'),
    ],
)
def test_portability_scan_reads_decoded_structured_strings(
    tmp_path: Path, filename: str, content: str
) -> None:
    plugin = tmp_path / "plugins/skiphow"
    plugin.mkdir(parents=True)
    candidate = plugin / filename
    candidate.write_text(content, encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[candidate]),
    ):
        assert any("/Users/alice" in error for error in check.portability_scan())


@pytest.mark.parametrize(
    "content",
    [
        "gpt&#45;5.6\n",
        r"gpt\-5.6" + "\n",
        "gpt-**5.6**\n",
    ],
)
def test_model_scan_reads_commonmark_rendered_text(tmp_path: Path, content: str) -> None:
    candidate = tmp_path / "policy.md"
    candidate.write_text(content, encoding="utf-8")
    assert any("gpt-5.6" in error for error in check.model_id_scan([candidate]))


@pytest.mark.parametrize(
    "target",
    [
        "https://example.test/gpt%2D5.6",
        "https://example.test/gpt&#45;5.6",
        "https://example.test/gpt&amp;#45;5.6",
    ],
)
def test_model_scan_reads_decoded_markdown_destinations(
    tmp_path: Path, target: str
) -> None:
    candidate = tmp_path / "policy.markdown"
    candidate.write_text(f"[model]({target})\n", encoding="utf-8")
    assert any("gpt-5.6" in error for error in check.model_id_scan([candidate]))


@pytest.mark.parametrize(
    "content",
    [
        '[model](https://example.test "gpt&#45;5.6")\n',
        '![model](https://example.test/x.png "gpt&amp;#45;5.6")\n',
        "![gpt-**5.6**](https://example.test/x.png)\n",
    ],
)
def test_model_scan_reads_decoded_markdown_titles(
    tmp_path: Path, content: str
) -> None:
    candidate = tmp_path / "policy.md"
    candidate.write_text(content, encoding="utf-8")
    assert any("gpt-5.6" in error for error in check.model_id_scan([candidate]))


@pytest.mark.parametrize(
    "target",
    [
        "https://example.test/?path=%252FUsers/alice",
        "https://example.test/?path=&#47;Users/alice",
    ],
)
def test_portability_scan_reads_decoded_markdown_destinations(
    tmp_path: Path, target: str
) -> None:
    plugin = tmp_path / "plugins/skiphow"
    plugin.mkdir(parents=True)
    candidate = plugin / "policy.md"
    candidate.write_text(f"[home]({target})\n", encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[candidate]),
    ):
        assert any("/Users/alice" in error for error in check.portability_scan())


def test_portability_scan_reads_decoded_markdown_titles(tmp_path: Path) -> None:
    plugin = tmp_path / "plugins/skiphow"
    plugin.mkdir(parents=True)
    candidate = plugin / "policy.md"
    candidate.write_text(
        '[home](https://example.test "path=&#47;Users/alice")\n',
        encoding="utf-8",
    )
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[candidate]),
    ):
        assert any("/Users/alice" in error for error in check.portability_scan())


def test_portability_scan_reads_commonmark_rendered_paths(tmp_path: Path) -> None:
    plugin = tmp_path / "plugins/skiphow"
    plugin.mkdir(parents=True)
    candidate = plugin / "policy.md"
    candidate.write_text("/Us&#101;rs/**alice**\n", encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[candidate]),
    ):
        assert any("/Users/alice" in error for error in check.portability_scan())


def test_policy_scans_decode_skill_frontmatter_independently(tmp_path: Path) -> None:
    plugin = tmp_path / "plugins/skiphow"
    skill = plugin / "skills/skiphow/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        '---\nname: skiphow\ndescription: "Use \\u0067pt-5.6 at /\\u0055sers/alice"\n'
        "---\n\nBody.\n",
        encoding="utf-8",
    )
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[skill]),
    ):
        assert any("gpt-5.6" in error for error in check.model_id_scan([skill]))
        assert any("/Users/alice" in error for error in check.portability_scan())


def test_bad_skill_frontmatter_cannot_suppress_rendered_markdown_scan(tmp_path: Path) -> None:
    candidate = tmp_path / "SKILL.md"
    candidate.write_text(
        "---\ndescription: [\n---\n\ngpt&#45;5.6\n", encoding="utf-8"
    )
    assert any("gpt-5.6" in error for error in check.model_id_scan([candidate]))


def test_json_and_yaml_duplicate_keys_are_rejected(tmp_path: Path) -> None:
    json_path = tmp_path / "duplicate.json"
    yaml_path = tmp_path / "duplicate.yaml"
    json_path.write_text('{"name": "first", "name": "second"}\n', encoding="utf-8")
    yaml_path.write_text("name: first\nname: second\n", encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "repository_files", return_value=[json_path]),
    ):
        assert any("duplicate JSON field" in error for error in check.validate_json())
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "repository_files", return_value=[yaml_path]),
    ):
        assert any("duplicate key" in error for error in check.validate_yaml())


def test_semantic_scans_handle_recursive_yaml_aliases(tmp_path: Path) -> None:
    candidate = tmp_path / "recursive.yaml"
    candidate.write_text(
        'loop: &loop\n  - *loop\nmodel: "\\u0067pt-5.6"\n',
        encoding="utf-8",
    )
    assert any("gpt-5.6" in error for error in check.model_id_scan([candidate]))


def test_model_scan_covers_every_shipped_file_and_current_families(tmp_path: Path) -> None:
    """The default scan read the prose only, and named no current Claude family.

    A `claude-fable-5` in the Codex adapter or either manifest passed both gates.
    """
    # `claude-future-5` and `gemini-pro-3` name no family the pattern lists; recognized
    # provider-shaped IDs must not depend on enumerating the families of the day.
    for identifier in (
        "claude-fable-5", "fable-5", "gpt-oss-120b", "grok-4", "qwen3-235b",
        "claude-future-5", "gemini-pro-3", "mistral-large-2",
    ):
        candidate = tmp_path / "policy.md"
        candidate.write_text(f"Use {identifier}.\n", encoding="utf-8")
        assert check.model_id_scan([candidate]) != [], identifier
    for innocent in ("claude-code", "Claude Code 2.1.246", "a fabled release", "the opus of work"):
        candidate = tmp_path / "prose.md"
        candidate.write_text(f"{innocent}\n", encoding="utf-8")
        assert check.model_id_scan([candidate]) == [], innocent
    # Default mode, over a manifest -- the file kind the old candidate list skipped.
    package = tmp_path / "skiphow"
    (package / ".codex-plugin").mkdir(parents=True)
    (package / ".codex-plugin/plugin.json").write_text(
        '{"model": "claude-fable-5"}\n', encoding="utf-8"
    )
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.model_id_scan()
    assert any("claude-fable-5" in error for error in errors)


def test_package_shape_rejects_an_extra_shipped_file(tmp_path: Path) -> None:
    """A universal agents directory is not part of the composable skill package."""
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    (package / "agents").mkdir(exist_ok=True)
    (package / "agents/extra.txt").write_text("x\n", encoding="utf-8")
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("agents/extra.txt" in error for error in errors)


def test_package_shape_rejects_a_nested_skill(tmp_path: Path) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    nested = package / "skills/skiphow/references/nested/SKILL.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text(
        "---\nname: nested\ndescription: Wrongly nested skill.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("nested SKILL.md" in error for error in errors)


def test_package_shape_rejects_hidden_markdown_outside_references(
    tmp_path: Path,
) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    hidden = package / "skills/skiphow/methods/new-method.markdown"
    hidden.parent.mkdir()
    hidden.write_text("Hidden method.\n", encoding="utf-8")
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("Markdown outside SKILL.md and references" in error for error in errors)


def test_markdown_symlinks_are_rejected_before_reachability_resolution(
    tmp_path: Path,
) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    outside = tmp_path / "outside.md"
    outside.write_text("Outside.\n", encoding="utf-8")
    link = package / "skills/skiphow/references/linked.md"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("regular file, not a link" in error for error in errors)


def test_reachability_display_handles_macos_var_alias(tmp_path: Path) -> None:
    resolved = tmp_path.resolve()
    private_var = Path("/private/var")
    if not resolved.is_relative_to(private_var):
        pytest.skip("macOS /var alias is unavailable")
    aliased = Path("/var") / resolved.relative_to(private_var)
    skill = write_skill(aliased / "skills", "skiphow")
    hidden = skill / "methods/new-method.md"
    hidden.parent.mkdir()
    hidden.write_text("Hidden.\n", encoding="utf-8")
    errors = check.validate_skill_markdown_reachability(skill)
    assert any("Markdown outside SKILL.md and references" in error for error in errors)


def test_windows_invalid_package_paths_and_local_destinations_are_rejected(
    tmp_path: Path,
) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    reference = package / "skills/skiphow/references/foo:bar.md"
    reference.write_text("Unsafe on Windows.\n", encoding="utf-8")
    (package / "skills/skiphow/references/NUL.md").write_text(
        "Reserved device name.\n", encoding="utf-8"
    )
    skill = package / "skills/skiphow/SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8") + "\n[colon](references/foo:bar.md)\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("nonportable file path" in error for error in errors)
    assert any("disallowed Markdown destination" in error for error in errors)


def test_package_paths_reject_windows_names_and_case_collisions() -> None:
    for path in (
        "skills/skiphow/references/NUL.md",
        "skills/skiphow/references/COM1.markdown",
        "skills/skiphow/references/COM¹.md",
        "skills/skiphow/references/lpt².Markdown",
        "skills/skiphow/references/LPT³.txt",
        "skills/skiphow/references/trailing. ",
        "skills/skiphow/references/foo:bar.md",
        "skills/skiphow/references/bad\udcff.md",
    ):
        assert check.windows_package_path_key(path) is None
    errors = check.validate_package_path_portability(
        {"skills/skiphow/references/Case.md", "skills/skiphow/references/case.MD"}
    )
    assert any("case-insensitive" in error for error in errors)
    errors = check.validate_package_path_portability(
        {
            "skills/skiphow/references/Foo/a.md",
            "skills/skiphow/references/foo/b.md",
            "skills/skiphow/references/Café/c.md",
            "skills/skiphow/references/Cafe\u0301/d.md",
        }
    )
    assert sum("directory paths collide" in error for error in errors) == 2


def test_local_link_spelling_must_match_exactly(tmp_path: Path) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "skiphow")
    references = skill / "references"
    references.mkdir()
    (references / "Case.md").write_text("Exact case.\n", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        "---\nname: skiphow\ndescription: Owner entry.\n---\n\n"
        "Read [wrong case](references/case.md).\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        errors = check.validate_plugin_links()
    assert any("broken plugin link" in error for error in errors)


@pytest.mark.parametrize(
    "target",
    ["f%69le:///etc/passwd", "http://[", "a%00b.md", "C:Windows/win.ini"],
)
def test_plugin_static_reports_invalid_destinations_instead_of_crashing(
    tmp_path: Path, target: str
) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    skill = package / "skills/skiphow/SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8") + f"\n[unsafe]({target})\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("disallowed Markdown destination" in error for error in errors)


def test_plugin_static_reports_non_utf8_markdown_instead_of_crashing(
    tmp_path: Path,
) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    reference = package / "skills/skiphow/references/non-utf8.MD"
    reference.write_bytes(b"\xff\xfe")
    skill = package / "skills/skiphow/SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8")
        + "\n[invalid bytes](references/non-utf8.MD)\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("UTF-8" in error or "utf-8" in error for error in errors)


def test_package_shape_rejects_a_second_owner_visible_skill(tmp_path: Path) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    write_skill(package / "skills", "extra-entry")
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("exactly one owner entry" in error for error in errors)


@pytest.mark.parametrize("linked_component", ["plugins", "skiphow"])
def test_plugin_root_rejects_symlinks_in_its_component_chain(
    tmp_path: Path, linked_component: str
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    external = tmp_path / "external/plugins"
    shutil.copytree(check.PLUGIN_ROOT, external / "skiphow")
    try:
        if linked_component == "plugins":
            (repository / "plugins").symlink_to(external, target_is_directory=True)
        else:
            (repository / "plugins").mkdir()
            (repository / "plugins/skiphow").symlink_to(
                external / "skiphow", target_is_directory=True
            )
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    with (
        patch.object(check, "ROOT", repository),
        patch.object(check, "PLUGIN_ROOT", repository / "plugins/skiphow"),
    ):
        errors = check.validate_plugin_static()
    assert any("plugin path component must not be a link" in error for error in errors)


@pytest.mark.parametrize(
    ("host", "field", "value"),
    [
        ("codex", "mcpServers", {"unsafe": {"command": "run-me"}}),
        ("codex", "apps", "./.app.json"),
        ("codex", "hooks", "./hooks/hooks.json"),
        ("claude", "commands", ["./commands/danger.md"]),
        ("claude", "agents", ["./agents/danger.md"]),
        ("claude", "hooks", "./hooks/hooks.json"),
        ("claude", "mcpServers", {"unsafe": {"command": "run-me"}}),
        ("claude", "lspServers", {"unsafe": {"command": "run-me"}}),
        ("claude", "outputStyles", "./styles/"),
        ("claude", "workflows", "./workflows/"),
        ("claude", "experimental", {"monitors": ["./monitors.json"]}),
        ("claude", "dependencies", ["other-plugin"]),
        ("claude", "userConfig", {"token": {"type": "string"}}),
        ("claude", "channels", [{"server": "messages"}]),
        ("claude", "unknownComponent", "./danger"),
    ],
)
def test_host_manifests_allow_only_the_packaged_skill_component(
    tmp_path: Path, host: str, field: str, value: object
) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    manifest_path = package / f".{host}-plugin/plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[field] = value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any(
        f"{host.title()} manifest" in error and "unsupported" in error
        or "may declare only the skills component" in error
        for error in errors
    ), (host, field, errors)


def test_plugin_static_rejects_openai_behavior_dependencies(tmp_path: Path) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    metadata = package / "skills/skiphow/agents/openai.yaml"
    metadata.write_text(
        metadata.read_text(encoding="utf-8")
        + "dependencies:\n  tools:\n    - type: mcp\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("may contain only interface and policy" in error for error in errors)


def marketplace_root(tmp_path: Path) -> Path:
    shutil.copytree(check.ROOT / ".agents", tmp_path / ".agents")
    shutil.copytree(check.ROOT / ".claude-plugin", tmp_path / ".claude-plugin")
    return tmp_path


@pytest.mark.parametrize(
    ("host", "relative"),
    [
        ("codex", ".agents/plugins/marketplace.json"),
        ("claude", ".claude-plugin/marketplace.json"),
    ],
)
def test_root_marketplace_catalogs_must_not_be_symlinks(
    tmp_path: Path, host: str, relative: str
) -> None:
    repository = tmp_path / "repository"
    catalog = repository / relative
    catalog.parent.mkdir(parents=True)
    target = tmp_path / f"{host}-catalog.json"
    target.write_text("{}\n", encoding="utf-8")
    try:
        catalog.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    with patch.object(check, "ROOT", repository):
        errors = check.validate_marketplace_catalogs()
    assert any(
        host.title() in error and "non-symlink" in error for error in errors
    )

    destination = tmp_path / f"plain-{host}"
    with patch.object(hosts, "ROOT", repository):
        with pytest.raises(ValueError, match="regular non-symlink"):
            hosts._plain_marketplace(destination, host)
        assert not destination.exists()


@pytest.mark.parametrize("linked_parent", [False, True])
def test_plain_marketplace_rejects_linked_plugin_before_copy(
    tmp_path: Path, linked_parent: bool
) -> None:
    repository = tmp_path / "repo"
    external = tmp_path / "external"
    shutil.copytree(check.ROOT / ".agents", repository / ".agents")
    shutil.copytree(check.PLUGIN_ROOT, external / "skiphow")
    (repository / "plugins").mkdir(parents=True)
    try:
        if linked_parent:
            (repository / "plugins").rmdir()
            (repository / "plugins").symlink_to(external, target_is_directory=True)
        else:
            (repository / "plugins/skiphow").symlink_to(
                external / "skiphow", target_is_directory=True
            )
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    destination = tmp_path / "plain"
    with (
        patch.object(hosts, "ROOT", repository),
        patch.object(hosts, "PLUGIN_ROOT", repository / "plugins/skiphow"),
        pytest.raises(ValueError, match="package directory is unavailable"),
    ):
        hosts._plain_marketplace(destination, "codex")
    assert not destination.exists()


def test_json_loader_rejects_a_special_marketplace_file_without_reading_it(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    catalog = repository / ".agents/plugins/marketplace.json"
    catalog.parent.mkdir(parents=True)
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO files unavailable")
    os.mkfifo(catalog)
    with patch.object(check, "ROOT", repository):
        with pytest.raises(ValueError, match="regular non-symlink"):
            check.load_json(".agents/plugins/marketplace.json")


def test_version_and_root_license_must_be_regular_files(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    version_target = tmp_path / "VERSION-target"
    version_target.write_text("1.0.0\n", encoding="utf-8")
    license_target = tmp_path / "LICENSE-target"
    license_target.write_text("terms\n", encoding="utf-8")
    try:
        (repository / "VERSION").symlink_to(version_target)
        (repository / "LICENSE").symlink_to(license_target)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    with patch.object(check, "ROOT", repository):
        assert any("regular non-symlink" in error for error in check.validate_version())
        assert check.regular_file_problem(repository / "LICENSE", "root LICENSE")
        assert any(
            "root LICENSE must be a regular non-symlink file" in error
            for error in check.validate_plugin_static()
        )


@pytest.mark.parametrize("control_file", ["CHANGELOG.md", "SECURITY.md"])
@pytest.mark.parametrize("node_kind", ["fifo", "fifo-symlink"])
def test_version_validation_rejects_special_text_control_files_without_reading(
    tmp_path: Path, control_file: str, node_kind: str
) -> None:
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO files unavailable")
    repository = tmp_path / "repository"
    shutil.copytree(check.ROOT / ".agents", repository / ".agents")
    shutil.copytree(check.ROOT / ".claude-plugin", repository / ".claude-plugin")
    for relative in (
        "VERSION",
        "CHANGELOG.md",
        "SECURITY.md",
        "plugins/skiphow/.codex-plugin/plugin.json",
        "plugins/skiphow/.claude-plugin/plugin.json",
    ):
        if relative == control_file:
            continue
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(check.ROOT / relative, destination)
    control_path = repository / control_file
    if node_kind == "fifo":
        os.mkfifo(control_path)
    else:
        external_fifo = tmp_path / f"external-{control_file}"
        os.mkfifo(external_fifo)
        try:
            control_path.symlink_to(external_fifo)
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")

    result: dict[str, list[str]] = {}
    with patch.object(check, "ROOT", repository):
        thread = threading.Thread(
            target=lambda: result.setdefault("errors", check.validate_version()),
            daemon=True,
        )
        thread.start()
        thread.join(timeout=1)
        assert not thread.is_alive(), f"validate_version blocked on {node_kind} {control_file}"
    errors = result["errors"]
    assert any(
        control_file in error and "regular non-symlink" in error for error in errors
    )


def test_codex_marketplace_identity_policy_and_cardinality_are_exact(tmp_path: Path) -> None:
    root = marketplace_root(tmp_path)
    path = root / ".agents/plugins/marketplace.json"
    baseline = json.loads(path.read_text(encoding="utf-8"))
    candidates = []
    candidate = json.loads(json.dumps(baseline))
    candidate["name"] = "wrong"
    candidates.append(candidate)
    candidate = json.loads(json.dumps(baseline))
    candidate["plugins"][0]["name"] = "wrong"
    candidates.append(candidate)
    candidate = json.loads(json.dumps(baseline))
    candidate["plugins"][0]["policy"]["installation"] = "BLOCKED"
    candidates.append(candidate)
    candidate = json.loads(json.dumps(baseline))
    candidate["plugins"][0]["policy"]["products"] = []
    candidates.append(candidate)
    candidate = json.loads(json.dumps(baseline))
    candidate["plugins"].append(json.loads(json.dumps(candidate["plugins"][0])))
    candidates.append(candidate)
    candidate = json.loads(json.dumps(baseline))
    candidate["plugins"][0]["extra"] = True
    candidates.append(candidate)

    with patch.object(check, "ROOT", root):
        for candidate in candidates:
            path.write_text(json.dumps(candidate), encoding="utf-8")
            assert check.validate_marketplace_catalogs() != []


def test_claude_marketplace_identity_and_cardinality_are_exact(tmp_path: Path) -> None:
    root = marketplace_root(tmp_path)
    path = root / ".claude-plugin/marketplace.json"
    baseline = json.loads(path.read_text(encoding="utf-8"))
    candidates = []
    candidate = json.loads(json.dumps(baseline))
    candidate["name"] = "wrong"
    candidates.append(candidate)
    candidate = json.loads(json.dumps(baseline))
    candidate["plugins"][0]["name"] = "wrong"
    candidates.append(candidate)
    candidate = json.loads(json.dumps(baseline))
    candidate["plugins"][0]["version"] = "9.9.9"
    candidates.append(candidate)
    candidate = json.loads(json.dumps(baseline))
    candidate["owner"]["extra"] = True
    candidates.append(candidate)
    candidate = json.loads(json.dumps(baseline))
    candidate["owner"] = {"name": "impostor", "url": "https://evil.example"}
    candidates.append(candidate)
    candidate = json.loads(json.dumps(baseline))
    candidate["plugins"].append(json.loads(json.dumps(candidate["plugins"][0])))
    candidates.append(candidate)

    with patch.object(check, "ROOT", root):
        for candidate in candidates:
            path.write_text(json.dumps(candidate), encoding="utf-8")
            assert check.validate_marketplace_catalogs() != []


def test_changelog_must_lead_with_the_released_version() -> None:
    """A newer section above the released one used to satisfy the heading search."""
    changelog = (check.ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    release = (check.ROOT / "VERSION").read_text(encoding="utf-8").strip()
    dated = re.findall(r"^## (\S+) \(\d{4}-\d{2}-\d{2}\)$", changelog, re.MULTILINE)
    assert dated[0] == release
    assert check.validate_version() == []


def test_safe_hook_literal_pattern_rejects_shell_behavior() -> None:
    breakout = (
        "sh -c 'printf \"%s\\n\" \"' ; touch f; echo '\"; "
        "if [ -f .skiphow/handoff.md ]; then cat .skiphow/handoff.md; fi; exit 0'"
    )
    assert check.SAFE_ECHO_COMMAND.fullmatch(breakout) is None
    assert check.SAFE_ECHO_COMMAND.fullmatch("echo '-n'") is None
    assert check.SAFE_ECHO_COMMAND.fullmatch("echo '--help'") is None
    real = real_hook_payload()
    for command in (group["hooks"][0]["command"] for group in real["hooks"]["SessionStart"]):
        payload = check.SAFE_ECHO_COMMAND.fullmatch(command).group(1)
        assert not set(payload) & set("$`\\|&;<>()*?[]{}!#~'\"")
        assert not re.search(
            r"\b(?:curl|wget|nc|ssh|scp|nslookup|dig|python|node|sh|bash|zsh|eval|"
            r"source|cat|cp|mv|rm|mkdir|touch|tee|chmod|git|pip|npm)\b",
            command,
        )


def test_personal_path_scan_leaves_web_routes_alone() -> None:
    """Dropping the required trailing separator reached into URLs.

    A `/users/` route in a documented URL is not a home directory, and the gate
    scans public documentation, so a false positive blocks a release for nothing.
    """
    for innocent in (
        "https://example.com/Users/profile",
        "https://example.test/users/alice",
        "https://example.com/root/docs",
        "GET /users/me",
    ):
        assert check.PERSONAL_PATH.search(innocent) is None, innocent
    for personal in (
        "see /" + "Users/person",
        "/" + "home/person",
        "C:\\USERS\\person\\x",
        "/root",
        "/root/secret",
        "%UserProfile%\\secret",
        "%userprofile%/secret",
    ):
        assert check.PERSONAL_PATH.search(personal), personal


def test_portability_scan_distinguishes_root_home_from_a_web_route(
    tmp_path: Path,
) -> None:
    plugin = tmp_path / "plugins/skiphow"
    plugin.mkdir(parents=True)
    candidate = plugin / "policy.md"
    candidate.write_text(
        "[innocent route](https://example.com/root/docs)\n",
        encoding="utf-8",
    )
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[candidate]),
    ):
        assert check.portability_scan() == []

    candidate.write_text("Actual local homes: /root and %UserProfile%\\work.\n", encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[candidate]),
    ):
        errors = check.portability_scan()
    assert any("'/root'" in error for error in errors)
    assert any("%UserProfile%" in error for error in errors)


def test_file_enumeration_falls_back_without_git(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    expected = tmp_path / "docs/archive.md"
    expected.write_text("archive\n", encoding="utf-8")
    completed = check.subprocess.CompletedProcess(["git"], 128, b"", b"not a repository")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check.subprocess, "run", return_value=completed),
    ):
        assert list(check.repository_files({".md"})) == [expected]
        assert check.validate_diff(None) == []
