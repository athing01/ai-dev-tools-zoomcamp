"""Fixed-source, read-only MCP access to the TaskFlow OpenAPI contract."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import mcp.server.stdio
import mcp.types as types
import yaml
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions


SERVER_NAME = "taskflow_readonly"
SERVER_VERSION = "0.1.0"
TOOL_NAME = "get_taskflow_contract"
SOURCE_LABEL = "module-3/openapi.yaml"
MAX_OUTPUT_BYTES = 64 * 1024

QUERY_CHOICES = (
    "tasks_collection",
    "task_item",
    "schemas",
)

ALLOWED_SCHEMAS = (
    "TaskStatus",
    "Task",
    "CreateTaskRequest",
    "UpdateTaskRequest",
    "ErrorResponse",
)

REF_PREFIX = "#/components/schemas/"
REPO_ROOT = Path(__file__).resolve().parents[2]

server = Server(SERVER_NAME, version=SERVER_VERSION)


class ContractSourceError(RuntimeError):
    """The fixed contract source is missing or invalid."""


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) for key in value
    ):
        raise ContractSourceError(f"{label} must be a string-keyed mapping.")
    return value


def _resolve_contract_path(repo_root: Path | None = None) -> Path:
    """Resolve only the fixed contract; reject symlink substitutions."""
    root_source = REPO_ROOT if repo_root is None else repo_root

    try:
        root = root_source.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ContractSourceError("Repository root is unavailable.") from exc

    module_dir = root / "module-3"
    contract = module_dir / "openapi.yaml"

    if module_dir.is_symlink() or contract.is_symlink():
        raise ContractSourceError(
            "The module directory and contract must not be symlinks."
        )

    try:
        resolved = contract.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ContractSourceError("The fixed contract is unavailable.") from exc

    if resolved != contract or not resolved.is_file():
        raise ContractSourceError(
            "The fixed contract must be a regular repository file."
        )

    return resolved


def _load_document(repo_root: Path | None = None) -> dict[str, Any]:
    path = _resolve_contract_path(repo_root)

    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ContractSourceError("The fixed contract could not be parsed.") from exc

    return _mapping(document, "OpenAPI document")


def _project_parameters(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ContractSourceError("OpenAPI parameters must be a list.")

    fields = ("name", "in", "required", "description", "schema")
    result = []

    for item in value:
        parameter = _mapping(item, "parameter")
        result.append(
            {key: parameter[key] for key in fields if key in parameter}
        )

    return result


def _project_json_content(value: Any, label: str) -> dict[str, Any]:
    content = _mapping(value, label)
    media_value = content.get("application/json")

    if media_value is None:
        return {}

    media = _mapping(media_value, f"{label}.application/json")

    if "schema" not in media:
        return {}

    return {"application/json": {"schema": media["schema"]}}


def _project_request_body(value: Any) -> dict[str, Any]:
    body = _mapping(value, "request body")
    result = {
        key: body[key]
        for key in ("description", "required")
        if key in body
    }

    if "content" in body:
        content = _project_json_content(body["content"], "request content")
        if content:
            result["content"] = content

    return result


def _project_response(value: Any, status_code: str) -> dict[str, Any]:
    response = _mapping(value, f"response {status_code}")
    result = {}

    if "description" in response:
        result["description"] = response["description"]

    if "content" in response:
        content = _project_json_content(
            response["content"], f"response {status_code} content"
        )
        if content:
            result["content"] = content

    return result


def _project_operation(value: Any, method: str) -> dict[str, Any]:
    operation = _mapping(value, f"{method} operation")
    fields = ("operationId", "summary", "description", "deprecated")
    result = {
        key: operation[key]
        for key in fields
        if key in operation
    }

    if "parameters" in operation:
        result["parameters"] = _project_parameters(operation["parameters"])

    if "requestBody" in operation:
        result["requestBody"] = _project_request_body(operation["requestBody"])

    responses = _mapping(
        operation.get("responses"), f"{method} responses"
    )
    if not responses:
        raise ContractSourceError(f"{method} has no declared responses.")

    result["responses"] = {
        str(code): _project_response(response, str(code))
        for code, response in responses.items()
    }

    return result


def _project_endpoint(
    document: dict[str, Any],
    endpoint: str,
    methods: tuple[str, ...],
) -> dict[str, Any]:
    paths = _mapping(document.get("paths"), "OpenAPI paths")
    path_item = _mapping(paths.get(endpoint), f"allowlisted endpoint {endpoint}")

    result: dict[str, Any] = {"endpoint": endpoint}

    if "parameters" in path_item:
        result["path_parameters"] = _project_parameters(
            path_item["parameters"]
        )

    operations = {}
    for method in methods:
        raw_operation = path_item.get(method)
        if raw_operation is None:
            raise ContractSourceError(
                f"Expected operation is missing: {method.upper()} {endpoint}"
            )

        operations[method.upper()] = _project_operation(
            raw_operation, method.upper()
        )

    result["operations"] = operations
    return result


def _validate_schema_refs(value: Any) -> None:
    """Allow only local references to explicitly approved schema names."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "$ref":
                if not isinstance(item, str) or not item.startswith(REF_PREFIX):
                    raise ContractSourceError(
                        "External or non-schema references are not permitted."
                    )

                schema_name = item[len(REF_PREFIX):]
                if schema_name not in ALLOWED_SCHEMAS:
                    raise ContractSourceError(
                        "Reference targets a schema outside the allowlist."
                    )
            else:
                _validate_schema_refs(item)

    elif isinstance(value, list):
        for item in value:
            _validate_schema_refs(item)


