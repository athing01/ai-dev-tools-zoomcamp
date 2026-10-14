"""Tests for the TaskFlow read-only MCP allowlist."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MCP_DIR = Path(__file__).resolve().parents[1] / "mcp"
SERVER_PATH = MCP_DIR / "taskflow_readonly_server.py"
REPO_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(MCP_DIR))
import taskflow_readonly_server as server  # noqa: E402


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _text_content(result: object) -> str:
    return "\n".join(
        block.text
        for block in getattr(result, "content", [])
        if getattr(block, "type", None) == "text"
    )


def _is_error(result: object) -> bool:
    return bool(
        getattr(result, "isError", False)
        or getattr(result, "is_error", False)
    )


def test_tasks_collection_returns_only_expected_operations() -> None:
    payload = server.build_payload("tasks_collection")

    assert payload["source"] == "module-3/openapi.yaml"
    assert payload["endpoint"] == "/api/tasks"
    assert set(payload["operations"]) == {"GET", "POST"}
    assert (
        payload["operations"]["POST"]["responses"]["422"]["content"]
        ["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )


def test_task_item_returns_only_expected_operations() -> None:
    payload = server.build_payload("task_item")

    assert payload["endpoint"] == "/api/tasks/{task_id}"
    assert set(payload["operations"]) == {"PATCH", "DELETE"}
    assert payload["path_parameters"][0]["name"] == "task_id"
    assert "404" in payload["operations"]["DELETE"]["responses"]


def test_schema_query_returns_only_allowlisted_schemas() -> None:
    payload = server.build_payload("schemas")

    assert set(payload["schemas"]) == set(server.ALLOWED_SCHEMAS)
    assert payload["schemas"]["TaskStatus"]["enum"] == [
        "todo",
        "in_progress",
        "done",
    ]


@pytest.mark.parametrize(
    "query",
    [
        "unknown_endpoint",
        "/etc/passwd",
        "../../module-4/AGENTS.md",
        "shell",
        "write_file",
    ],
)
def test_unknown_queries_are_rejected(query: str) -> None:
    with pytest.raises(ValueError, match="Unsupported query"):
        server.build_payload(query)


def test_contract_path_is_fixed_to_repository_source() -> None:
    expected = REPO_ROOT / "module-3" / "openapi.yaml"

    assert server._resolve_contract_path() == expected.resolve()
    assert expected.is_file()


def test_symlinked_contract_file_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    module_dir = root / "module-3"
    module_dir.mkdir(parents=True)

    outside = tmp_path / "outside.yaml"
    outside.write_text("secret: must not be read\n", encoding="utf-8")
    (module_dir / "openapi.yaml").symlink_to(outside)

    with pytest.raises(server.ContractSourceError, match="must not be symlinks"):
        server._resolve_contract_path(root)


def test_symlinked_module_directory_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    outside = tmp_path / "outside-module"
    outside.mkdir()
    (outside / "openapi.yaml").write_text(
        "openapi: 3.0.3\n", encoding="utf-8"
    )
    (root / "module-3").symlink_to(outside, target_is_directory=True)

    with pytest.raises(server.ContractSourceError, match="must not be symlinks"):
        server._resolve_contract_path(root)


def test_response_size_limit_is_enforced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(server, "MAX_OUTPUT_BYTES", 1)

    with pytest.raises(server.ContractSourceError, match="size limit"):
        server.build_payload("tasks_collection")


@pytest.mark.anyio
async def test_stdio_tool_enforces_allowlist() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
    )

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            assert [tool.name for tool in tools] == [server.TOOL_NAME]

            schema = (
                getattr(tools[0], "inputSchema", None)
                or getattr(tools[0], "input_schema", None)
            )
            assert schema["type"] == "object"
            assert schema["required"] == ["query"]
            assert schema["additionalProperties"] is False
            assert set(schema["properties"]) == {"query"}
            assert set(schema["properties"]["query"]["enum"]) == set(
                server.QUERY_CHOICES
            )

            allowed = await session.call_tool(
                server.TOOL_NAME,
                {"query": "tasks_collection"},
            )
            assert not _is_error(allowed)

            payload = json.loads(_text_content(allowed))
            assert payload["endpoint"] == "/api/tasks"
            assert set(payload["operations"]) == {"GET", "POST"}

            rejected_calls = [
                (
                    server.TOOL_NAME,
                    {"query": "unknown_endpoint"},
                ),
                (
                    server.TOOL_NAME,
                    {"query": "schemas", "path": "/etc/passwd"},
                ),
                ("read_file", {"path": "/etc/passwd"}),
                (
                    "write_file",
                    {"path": str(REPO_ROOT / "README.md"), "content": "unsafe"},
                ),
                ("run_shell", {"command": "printf unsafe"}),
            ]

            for name, arguments in rejected_calls:
                result = await session.call_tool(name, arguments)
                assert _is_error(result), (
                    f"Expected rejected call: {name} with {arguments!r}"
                )


def test_self_check_reports_all_supported_queries() -> None:
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            str(SERVER_PATH),
            "--self-check",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr

    report = json.loads(result.stdout)
    assert report["status"] == "ok"
    assert set(report["queries"]) == set(server.QUERY_CHOICES)
