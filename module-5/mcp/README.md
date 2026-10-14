# TaskFlow Read-only MCP Server

## Purpose

This project provides one local stdio MCP tool named
`get_taskflow_contract` for the TaskFlow API review workflow.

The server reads the fixed checked-in contract at
`module-3/openapi.yaml`. Callers cannot supply a filesystem path.

## Allowed queries

- `tasks_collection`: metadata for GET and POST `/api/tasks`
- `task_item`: metadata for PATCH and DELETE `/api/tasks/{task_id}`
- `schemas`: the allowlisted TaskFlow request, response, and status schemas

The tool accepts one required argument named `query`. Its value must be one
of the three supported query names. Additional arguments and unknown query
values are rejected.

The server exposes no file-write, shell, database, deployment, credential,
or production-service tool.

## Security boundary

The fixed-source allowlist is an application-level restriction. It does not
prove that the operating system blocks every possible filesystem or network
operation. Effective client sandbox permissions and network restrictions
must be assessed separately.

## Environment

The server has its own `pyproject.toml` and `uv.lock`. It does not reuse or
modify the root, Module 3, or Module 4 Python environments.

## Validation workflow

From the repository root, use the pinned course version of `uv`.

1. Generate the lockfile with `uv lock --project module-5/mcp`.
2. Synchronize dependencies with `uv sync --locked --project module-5/mcp`.
3. Run the server self-check with
   `uv run --locked --project module-5/mcp python module-5/mcp/taskflow_readonly_server.py --self-check`.
4. Run the allowlist and protocol tests with
   `uv run --locked --project module-5/mcp pytest module-5/tests/test_mcp_allowlist.py -q`.

Starting the server without `--self-check` runs its MCP stdio transport.
Standard output is reserved for MCP protocol messages.

## Codex registration

The repository-scoped MCP entry must be added to `.codex/config.toml` only
after this project and its lockfile exist and have been checked.

Live discovery and tool invocation through the repository configuration are
separate acceptance checks; successful syntax or unit tests alone do not
prove that Codex can start the configured server.
