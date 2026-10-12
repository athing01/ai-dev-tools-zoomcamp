# Module 5 Permissions and Security Note

## Security posture

The Agent Extension Pack is a development-time review capability. The pack
itself does not configure AWS permissions, supply credentials, define production
endpoints, connect to databases, or add deployment tools. Effective capabilities
may still depend on the parent session and the active sandbox/network policy;
these boundaries must be verified in the target environment.

A passing agent review is advisory; a human and normal repository protections
remain responsible for merge and release decisions.

## Capability matrix

| Capability | Read | Write | Network | Credentials | Approval/guardrail |
| --- | --- | --- | --- | --- | --- |
| Root project instructions | Repository guidance only | None | None | None | Always read as project context |
| Portable API-review skill | User diff and allowlisted repo files | None | None required | None | User invocation; no patching |
| API-reviewer subagent | Diff, Module 3 contract, relevant tests | None (effective `sandbox_mode = "read-only"`); effective mode must be verified | Parent-session tools may be inherited; effective network restrictions must be verified separately; production access is prohibited. | None | Instructions are advisory; effective permission mode and negative tests are required |
| MCP contract tool | Fixed OpenAPI source and allowlisted fields | None | Local stdio through `.codex/config.toml` | None | Tool allowlist; invalid queries fail closed |
| Protected-path guardrail | Git diff metadata and paths | None | CI platform only | `contents: read` at most | Negative tests fail the check |
| Module 5 CI | Module 5 sources and fixtures | Ephemeral workspace only | No production network | No secrets | Independent workflow; no OIDC/AWS |
| Isolated demo | Disposable worktree and fixture code | Demo branch only | Local test services only | None | Discard branch/worktree; never merge demo-only change |

## MCP allowlist

The server must define permitted query values in code and validate them before
reading anything. The initial allowlist is:

```text
tasks_collection
task_item
schemas
```

The only source is the checked-in Module 3 API contract at a fixed repository
relative location, or an equivalent embedded snapshot generated during
implementation. The caller cannot provide a filesystem path, glob, URL,
command, SQL statement, or arbitrary JSON pointer. Output is limited to
endpoint/method/schema/response metadata needed for API review.

Negative security cases must prove rejection of:

- `../` and absolute paths;
- unknown endpoint names and unrecognized fields;
- shell-like strings such as `$(...)` or `; cat ...`;
- write verbs or mutation requests;
- requests for secrets, environment variables, `.aws`, `.codex`, `.venv`, or
  `node_modules`; and
- any network or AWS operation.

## Repo-local discovery and enablement

The implementation will add `.agents/plugins/marketplace.json` with marketplace
name `local-repo` and a local source path `./plugins/taskflow-agent-pack`.
It will add `.codex/config.toml` in stages. In Phase 1 it contains only the
repo-local enablement for `taskflow-agent-pack@local-repo` and does not reference
user-home paths. In Phase 3, after the server and locked environment exist, it
gains the named `taskflow_readonly` local stdio server entry. Codex project
trust may be required by the client; the clean-clone procedure must verify trust
without editing global Codex configuration. The client may maintain its normal
plugin cache under the user home directory; that cache is not a repository
change or an instruction to edit global settings.

The MCP command will run the locked repo-local project under
`module-5/mcp/pyproject.toml` using `uv run --project module-5/mcp ...`.
Plugin/layout/guardrail tools use a separate locked project at
`module-5/pyproject.toml` and `module-5/uv.lock`; MCP runtime/test dependencies
must not be required by that tooling project. Thus plugin and custom-agent
discovery are available from Phase 1, while MCP invocation becomes available only
after the Phase 3 registration.

## Plugin validation boundaries

Layer A may access the pinned `check-jsonschema==0.38.2` tool through `uvx`,
retrieve the canonical versioned schema when uncached, and store that schema
only in a controlled temporary location. It may require network access, but it
uses no credentials, AWS access, production endpoint, or deployment permission.
Layer A is official JSON Schema validation; it is not a project-policy check.
The official schema requires `$schema` and `name`; `version` and `description`
are optional portable metadata. Layer B separately requires non-empty string
values for all three metadata fields, so missing or empty `version`/`description`
fail project policy and must never be reported as official-schema failures.

The planned `module-5/guardrails/validate_official_plugin_schema.py` helper is
the single canonical Layer A positive/negative runner for CI and the demo. It
must first prove that the pinned CLI can be resolved and executed, retrieve and
parse the canonical versioned schema once per invocation into a controlled
temporary file, and fail explicitly if network retrieval or parsing fails. It
then uses that same schema file for the real manifest and both
official-schema-negative fixtures. It should prefer a machine-readable format
from the pinned CLI only if verified to expose the needed instance path and
validation keyword. Otherwise, a bounded version-pinned check over combined
stdout/stderr must identify a required-property violation for `$schema` in
`schema-invalid-missing-schema.json` and a type violation at `name` with
expected type `string` in `schema-invalid-name-type.json`. Generic nonzero
status or unrelated output is insufficient; tool resolution, network/retrieval,
schema parsing, and unexpected output must fail the helper. Validator output is
retained for diagnosis, and no key-presence fallback is permitted.

