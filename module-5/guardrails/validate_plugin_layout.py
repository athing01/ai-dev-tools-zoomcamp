"""Validate the fixed Module 5 plugin layout and marketplace policy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PLUGIN_RELATIVE = Path("plugins/taskflow-agent-pack")
MANIFEST_RELATIVE = PLUGIN_RELATIVE / "plugin.json"
SKILLS_RELATIVE = PLUGIN_RELATIVE / "skills"
SKILL_RELATIVE = SKILLS_RELATIVE / "taskflow-api-review" / "SKILL.md"
MARKETPLACE_RELATIVE = Path(".agents/plugins/marketplace.json")
PLUGIN_NAME = "taskflow-agent-pack"


class ValidationError(Exception):
    """A project-policy or filesystem validation failure."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the Module 5 plugin layout and marketplace."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="repository or isolated fixture root (defaults to this file's repository)",
    )
    return parser


def _selected_root(argument: Path | None) -> Path:
    candidate = argument if argument is not None else Path(__file__).resolve().parents[2]
    try:
        root = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValidationError(f"Repository root is unavailable: {candidate}") from exc
    if not root.is_dir():
        raise ValidationError(f"Repository root is not a directory: {candidate}")
    return root


def _safe_path(root: Path, relative: Path, kind: str) -> Path:
    """Resolve one fixed path while rejecting symlink components and escapes."""
    if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
        raise ValidationError(f"Unsafe fixed {kind} path: {relative}")

    current = root
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                raise ValidationError(
                    f"Symlink is not permitted in {kind} path: {relative}"
                )
        except OSError as exc:
            raise ValidationError(f"Cannot inspect {kind} path: {relative}") from exc

    try:
        resolved = current.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValidationError(f"Missing {kind}: {relative}") from exc

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValidationError(f"{kind.capitalize()} escapes repository root: {relative}") from exc

    if kind.endswith("directory"):
        if not resolved.is_dir():
            raise ValidationError(f"Expected directory: {relative}")
    elif not resolved.is_file():
        raise ValidationError(f"Expected regular file: {relative}")

    return resolved


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, UnicodeDecodeError) as exc:
        raise ValidationError(f"Could not read {label}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Malformed JSON in {label}: {exc.msg}") from exc

    if not isinstance(value, dict):
        raise ValidationError(f"{label} must contain a JSON object")
    return value


def _require_nonempty_string(document: dict[str, Any], key: str, label: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(
            f"{label} project policy requires non-empty string '{key}'"
        )
    return value


def _validate_plugin(root: Path) -> None:
    plugin_dir = _safe_path(root, PLUGIN_RELATIVE, "plugin directory")
    _safe_path(root, MANIFEST_RELATIVE, "plugin manifest")
    _safe_path(root, SKILLS_RELATIVE, "skills directory")
    _safe_path(root, SKILL_RELATIVE, "required skill file")

    manifest = _load_json(root / MANIFEST_RELATIVE, "plugin manifest")
    name = _require_nonempty_string(manifest, "name", "Plugin")
    if name != PLUGIN_NAME:
        raise ValidationError(
            f"Plugin name must be '{PLUGIN_NAME}', got {name!r}"
        )
    _require_nonempty_string(manifest, "version", "Plugin")
    _require_nonempty_string(manifest, "description", "Plugin")

    try:
        (root / MANIFEST_RELATIVE).resolve(strict=True).relative_to(plugin_dir)
    except ValueError as exc:
        raise ValidationError("Plugin manifest resolves outside plugin directory") from exc


def _validate_marketplace(root: Path) -> None:
    marketplace_path = _safe_path(root, MARKETPLACE_RELATIVE, "marketplace file")
    marketplace = _load_json(marketplace_path, "marketplace")

    if marketplace.get("name") != "local-repo":
        raise ValidationError("Marketplace name must be 'local-repo'")

    entries = marketplace.get("plugins")
    if not isinstance(entries, list):
        raise ValidationError("Marketplace 'plugins' must be an array")

    matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME]
    if len(matches) != 1:
        raise ValidationError(
            f"Marketplace must contain exactly one '{PLUGIN_NAME}' plugin entry"
        )
    entry = matches[0]

    source = entry.get("source")
    if not isinstance(source, dict):
        raise ValidationError("Plugin marketplace 'source' must be an object")
    if source.get("source") != "local":
        raise ValidationError("Plugin marketplace source type must be 'local'")
    if source.get("path") != "./plugins/taskflow-agent-pack":
        raise ValidationError(
            "Plugin marketplace source path must be './plugins/taskflow-agent-pack'"
        )

    plugin_dir = _safe_path(root, PLUGIN_RELATIVE, "marketplace plugin directory")
    source_path = root / source["path"]
    try:
        resolved_source = source_path.resolve(strict=True)
        resolved_source.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValidationError("Marketplace source path is outside the repository") from exc
    if resolved_source != plugin_dir:
        raise ValidationError("Marketplace source path does not identify the required plugin directory")

    policy = entry.get("policy")
    if not isinstance(policy, dict):
        raise ValidationError("Plugin marketplace 'policy' must be an object")
    for key, expected in (("installation", "AVAILABLE"), ("authentication", "ON_INSTALL")):
        value = policy.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"Marketplace policy requires non-empty string '{key}'")
        if value != expected:
            raise ValidationError(f"Marketplace policy '{key}' must be '{expected}'")

    category = entry.get("category")
    if not isinstance(category, str) or not category.strip():
        raise ValidationError("Marketplace entry requires a non-empty string 'category'")
    if category != "Productivity":
        raise ValidationError("Marketplace category must be 'Productivity'")


def validate(root: Path) -> None:
    _validate_plugin(root)
    _validate_marketplace(root)


def main() -> int:
    try:
        root = _selected_root(_parser().parse_args().repo_root)
        validate(root)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: plugin layout, project policy, and marketplace consistency")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
