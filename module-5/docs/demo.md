# Module 5 Demo Plan

## Demo boundary

The demo is a disposable feature experiment, not a Module 5 product change.
Run it only after the required Phase 1, Phase 2, and Phase 3 capabilities have
been implemented and verified; the demo itself is Phase 5 work after the CI
guardrail phase. Create a separate worktree or branch from the current TaskFlow
baseline, for example `codex/m5-taskflow-api-demo`, and delete/archive it after
evidence is captured.
Do not merge the demo-only application change into `main` as part of
this phase. Do not deploy it.

The proposed small feature is a read-only `GET /api/tasks/count` endpoint in
the disposable TaskFlow copy. It is intentionally small but exercises route,
schema, OpenAPI, tests, and API compatibility review. If the current product
spec or implementation makes this endpoint inappropriate, substitute an
equally small isolated API change and record the decision; do not change main.

## Script and evidence

1. In the disposable worktree, show baseline commit, branch, and clean status.
   Capture the worktree path.
2. Ask the primary agent to plan the feature. Capture evidence that it read
   root `AGENTS.md` and honored no-deployment/protected-path rules.
3. Review the repo-local `.agents/plugins/marketplace.json` and
   `.codex/config.toml`; verify `taskflow-agent-pack@local-repo` is enabled,
   the skill and `taskflow-api-reviewer` custom agent are discoverable, and the
   Phase 3 `taskflow_readonly` MCP stdio server registration is present. If the
   client requires project trust, verify it without editing global Codex
   configuration. The client may maintain its normal user-home plugin cache.
4. Synchronize the `module-5` validation project with
   `uv sync --locked --project module-5`. Run the static plugin checks before the
   demo: Layer A official-schema validation of the real manifest and both
   schema-negative fixtures, Layer B project-policy/filesystem/marketplace
   validation, and Layer C positive and negative layout tests. The Layer A helper
   must retrieve and parse the canonical schema once, use it for the real manifest
   and both fixtures, and verify the expected missing-`$schema` and
   non-string-`name` diagnostics. Do not rely on an existing root, `.venv`, or
   Module 3/4 Python environment. A generic nonzero status is insufficient: tool
   resolution, network/retrieval, schema parsing, or unexpected diagnostic output
   must fail the helper, with stdout/stderr retained. Record that missing or
   empty `version` and `description` are rejected by Layer B project policy, not
   attributed to Layer A.
5. Separately perform the real Codex discovery checks: plugin discovery,
   custom-agent availability, and Phase 3 MCP registration/invocation through
   the configured stdio server. Static JSON/layout validation is not evidence
   of Codex discovery. After Phase 3, synchronize the separate MCP project with
   `uv sync --locked --project module-5/mcp` before running its allowlist tests
   or server self-check.
6. Invoke `taskflow-api-review` before implementation against the proposed
   contract. Capture its checklist/output.
7. Make the demo-only endpoint and focused tests in the disposable worktree.
8. Invoke `taskflow-api-reviewer` on the demo diff. Verify its effective
   permission mode is read-only in the parent session, including inherited or
   overridden settings. Do not treat its instructions as enforcement and do
   not claim shell invocation is disabled. Capture findings with file evidence.
9. Call `get_taskflow_contract` through the configured Phase 3 local stdio server for
   `tasks_collection` or `schemas`; capture the structured response. Then call
   it with an invalid query and capture the fail-closed response.
10. Run the guardrail with a positive Module 5-only fixture and a negative
   fixture attempting to modify `.github/workflows/deploy.yml` or
   `module-3/infra/**`. Capture output; the negative case must fail.
11. Run focused disposable-worktree API tests and inspect `git diff --check`,
   `git diff --stat`, and the full final diff. Capture human review.
12. Remove/archive the disposable worktree or branch. Verify the primary branch
   has no demo-only files or behavior changes.

## Expected evidence

| Required demonstration | Evidence |
| --- | --- |
| Instructions read | Agent output naming root `AGENTS.md` and applying its boundaries |
| Workflow invoked | Skill name, input, and structured API-review output |
| Specialized API reviewer used | Subagent identity, read-only scope, findings, and file references |
| MCP tool called | Allowed structured response and invalid-query rejection |
| Guardrail checked/prevented an action | Positive pass plus protected-path negative failure |
| Final diff reviewed | `git diff --check`, diff summary, human review note, and cleanup |

## Validation commands

Planned implementation-phase examples, run from the repository root:

```bash
# Validation, plugin-layout tests, and protected-path checks.
uv sync --locked --project module-5
uv run --project module-5 python module-5/guardrails/validate_official_plugin_schema.py
uv run --project module-5 python module-5/guardrails/validate_plugin_layout.py
uv run --project module-5 pytest module-5/guardrails/test_plugin_layout.py -q
uv run --project module-5 pytest module-5/guardrails/test_protected_paths.py -q
# Set BASE_SHA and HEAD_SHA to the actual commit SHAs first.
uv run --project module-5 python module-5/guardrails/protected_paths.py --base "$BASE_SHA" --head "$HEAD_SHA"

# Phase 3 onward: MCP server and its allowlist tests use the separate MCP environment.
uv sync --locked --project module-5/mcp
uv run --project module-5/mcp pytest module-5/tests/test_mcp_allowlist.py -q
uv run --project module-5/mcp python module-5/mcp/taskflow_readonly_server.py --self-check

git status --short --branch
git diff --check
git diff --stat
```

The validation/guardrail project is `module-5/pyproject.toml` with
`module-5/uv.lock`; the MCP server/test project is independently defined by
`module-5/mcp/pyproject.toml` and `module-5/mcp/uv.lock`. These commands are
planned examples and must be checked against the files created during
implementation. Do not claim any command passed during the planning phase.

## Failure cases

- If the agent does not read `AGENTS.md`, stop and fix discovery.
- If the skill edits files, it fails the reusable-workflow gate.
- If the reviewer can write, access AWS, or invoke deployment, it fails the
  subagent/security gate.
- If an invalid MCP query reads an arbitrary path or executes anything, stop and
  redesign the server allowlist.
- If the protected-path negative fixture passes, fail the Module 5 gate.
- If the demo touches Module 3/4 workflows or infrastructure, discard the demo
  branch and investigate the boundary failure.
- If the final diff includes generated files, secrets, credentials, `.venv`, or
  `node_modules`, remove them from the disposable worktree before evidence.
- If a client-version mismatch prevents discovery, record it as a compatibility
  risk and do not silently alter user-global configuration.
