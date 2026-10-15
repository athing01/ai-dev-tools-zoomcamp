#!/usr/bin/env python3
"""Reject diffs that touch the protected Module 3/4 surface."""

from __future__ import annotations

import argparse
import os
from pathlib import PurePosixPath
import subprocess
import sys
from typing import Iterable


PROTECTED_FILES = frozenset(
    {
        ".github/workflows/ci.yml",
        ".github/workflows/deploy.yml",
        ".github/workflows/ci-module-4.yml",
        ".github/workflows/deploy-module-4.yml",
        ".github/workflows/promote-module-4.yml",
    }
)

# These are repository policy roots, not string prefixes.  The explicit
# module roots cover the checked-in application and runtime configuration
# layout; infra/deploy roots also protect the documented future boundaries.
PROTECTED_ROOTS = frozenset(
    {
        "module-3/infra",
        "module-3/deploy",
        "module-3/backend",
        "module-3/frontend",
        "module-3/docker-compose.yml",
        "module-3/openapi.yaml",
        "module-4/infra",
        "module-4/deploy",
        "module-4/backend",
        "module-4/frontend",
        "module-4/observability",
        "module-4/incident-response",
        "module-4/security-audit",
        "module-4/docker-compose.yml",
        "module-4/openapi.yaml",
    }
)


def repository_root(repo_root: str | None) -> str:
    """Return a canonical repository root, independent of cwd."""
    candidate = os.path.abspath(repo_root) if repo_root else os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    try:
        result = subprocess.run(
            ["git", "-C", candidate, "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", "replace").strip()
        raise RuntimeError(f"cannot find a Git repository at {candidate}: {detail}") from exc
    return os.path.realpath(result.stdout.decode("utf-8").strip())


def validate_revision(root: str, revision: str, label: str) -> str:
    if not revision or revision.startswith("-") or "\x00" in revision:
        raise RuntimeError(f"invalid {label} revision: {revision!r}")
    try:
        result = subprocess.run(
            ["git", "-C", root, "rev-parse", "--verify", f"{revision}^{{commit}}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", "replace").strip()
        raise RuntimeError(f"invalid {label} revision {revision!r}: {detail}") from exc
    return result.stdout.decode("ascii").strip()


def normalize_path(raw: bytes) -> str:
    try:
        path = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Git returned a changed path that is not valid UTF-8") from exc
    if (
        not path
        or "\\" in path
        or "\x00" in path
        or path.startswith("/")
        or path.startswith("//")
    ):
        raise RuntimeError(f"malformed changed path: {path!r}")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RuntimeError(f"unsafe changed path: {path!r}")
    # PurePosixPath is used only as a component-aware validation step.  It
    # prevents a protected root from becoming a textual prefix match.
    normalized = PurePosixPath(*parts).as_posix()
    if normalized != path:
        raise RuntimeError(f"unsafe changed path: {path!r}")
    return normalized


def changed_paths(root: str, base: str, head: str) -> list[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                root,
                "diff",
                "--name-only",
                "--no-renames",
                "-z",
                base,
                head,
                "--",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", "replace").strip()
        raise RuntimeError(f"unable to obtain Git diff: {detail}") from exc
    return [normalize_path(raw) for raw in result.stdout.split(b"\0") if raw]


def is_protected(path: str) -> bool:
    if path in PROTECTED_FILES:
        return True
    return any(path == root or path.startswith(f"{root}/") for root in PROTECTED_ROOTS)


def protected_paths(paths: Iterable[str]) -> list[str]:
    return sorted(path for path in paths if is_protected(path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="base Git revision")
    parser.add_argument("--head", required=True, help="head Git revision")
    parser.add_argument("--repo-root", help="isolated repository root")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = repository_root(args.repo_root)
        base = validate_revision(root, args.base, "base")
        head = validate_revision(root, args.head, "head")
        changed = changed_paths(root, base, head)
        blocked = protected_paths(changed)
    except RuntimeError as exc:
        print(f"protected-path guardrail error: {exc}", file=sys.stderr)
        return 2

    if blocked:
        print("protected paths changed; policy violation:", file=sys.stderr)
        for path in blocked:
            print(f"  {path}", file=sys.stderr)
        return 1
    print(f"No protected paths changed ({len(changed)} changed path(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
