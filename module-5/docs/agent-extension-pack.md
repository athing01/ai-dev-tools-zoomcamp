# Agent Extension Pack — Proposed Design

## Goal

The pack gives an agent a small, auditable toolchain for reviewing TaskFlow API
changes. It teaches a reusable procedure, delegates a focused review to a
specialist, exposes one bounded read-only MCP capability, and enforces the
repository boundary in CI.

It is not an autonomous deployer and is not a replacement for the Module 3/4
application or release system.

## Components

### Project instructions

The implementation will add a root `AGENTS.md` describing the repository map,
commands, authoritative Module 3/4 constraints, Module 5 paths, security
boundaries, and evidence expectations. It will explicitly say that generated
dependency directories such as `.venv` and `node_modules` are not project-owned
capability inventories.

### Portable plugin and reusable skill

`plugins/taskflow-agent-pack/plugin.json` will be a portable manifest with a
stable kebab-case `name`, optional portable metadata fields `version` and
`description`, and no machine-specific absolute paths. The official portable
schema requires `$schema` and `name`; this project independently requires
non-empty string values for `name`, `version`, and `description` through Layer
B project policy. The implementation will validate both responsibilities
separately against the portable plugin schema and project policy. Its reusable
skill will live at:

```text
plugins/taskflow-agent-pack/skills/taskflow-api-review/SKILL.md
```

The skill will define inputs (diff/base, API contract, and test locations), a
repeatable review sequence, output headings, and stop conditions. It will
separate facts from inferences, identify breaking changes, and recommend tests.
It will not edit files, run deployment commands, access AWS, or treat model
confidence as approval.

### Three-layer plugin validation

Plugin validation has separate responsibilities:

1. Layer A uses the pinned `check-jsonschema==0.38.2` CLI against the real
   `plugins/taskflow-agent-pack/plugin.json` and the canonical versioned schema
   `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`. The manifest's
   `$schema` must use that URL. The official schema requires `$schema` and
   `name`, while `version` and `description` are optional in the portable
   specification.
2. Layer B uses `module-5/guardrails/validate_plugin_layout.py` for project
   policy, filesystem structure, and marketplace consistency. It requires
   non-empty string `name`, `version`, and `description`, the exact skill path,
   safe non-symlink paths, and the expected `local-repo` marketplace entry.
   It does not reimplement or claim to perform JSON Schema validation.
3. Layer C uses `module-5/guardrails/test_plugin_layout.py` and temporary
   fixtures for positive and negative policy/layout/marketplace cases. Official
   schema negatives use the actual pinned CLI; missing `version` and
   `description` are project-policy negatives, not official-schema failures.

Layer A may access the pinned validator through `uvx`, retrieve the canonical
versioned schema when uncached, and store it only in a controlled temporary
location. The future `module-5/guardrails/validate_official_plugin_schema.py`
helper is the single canonical Layer A positive/negative runner for CI and the
demo. On each invocation it will resolve the pinned CLI, retrieve and parse the
schema once, and use that same schema for the real manifest and both malformed
fixtures. It will prefer a machine-readable diagnostic format from the pinned
CLI only if that format is verified to expose the needed instance path and
validation keyword. Otherwise it will apply bounded, version-pinned checks to
combined stdout/stderr: missing `$schema` must be identified as a
required-property violation, and `name` must be identified as a type violation
whose expected type is `string`. Tool resolution, network/retrieval, schema
parsing, unexpected output, or a CLI-output compatibility change are fatal and
retain useful stdout/stderr; the project does not silently substitute a
required-key-only smoke check.

Layer A may read only its explicitly named manifest and schema-negative fixture
inputs, the canonical schema fetched into a controlled temporary file, and
normal executable/dependency files needed by the pinned CLI in its configured
`uvx` cache. That cache is tool-runtime state, not permission to enumerate or
inspect arbitrary home-directory files. Layer A must not read secrets,
credentials, AWS configuration, user-global Codex configuration, or unrelated
host files.

Layer B is confined to the explicitly selected repository root or temporary
repository-fixture root; resolved paths outside that root must fail closed.
Layer C may create and inspect its own temporary test fixtures, but must not read
unrelated host files. The validation/guardrail project uses
`module-5/pyproject.toml` and `module-5/uv.lock`; MCP-specific tests use the
separate `module-5/mcp/pyproject.toml` and `module-5/mcp/uv.lock` environment.

### Project-scoped API reviewer

`.codex/agents/taskflow-api-reviewer.toml` will define a narrow custom agent
with required `name`, `description`, and `developer_instructions` fields plus
`sandbox_mode = "read-only"`. Its instructions will require tracing the actual
API route and schema, comparing the proposed contract with the current OpenAPI
document, checking status codes/validation/persistence/tests, and reporting
concrete findings with file/symbol evidence.

Read-only behavior is an effective configuration requirement, not a claim made
by the instructions. The custom agent can inherit parent-session settings when
its file omits them, and explicit spawn/session settings or client policy may
override them. The implementation must inspect the effective permission mode
in the real parent session before the demo. Shell invocation is not claimed to
be technically disabled; the test verifies that the effective mode prevents
writes and that the reviewer does not deploy, access AWS, or access production.

The agent is separate from the plugin so another repository can use the skill
without importing this TaskFlow-specific reviewer.

### Read-only MCP server

