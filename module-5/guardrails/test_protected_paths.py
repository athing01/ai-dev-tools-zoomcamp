from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).with_name("protected_paths.py")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def write_file(repo: Path, relative: str, content: str = "fixture\n") -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def fixture_repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo with spaces"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Guardrail Test")
    write_file(repo, "README.md")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "initial")
    base = git(repo, "rev-parse", "HEAD")
    return repo, base, base


def run_guardrail(repo: Path, base: str, head: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(repo),
            "--base",
            base,
            "--head",
            head,
            *extra,
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def commit_change(repo: Path, relative: str, content: str = "changed\n") -> tuple[str, str]:
    base = git(repo, "rev-parse", "HEAD")
    write_file(repo, relative, content)
    git(repo, "add", "--", relative)
    git(repo, "commit", "-qm", f"change {relative}")
    return base, git(repo, "rev-parse", "HEAD")


def test_module_5_only_change_passes(fixture_repo: tuple[Path, str, str]) -> None:
    repo, _, _ = fixture_repo
    base, head = commit_change(repo, "module-5/guardrails/example.txt")
    result = run_guardrail(repo, base, head)
    assert result.returncode == 0
    assert "No protected paths changed" in result.stdout


@pytest.mark.parametrize(
    "relative",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/deploy.yml",
        ".github/workflows/ci-module-4.yml",
        ".github/workflows/deploy-module-4.yml",
        ".github/workflows/promote-module-4.yml",
        "module-3/infra/cloudformation/taskflow.yaml",
        "module-3/deploy/ec2/deploy.sh",
        "module-3/backend/taskflow_backend/app.py",
        "module-3/frontend/src/routes/index.tsx",
        "module-3/docker-compose.yml",
        "module-3/openapi.yaml",
        "module-4/infra/stack.yaml",
        "module-4/deploy/release.sh",
        "module-4/backend/taskflow_backend/app.py",
        "module-4/frontend/src/routes/index.tsx",
        "module-4/observability/alerts.yaml",
        "module-4/docker-compose.yml",
        "module-4/openapi.yaml",
    ],
)
def test_protected_paths_fail(fixture_repo: tuple[Path, str, str], relative: str) -> None:
    repo, _, _ = fixture_repo
    base, head = commit_change(repo, relative)
    result = run_guardrail(repo, base, head)
    assert result.returncode != 0
    assert relative in result.stderr
    assert "policy violation" in result.stderr


def test_module_5_workflow_is_allowed(fixture_repo: tuple[Path, str, str]) -> None:
    repo, _, _ = fixture_repo
    base, head = commit_change(repo, ".github/workflows/ci-module-5.yml")
    result = run_guardrail(repo, base, head)
    assert result.returncode == 0


def test_rename_from_protected_workflow_is_rejected(
    fixture_repo: tuple[Path, str, str],
) -> None:
    repo, _, _ = fixture_repo
    write_file(repo, ".github/workflows/ci.yml")
    git(repo, "add", "--", ".github/workflows/ci.yml")
    git(repo, "commit", "-qm", "add protected workflow")
    base = git(repo, "rev-parse", "HEAD")

    git(repo, "mv", ".github/workflows/ci.yml", ".github/workflows/ci-module-5.yml")
    git(repo, "commit", "-qm", "rename protected workflow")
    head = git(repo, "rev-parse", "HEAD")

    result = run_guardrail(repo, base, head)
    assert result.returncode != 0
    assert ".github/workflows/ci.yml" in result.stderr


def test_deletion_is_rejected(fixture_repo: tuple[Path, str, str]) -> None:
    repo, _, _ = fixture_repo
    write_file(repo, ".github/workflows/ci.yml")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "add protected workflow")
    base = git(repo, "rev-parse", "HEAD")
    (repo / ".github/workflows/ci.yml").unlink()
    git(repo, "add", "-u", ".")
    git(repo, "commit", "-qm", "delete protected workflow")
    head = git(repo, "rev-parse", "HEAD")
    result = run_guardrail(repo, base, head)
    assert result.returncode != 0
    assert ".github/workflows/ci.yml" in result.stderr


