"""Layer C tests for the isolated Module 5 plugin-layout validator."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


VALIDATOR = Path(__file__).with_name("validate_plugin_layout.py")


def _write_fixture(root: Path) -> None:
    plugin = root / "plugins/taskflow-agent-pack"
    (plugin / "skills/taskflow-api-review").mkdir(parents=True)
    (root / ".agents/plugins").mkdir(parents=True)
    (plugin / "plugin.json").write_text(
        json.dumps(
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": "taskflow-agent-pack",
                "version": "0.1.0",
                "description": "Fixture plugin",
            }
        ),
        encoding="utf-8",
    )
    (plugin / "skills/taskflow-api-review/SKILL.md").write_text(
        "# Review\n", encoding="utf-8"
    )
    (root / ".agents/plugins/marketplace.json").write_text(
        json.dumps(
            {
                "name": "local-repo",
                "plugins": [
                    {
                        "name": "taskflow-agent-pack",
                        "source": {
                            "source": "local",
                            "path": "./plugins/taskflow-agent-pack",
                        },
                        "policy": {
                            "installation": "AVAILABLE",
                            "authentication": "ON_INSTALL",
                        },
                        "category": "Productivity",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--repo-root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def _manifest(root: Path) -> Path:
    return root / "plugins/taskflow-agent-pack/plugin.json"


def _marketplace(root: Path) -> Path:
    return root / ".agents/plugins/marketplace.json"


def _change_json(path: Path, mutate) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(json.dumps(document), encoding="utf-8")


def _assert_failure(root: Path, fragment: str) -> None:
    result = _run(root)
    assert result.returncode != 0
    assert fragment.lower() in (result.stdout + result.stderr).lower()


def test_valid_fixture_passes_and_selected_root_is_respected(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout


@pytest.mark.parametrize(
    ("relative", "fragment"),
    [
        ("plugins/taskflow-agent-pack/plugin.json", "plugin manifest"),
        ("plugins/taskflow-agent-pack/skills", "skills directory"),
        ("plugins/taskflow-agent-pack/skills/taskflow-api-review/SKILL.md", "required skill"),
    ],
)
def test_required_layout_paths_are_required(
    tmp_path: Path, relative: str, fragment: str
) -> None:
    _write_fixture(tmp_path)
    path = tmp_path / relative
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    _assert_failure(tmp_path, fragment)


def test_deeper_skill_nesting_does_not_substitute(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    required = tmp_path / "plugins/taskflow-agent-pack/skills/taskflow-api-review/SKILL.md"
    required.unlink()
    deeper = required.parent / "nested/SKILL.md"
    deeper.parent.mkdir()
    deeper.write_text("# Deeper\n", encoding="utf-8")
    _assert_failure(tmp_path, "required skill")


def test_escaping_symlink_fails_closed(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    outside = tmp_path.parent / f"plugin-layout-outside-{os.getpid()}"
    outside.mkdir()
    try:
        target = tmp_path / "plugins/taskflow-agent-pack/skills/taskflow-api-review/SKILL.md"
        target.unlink()
        try:
            target.symlink_to(outside / "SKILL.md")
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"platform cannot create symlinks: {exc}")
        _assert_failure(tmp_path, "symlink")
    finally:
        if outside.exists():
            for child in outside.iterdir():
                child.unlink()
            outside.rmdir()


def test_mismatched_plugin_identity_fails(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    _change_json(_manifest(tmp_path), lambda doc: doc.update(name="other-plugin"))
    _assert_failure(tmp_path, "plugin name")


@pytest.mark.parametrize("value", [None, "", "   "])
def test_version_is_layer_b_policy(tmp_path: Path, value: str | None) -> None:
    _write_fixture(tmp_path)
    if value is None:
        _change_json(_manifest(tmp_path), lambda doc: doc.pop("version"))
    else:
        _change_json(_manifest(tmp_path), lambda doc: doc.update(version=value))
    _assert_failure(tmp_path, "version")
    result = _run(tmp_path)
    assert "project policy" in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize("value", [None, "", "   "])
def test_description_is_layer_b_policy(tmp_path: Path, value: str | None) -> None:
    _write_fixture(tmp_path)
    if value is None:
        _change_json(_manifest(tmp_path), lambda doc: doc.pop("description"))
    else:
        _change_json(_manifest(tmp_path), lambda doc: doc.update(description=value))
    _assert_failure(tmp_path, "description")
    result = _run(tmp_path)
    assert "project policy" in (result.stdout + result.stderr).lower()


def test_invalid_json_fails(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    _manifest(tmp_path).write_text("{not json", encoding="utf-8")
    _assert_failure(tmp_path, "malformed json")


def test_wrong_marketplace_name_fails(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    _change_json(_marketplace(tmp_path), lambda doc: doc.update(name="wrong"))
    _assert_failure(tmp_path, "marketplace name")


@pytest.mark.parametrize("plugins", [[], [{"name": "other"}], {"name": "taskflow-agent-pack"}])
def test_missing_or_malformed_plugin_entry_fails(tmp_path: Path, plugins) -> None:
    _write_fixture(tmp_path)
    _change_json(_marketplace(tmp_path), lambda doc: doc.update(plugins=plugins))
    _assert_failure(tmp_path, "plugin entry" if isinstance(plugins, list) else "plugins")


def test_wrong_source_type_fails(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    _change_json(_marketplace(tmp_path), lambda doc: doc["plugins"][0]["source"].update(source="remote"))
    _assert_failure(tmp_path, "source type")


@pytest.mark.parametrize("path", ["./plugins/other", "../outside", "/tmp/plugin"])
def test_wrong_or_outside_source_path_fails(tmp_path: Path, path: str) -> None:
    _write_fixture(tmp_path)
    _change_json(_marketplace(tmp_path), lambda doc: doc["plugins"][0]["source"].update(path=path))
    _assert_failure(tmp_path, "source path")


@pytest.mark.parametrize("policy", [None, {}, {"installation": "AVAILABLE"}, {"installation": "", "authentication": "ON_INSTALL"}])
def test_missing_or_malformed_policy_fails(tmp_path: Path, policy) -> None:
    _write_fixture(tmp_path)
    _change_json(_marketplace(tmp_path), lambda doc: doc["plugins"][0].update(policy=policy))
    _assert_failure(tmp_path, "policy")


@pytest.mark.parametrize("category", [None, "", "   "])
def test_missing_or_empty_category_fails(tmp_path: Path, category: str | None) -> None:
    _write_fixture(tmp_path)
    _change_json(_marketplace(tmp_path), lambda doc: doc["plugins"][0].update(category=category))
    _assert_failure(tmp_path, "category")


def test_duplicate_matching_plugin_entries_fail(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    def duplicate(doc):
        doc["plugins"].append(doc["plugins"][0].copy())
    _change_json(_marketplace(tmp_path), duplicate)
    _assert_failure(tmp_path, "exactly one")