Layer B reads the fixed repository paths for the plugin root, manifest, skill,
and marketplace, or an explicitly supplied temporary `--repo-root` fixture.
Every repository/fixture filesystem read must remain within that explicitly
selected root; resolved paths outside it fail closed. `validate_plugin_layout.py`
enforces project metadata, safe filesystem structure, and marketplace
consistency without reimplementing the schema engine. Layer C supplies positive
and negative tests for those checks. A project-policy failure for missing/empty
`version` or `description` must not be reported as an official-schema failure
because those fields are optional in the portable schema.

The planned fixture paths are
`module-5/tests/fixtures/plugin-manifests/schema-invalid-missing-schema.json`,
`schema-invalid-name-type.json`, and
`policy-invalid-missing-version.json`. The first two are official-schema
negative inputs and must be executed by the pinned CLI helper; the last is a
project-policy negative input. Missing/empty `version` and `description` are
also covered by Layer B tests, independently of the official schema.

Validation logic must not inspect `.venv` or `node_modules` as project-owned
capabilities, and must not read secrets, credentials, AWS configuration,
user-global Codex configuration, or unrelated host files. Layer A may read its
explicitly named manifest and schema-negative fixture inputs, the canonical
schema fetched into a controlled temporary file, and normal runtime/dependency
files for the pinned CLI in its configured `uvx` cache. This cache is tool
runtime state, not permission to enumerate or inspect arbitrary home-directory
files. Layer B is confined to the selected repository root or temporary
repository-fixture root; Layer C may create and inspect only its explicit test
fixtures.

The validation/guardrail project uses `module-5/pyproject.toml` and
`module-5/uv.lock`; MCP-specific tests use the separate
`module-5/mcp/pyproject.toml` and `module-5/mcp/uv.lock` environment. No global
package installation is required: `uv` manages project-local environments from
the lockfiles, while `uvx` may obtain its pinned CLI in an isolated cache.
Schema retrieval may require network access when uncached.

## Protected repository boundaries

The guardrail must protect:

- `.github/workflows/ci.yml` and `.github/workflows/deploy.yml`;
- all three existing Module 4 workflows;
- `.github/workflows/ci-module-5.yml` must remain independent from those files;
- `.codex/agents/**`, `.codex/config.toml`, `.agents/plugins/**`,
  `plugins/taskflow-agent-pack/**`, `AGENTS.md`, and `module-5/**` are the
  complete Module 5 capability/configuration surface;
- `module-3/infra/**` and `module-3/deploy/**`;
- Module 3/4 production configuration and application source; and
- any future explicit protected path recorded in root instructions.

Module 5 additions may not weaken existing deployment workflows, add AWS
permissions, introduce credentials, or change TaskFlow behavior. The policy
must be tested with exact protected paths and descendants.

## Plugin and agent trust

The portable root plugin manifest must pass the official schema, which
requires `$schema` and `name`; Layer B project policy separately requires
non-empty string values for `name`, `version`, and `description`. It must
contain no secrets, fixed tokens, user-home paths, or implicit production URLs.
The skill is documentation/instructions, not a permission grant. The custom
agent must request `sandbox_mode = "read-only"`, but parent-session inheritance
and explicit overrides must be documented and verified. Do not claim shell
invocation is disabled unless the selected client configuration demonstrably
enforces that. Any future hook must be reviewed as executable code and fail
closed on malformed input. Read-only mode must not be treated as proof that
outbound network access is blocked. Verify and record the effective
sandbox/network policy in the target WSL2 environment before claiming that
production network access is technically prevented.

The plan targets Codex CLI `0.162.1`, but client behavior around plugin loading,
custom-agent discovery, MCP transports, and hook trust is version-sensitive.
Implementation must verify these behaviors locally and document deviations.

## Security acceptance

Security is accepted only when the implementation demonstrates:

1. An allowed MCP contract query succeeds.
2. Every negative MCP case is rejected without reading outside the fixed source.
3. The effective reviewer permission mode is read-only, and negative tests show
   no write or deployment behavior; this is not inferred from instructions alone.
4. CI has no AWS/OIDC/secrets permissions and is independent of deploy workflows.
5. A protected Module 3/4 path fails the guardrail negative test.
6. A Module 5-only diff passes the guardrail.
7. Final evidence contains no credential values or production access.