def test_spaces_and_similar_names_are_safe(fixture_repo: tuple[Path, str, str]) -> None:
    repo, _, _ = fixture_repo
    base, head = commit_change(repo, "module-3/infrastructure-notes.md")
    result = run_guardrail(repo, base, head)
    assert result.returncode == 0

    base, head = commit_change(repo, "module-5/notes with spaces.txt")
    result = run_guardrail(repo, base, head)
    assert result.returncode == 0


def test_protected_filename_with_spaces_is_rejected(
    fixture_repo: tuple[Path, str, str],
) -> None:
    repo, _, _ = fixture_repo
    relative = "module-3/backend/source with spaces.py"
    base, head = commit_change(repo, relative)
    result = run_guardrail(repo, base, head)
    assert result.returncode != 0
    assert relative in result.stderr


def test_mixed_allowed_and_protected_diff_fails(fixture_repo: tuple[Path, str, str]) -> None:
    repo, _, _ = fixture_repo
    base = git(repo, "rev-parse", "HEAD")
    write_file(repo, "module-5/allowed.txt")
    write_file(repo, "module-3/infra/changed.yaml")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "mixed change")
    result = run_guardrail(repo, base, git(repo, "rev-parse", "HEAD"))
    assert result.returncode != 0
    assert "module-3/infra/changed.yaml" in result.stderr


@pytest.mark.parametrize("revision", ["does-not-exist", "HEAD~99"])
def test_invalid_revisions_fail_closed(fixture_repo: tuple[Path, str, str], revision: str) -> None:
    repo, base, _ = fixture_repo
    result = run_guardrail(repo, base, revision)
    assert result.returncode != 0
    assert "guardrail error" in result.stderr


def test_invalid_base_revision_fails_closed(fixture_repo: tuple[Path, str, str]) -> None:
    repo, _, head = fixture_repo
    result = run_guardrail(repo, "does-not-exist", head)
    assert result.returncode != 0
    assert "invalid base revision" in result.stderr


def test_invalid_head_revision_fails_closed(fixture_repo: tuple[Path, str, str]) -> None:
    repo, base, _ = fixture_repo
    result = run_guardrail(repo, base, "does-not-exist")
    assert result.returncode != 0
    assert "invalid head revision" in result.stderr


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX backslash filename semantics")
def test_malformed_backslash_path_fails_closed(
    fixture_repo: tuple[Path, str, str],
) -> None:
    repo, _, _ = fixture_repo
    relative = r"module-3\infra\unexpected.yaml"
    base, head = commit_change(repo, relative)
    result = run_guardrail(repo, base, head)
    assert result.returncode != 0
    assert "malformed changed path" in result.stderr


def test_traversal_like_revision_and_path_fail_closed(fixture_repo: tuple[Path, str, str]) -> None:
    repo, base, _ = fixture_repo
    result = run_guardrail(repo, base, "../HEAD")
    assert result.returncode != 0

    # Git rejects slash-containing path components in this fixture, so this
    # confirms the normal diff path remains component-safe without touching the
    # real repository or accepting a traversal-shaped filename.
    base, head = commit_change(repo, "module-3/infra-notes/file.txt")
    result = run_guardrail(repo, base, head)
    assert result.returncode == 0


def test_git_execution_failure_is_not_a_pass(fixture_repo: tuple[Path, str, str]) -> None:
    repo, base, head = fixture_repo
    result = run_guardrail(repo / "missing", base, head)
    assert result.returncode != 0
    assert "guardrail error" in result.stderr


def test_git_diff_failure_is_not_a_pass(fixture_repo: tuple[Path, str, str]) -> None:
    repo, _, _ = fixture_repo
    base, head = commit_change(repo, "module-5/diff-failure.txt")
    tree_sha = git(repo, "rev-parse", f"{head}^{{tree}}")
    tree_path = repo / ".git" / "objects" / tree_sha[:2] / tree_sha[2:]
    if not tree_path.is_file():
        pytest.skip("Git did not leave the fixture tree as a loose object")
    tree_path.unlink()

    result = run_guardrail(repo, base, head)
    assert result.returncode != 0
    assert "unable to obtain Git diff" in result.stderr