`module-5/mcp/taskflow_readonly_server.py` will expose one stdio MCP tool,
`get_taskflow_contract`, with enum-like queries `tasks_collection`, `task_item`,
or `schemas`. It may read the fixed checked-in `module-3/openapi.yaml` (or a
validated embedded contract snapshot), but it may not accept a caller-supplied
path. It returns only allowlisted endpoint, method, schema, and response
metadata needed for API review.

It will not expose filesystem browsing, arbitrary file reads, shell execution,
writes, database queries, network fetches, AWS APIs, secrets, or production
URLs. Invalid enum values and unexpected arguments fail closed. Response size
will be bounded and logs will contain no sensitive data.

The repository configuration is progressive. In Phase 1, `.codex/config.toml`
contains only the repo-local plugin enablement for the plugin discovered from
`.agents/plugins/marketplace.json`. In Phase 3, after the server,
`module-5/mcp/pyproject.toml`, and `uv.lock` exist, the implementation appends
the named `taskflow_readonly` stdio registration to that existing file. Its
command runs `uv run --project module-5/mcp ...`; the clean-clone procedure
then verifies invocation through Codex and this repository-scoped registration.
The client may maintain its normal plugin cache under the user home directory,
but the clean-clone procedure must not edit global Codex configuration.

Phase 4 creates a dedicated non-package validation project at
`module-5/pyproject.toml`, locked by `module-5/uv.lock`, with `pytest` in its
development dependencies. The MCP server and its allowlist tests use the
independent non-package project in `module-5/mcp/pyproject.toml` and
`module-5/mcp/uv.lock`, which also locks its MCP runtime and test dependencies.
Clean-clone verification synchronizes each project with
`uv sync --locked --project <path>`; it must not depend on pre-existing root,
Module 3, or Module 4 environments.

### Guardrail and independent workflow

The effective guardrail is a tested protected-path policy, not a prompt-only
instruction. It will be called by `.github/workflows/ci-module-5.yml`, named
exactly `CI — Module 5`.

The workflow is independent from the existing five workflows: it has its own
triggers, jobs, concurrency, and checks; it does not use `workflow_run`, deploy,
OIDC, AWS, secrets, or production services. It synchronizes the locked
`module-5` tooling project for schema/layout/protected-path validation and the
separate `module-5/mcp` project for MCP allowlist tests. It must not rely on
pre-existing virtual environments. Its path filters cover:

- `AGENTS.md`;
- `.agents/plugins/**`;
- `.codex/agents/**` and `.codex/config.toml`;
- `module-5/**`;
- `plugins/taskflow-agent-pack/**`; and
- `.github/workflows/ci-module-5.yml`.

Its planned validation commands run plugin/layout/guardrail checks through the
locked Module 5 tooling project and MCP server tests through the separate MCP
project. The implementation phase must create `module-5/pyproject.toml` and
`module-5/uv.lock` with `pytest` as a development dependency in a non-package
project; `module-5/mcp/pyproject.toml` and `module-5/mcp/uv.lock` independently
lock the MCP runtime and test dependencies. CI synchronizes both environments
with `uv sync --locked --project <path>` and never reuses an existing virtual
environment.

```bash
uv sync --locked --project module-5
uv run --project module-5 python module-5/guardrails/validate_official_plugin_schema.py
uv run --project module-5 python module-5/guardrails/validate_plugin_layout.py
uv run --project module-5 pytest module-5/guardrails/test_plugin_layout.py -q
uv run --project module-5 pytest module-5/guardrails/test_protected_paths.py -q
# Set BASE_SHA and HEAD_SHA to the actual commit SHAs first.
uv run --project module-5 python module-5/guardrails/protected_paths.py --base "$BASE_SHA" --head "$HEAD_SHA"

# After Phase 3, validate the MCP environment independently.
uv sync --locked --project module-5/mcp
uv run --project module-5/mcp pytest module-5/tests/test_mcp_allowlist.py -q
uv run --project module-5/mcp python module-5/mcp/taskflow_readonly_server.py --self-check
```

The helper is the single CI schema-positive and schema-negative command. It validates
the real manifest and both
`module-5/tests/fixtures/plugin-manifests/schema-invalid-missing-schema.json`
and `schema-invalid-name-type.json` with the same retrieved official schema.
It fails if either malformed fixture passes, if the pinned CLI cannot execute,
if the schema cannot be retrieved or parsed, or if output does not identify the
expected violation. Missing or empty `version` and `description` remain Layer B
project-policy cases, not official-schema failures. No global package
installation is required; `uvx` may obtain the pinned CLI in its isolated
cache, and schema retrieval may require network access when uncached.

## End-to-end flow

```text
root AGENTS.md
      ↓
taskflow-api-review skill ──→ taskflow-api-reviewer subagent
      ↓                                  ↓
bounded MCP contract lookup ←──── review evidence
      ↓
CI protected-path guardrail
      ↓
isolated demo diff → human final diff review
```

The arrows represent evidence flow, not authorization. A successful review does
not authorize a deployment or merge.

## Evidence produced by implementation

Preserve command output or screenshots showing skill invocation, reviewer
findings, an allowed MCP call, a rejected MCP call, a failed protected-path
negative test, and the final `git diff` review. Evidence must omit credentials
and must not imply a deployment occurred.
