"""Validate the portable plugin manifest and expected-invalid schema fixtures."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SCHEMA_URL = (
    "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
)
CLI_PACKAGE = "check-jsonschema==0.38.2"
CLI_VERSION = "0.38.2"
MAX_SCHEMA_BYTES = 1_000_000
COMMAND_TIMEOUT_SECONDS = 180

REPO_ROOT = Path(__file__).resolve().parents[2]

CASES = (
    {
        "label": "real plugin manifest",
        "relative_file": "plugins/taskflow-agent-pack/plugin.json",
        "expected_status": "ok",
    },
    {
        "label": "missing-$schema negative fixture",
        "relative_file": (
            "module-5/tests/fixtures/plugin-manifests/"
            "schema-invalid-missing-schema.json"
        ),
        "expected_status": "fail",
        "expected_path": "$",
        "expected_message": "'$schema' is a required property",
    },
    {
        "label": "non-string-name negative fixture",
        "relative_file": (
            "module-5/tests/fixtures/plugin-manifests/"
            "schema-invalid-name-type.json"
        ),
        "expected_status": "fail",
        "expected_path": "$.name",
        "expected_message": "is not of type 'string'",
    },
)


class ValidationError(RuntimeError):
    """A required validation step could not be verified."""


def _resolve_named_input(relative_file: str) -> Path:
    """Read only an explicitly named, regular input inside this repository."""
    candidate = REPO_ROOT

    for component in Path(relative_file).parts:
        if component in ("", ".", ".."):
            raise ValidationError(
                f"Invalid repository-relative input: {relative_file}"
            )

        candidate = candidate / component
        if candidate.is_symlink():
            raise ValidationError(
                f"Symlink input is not permitted: {relative_file}"
            )

    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValidationError(
            f"Required input is unavailable: {relative_file}"
        ) from exc

    if resolved != candidate or not resolved.is_file():
        raise ValidationError(
            f"Input must be a regular repository file: {relative_file}"
        )

    return resolved


def _show_process_output(result: subprocess.CompletedProcess[str]) -> None:
    print("stdout:", file=sys.stderr)
    print(result.stdout.rstrip() or "<empty>", file=sys.stderr)
    print("stderr:", file=sys.stderr)
    print(result.stderr.rstrip() or "<empty>", file=sys.stderr)


def _run_command(
    command: list[str],
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValidationError(
            f"Command timed out after {COMMAND_TIMEOUT_SECONDS} seconds."
        ) from exc
    except OSError as exc:
        raise ValidationError(
            f"Could not execute the pinned validator: {exc}"
        ) from exc


def _resolve_and_check_cli() -> str:
    uvx_executable = shutil.which("uvx")

    if not uvx_executable:
        raise ValidationError(
            "uvx was not found on PATH; refusing to substitute another validator."
        )

    result = _run_command(
        [
            uvx_executable,
            "--from",
            CLI_PACKAGE,
            "check-jsonschema",
            "--version",
        ]
    )

    combined_output = f"{result.stdout}\n{result.stderr}"

    if (
        result.returncode != 0
        or re.search(r"\b0\.38\.2\b", combined_output) is None
    ):
        _show_process_output(result)
        raise ValidationError(
            f"Could not verify the required CLI version {CLI_VERSION}."
        )

    print(f"PASS: resolved pinned CLI {CLI_VERSION}")
    return uvx_executable


def _download_schema(schema_file: Path) -> None:
    request = urllib.request.Request(
        SCHEMA_URL,
        headers={"User-Agent": "m5-plugin-schema-validator/0.1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise ValidationError(
                    f"Schema server returned HTTP {response.status}."
                )

            if response.geturl() != SCHEMA_URL:
                raise ValidationError(
                    "Schema URL redirected unexpectedly; refusing to use it."
                )

            raw_schema = response.read(MAX_SCHEMA_BYTES + 1)

    except ValidationError:
        raise
    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
    ) as exc:
        raise ValidationError(
            f"Canonical schema download failed: {type(exc).__name__}: {exc}"
        ) from exc

    if len(raw_schema) > MAX_SCHEMA_BYTES:
        raise ValidationError(
            f"Canonical schema exceeds {MAX_SCHEMA_BYTES} bytes."
        )

    try:
        parsed_schema = json.loads(raw_schema)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationError(
            "Canonical schema response is not valid JSON."
        ) from exc

    if not isinstance(parsed_schema, dict):
        raise ValidationError(
            "Canonical schema root must be a JSON object."
        )

    try:
        schema_file.write_bytes(raw_schema)
    except OSError as exc:
        raise ValidationError(
            f"Could not store schema in the controlled temporary directory: {exc}"
        ) from exc

    print(
        f"PASS: downloaded and parsed canonical schema once "
        f"({len(raw_schema)} bytes)"
    )


def _parse_json_output(
    result: subprocess.CompletedProcess[str],
    label: str,
) -> dict[str, Any]:
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        _show_process_output(result)
        raise ValidationError(
            f"{label}: pinned CLI did not return valid JSON on stdout."
        ) from exc

    if not isinstance(document, dict):
        _show_process_output(result)
        raise ValidationError(
            f"{label}: CLI JSON root is not an object."
        )

    if not isinstance(document.get("errors"), list):
        _show_process_output(result)
        raise ValidationError(
            f"{label}: CLI JSON lacks the expected errors array."
        )

    parse_errors = document.get("parse_errors", [])
    if not isinstance(parse_errors, list):
        _show_process_output(result)
        raise ValidationError(
            f"{label}: CLI parse_errors field has an unexpected type."
        )

    if parse_errors:
        _show_process_output(result)
        raise ValidationError(
            f"{label}: input or schema parsing failed; this is not "
            "an accepted validation result."
        )

    return document


def _validate_case(
    uvx_executable: str,
    schema_file: Path,
    case: dict[str, str],
) -> bool:
    label = case["label"]
    instance_file = _resolve_named_input(case["relative_file"])

    command = [
        uvx_executable,
        "--from",
        CLI_PACKAGE,
        "check-jsonschema",
        "--schemafile",
        str(schema_file),
        "--output-format",
        "json",
        str(instance_file),
    ]

    print(f"\n=== {label} ===")
    result = _run_command(command)

    try:
        report = _parse_json_output(result, label)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return False

    expected_status = case["expected_status"]
    errors = report["errors"]

    if expected_status == "ok":
        passed = (
            result.returncode == 0
            and report.get("status") == "ok"
            and errors == []
        )

        if passed:
            print("PASS: real manifest accepted by official schema")
            return True

        _show_process_output(result)
        print(
            "FAIL: real manifest did not produce the expected clean success.",
            file=sys.stderr,
        )
        return False

    # An invalid fixture must fail for exactly its one intended violation.
    if (
        result.returncode == 0
        or report.get("status") != "fail"
        or len(errors) != 1
    ):
        _show_process_output(result)
        print(
            "FAIL: malformed fixture did not produce exactly one schema error.",
            file=sys.stderr,
        )
        return False

    error = errors[0]
    if not isinstance(error, dict):
        _show_process_output(result)
        print("FAIL: schema error entry is not an object.", file=sys.stderr)
        return False

    filename = error.get("filename")
    try:
        reported_file = Path(filename).resolve(strict=False)
    except (TypeError, OSError, RuntimeError):
        reported_file = None

    expected_path = case["expected_path"]
    expected_message = case["expected_message"]
    actual_path = error.get("path")
    actual_message = error.get("message")

    if (
        reported_file != instance_file
        or actual_path != expected_path
        or not isinstance(actual_message, str)
        or expected_message not in actual_message
    ):
        _show_process_output(result)
        print(
            "FAIL: schema violation did not match the expected input, "
            "instance path, and reason.",
            file=sys.stderr,
        )
        return False

    print(f"PASS: expected violation at {actual_path}")
    print(f"PASS: {actual_message}")
    return True


def main() -> int:
    try:
        inputs = [
            _resolve_named_input(case["relative_file"])
            for case in CASES
        ]

        uvx_executable = _resolve_and_check_cli()

        with tempfile.TemporaryDirectory(
            prefix="m5-plugin-schema-"
        ) as temporary_directory:
            schema_file = Path(temporary_directory) / "plugin.schema.json"
            _download_schema(schema_file)

            results = []
            for case, instance_file in zip(
                CASES, inputs, strict=True
            ):
                # Resolve again immediately before use; inputs must remain
                # explicit regular repository files, never symlink substitutions.
                if _resolve_named_input(case["relative_file"]) != instance_file:
                    raise ValidationError(
                        f"Input changed during validation: {case['relative_file']}"
                    )

                results.append(
                    _validate_case(
                        uvx_executable,
                        schema_file,
                        case,
                    )
                )

        if not all(results):
            print(
                "\nFAIL: official plugin-schema validation did not pass.",
                file=sys.stderr,
            )
            return 1

    except ValidationError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 1

    print("\nPASS: official plugin-schema positive and negative checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