def _bound_output(payload: dict[str, Any]) -> dict[str, Any]:
    _validate_schema_refs(payload)

    try:
        encoded = json.dumps(
            payload, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractSourceError("Contract output is not serializable.") from exc

    if len(encoded) > MAX_OUTPUT_BYTES:
        raise ContractSourceError("Contract output exceeds the size limit.")

    return payload


def build_payload(
    query: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build an allowlisted payload; repo_root is only for isolated tests."""
    if not isinstance(query, str) or query not in QUERY_CHOICES:
        raise ValueError("Unsupported query.")

    document = _load_document(repo_root)
    info = _mapping(document.get("info"), "OpenAPI info")

    common = {
        "source": SOURCE_LABEL,
        "api_title": info.get("title"),
        "api_version": info.get("version"),
        "query": query,
    }

    if query == "tasks_collection":
        section = _project_endpoint(
            document, "/api/tasks", ("get", "post")
        )
        payload = {**common, **section}

    elif query == "task_item":
        section = _project_endpoint(
            document, "/api/tasks/{task_id}", ("patch", "delete")
        )
        payload = {**common, **section}

    else:
        components = _mapping(
            document.get("components"), "OpenAPI components"
        )
        schemas = _mapping(components.get("schemas"), "OpenAPI schemas")
        selected = {}

        for name in ALLOWED_SCHEMAS:
            if name not in schemas:
                raise ContractSourceError(
                    f"Required schema is missing: {name}"
                )
            selected[name] = _mapping(schemas[name], f"schema {name}")

        payload = {**common, "schemas": selected}

    return _bound_output(payload)


def _tool_text(text: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=text)]


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Expose exactly one tool with a closed input schema."""
    return [
        types.Tool(
            name=TOOL_NAME,
            description=(
                "Read allowlisted TaskFlow API metadata from the fixed "
                "checked-in OpenAPI contract."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "enum": list(QUERY_CHOICES),
                        "description": "The TaskFlow contract section to retrieve.",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        )
    ]


@server.call_tool()
async def call_tool(
    name: str,
    arguments: dict[str, Any] | None,
) -> list[types.TextContent]:
    """Reject unknown tools, invalid query values, and extra arguments."""
    if name != TOOL_NAME:
        raise ValueError("Unknown tool.")

    args = arguments if arguments is not None else {}
    if set(args) != {"query"}:
        raise ValueError("Exactly one argument named 'query' is required.")

    query = args["query"]
    if not isinstance(query, str) or query not in QUERY_CHOICES:
        raise ValueError("Unsupported query.")

    try:
        payload = build_payload(query)
        result_text = json.dumps(payload, ensure_ascii=False, indent=2)
    except (ContractSourceError, ValueError):
        raise ValueError("The requested contract section is unavailable.") from None

    return _tool_text(result_text)


async def _run_server() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=SERVER_NAME,
                server_version=SERVER_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def _self_check() -> dict[str, Any]:
    report = {}

    for query in QUERY_CHOICES:
        payload = build_payload(query)
        report[query] = {
            "endpoint": payload.get("endpoint"),
            "methods": list(payload.get("operations", {}).keys()),
            "schemas": list(payload.get("schemas", {}).keys()),
        }

    return {
        "status": "ok",
        "source": SOURCE_LABEL,
        "queries": report,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Check the fixed contract without starting the MCP server.",
    )
    args = parser.parse_args(argv)

    if args.self_check:
        try:
            report = _self_check()
        except (ContractSourceError, ValueError) as exc:
            print(f"Self-check failed: {exc}", file=sys.stderr)
            return 1

        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    asyncio.run(_run_server())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
