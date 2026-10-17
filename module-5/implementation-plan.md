# Module 5 — Agent Extension Pack Implementation Plan

## Status and scope

This is a planning-only artifact for branch `m5/agent-extension-pack` at base
`06ba7e3c237cd1995f231a89f940c00b402559a7`. No Module 5 runtime code, agent
configuration, hooks, tests, or workflow is created by this phase.

The current repository was inspected directly. It contains the Module 3 and
Module 4 TaskFlow implementations, infrastructure, deployment paths, and five
existing GitHub Actions workflows.

The design preserves the existing TaskFlow product and deployment architecture.
The implementation phase must not edit Module 3/4 application, infrastructure,
production configuration, or deployment workflows.

## Proposed capability map

| Minimum requirement | Proposed file(s) | Concrete acceptance test |
| --- | --- | --- |
| One project instructions file | `AGENTS.md` at repository root | A clean-clone agent task shows it read root instructions; protected-path behavior is verified. |
| One reusable skill/workflow/command | `plugins/taskflow-agent-pack/skills/taskflow-api-review/SKILL.md` | Invoke it against a fixture API change; it produces a contract diff, risks, and test recommendations without editing. |
| One specialized subagent | `.codex/agents/taskflow-api-reviewer.toml` | Spawn it on the isolated demo diff in an effective read-only permission mode; it reports API findings with citations and does not edit. |
| One MCP tool/server | `module-5/mcp/taskflow_readonly_server.py` plus `.codex/config.toml` stdio registration | An allowlisted contract query succeeds through the configured server; unknown endpoint/path/shell requests fail. |
| One hook or effective guardrail | `module-5/guardrails/`, exercised by `.github/workflows/ci-module-5.yml` | A protected Module 3/4 change fails CI; a Module 5-only change passes. |
| One small plugin/extension package OR custom agent | `plugins/taskflow-agent-pack/plugin.json` | Manifest and portable skill layout validate on a clean clone; no credentials or machine-specific paths exist. |
| One permission/security note | `module-5/docs/permissions.md` | Every capability has a documented read/write/network/credential boundary and a denial test. |

The custom agent and plugin are deliberately separate: the plugin is portable
and reusable across projects; the custom agent is narrow, project-scoped, and
Codex-specific under `.codex/agents/`.

## Proposed implementation layout

```text
AGENTS.md
.agents/plugins/marketplace.json
.codex/config.toml
.codex/agents/taskflow-api-reviewer.toml
module-5/
  pyproject.toml
  uv.lock
  guardrails/{protected_paths.py,test_protected_paths.py,validate_official_plugin_schema.py,validate_plugin_layout.py,test_plugin_layout.py}
  mcp/{taskflow_readonly_server.py,README.md,pyproject.toml,uv.lock}
  tests/test_mcp_allowlist.py
  tests/fixtures/plugin-manifests/
    schema-invalid-missing-schema.json
    schema-invalid-name-type.json
    policy-invalid-missing-version.json
plugins/taskflow-agent-pack/
  plugin.json
  skills/taskflow-api-review/SKILL.md
.github/workflows/ci-module-5.yml
```

These are future implementation paths; Phase 1 creates none of them except the five
requested Markdown documents. The implementation must use the pinned course
tooling (`uv 0.12.23`) and must not create environments or install dependencies in Phase 1.

`module-5/pyproject.toml` and `module-5/uv.lock` define a dedicated validation
and guardrail-test project. It will declare `pytest` as a development dependency,
record the resolved dependency set in `uv.lock`, and configure the project as a
non-package tooling environment so `uv` does not try to install a Python package
that this directory does not provide. Plugin/schema/layout and protected-path
checks run in this environment.

`module-5/mcp/pyproject.toml` and `module-5/mcp/uv.lock` remain a separate
environment for the MCP server and its tests. MCP runtime dependencies must not
be pulled into the validation project merely to run plugin-layout checks. The
MCP allowlist test at `module-5/tests/test_mcp_allowlist.py` runs under the MCP
project environment, which must also declare its test dependency (`pytest`) in
its development dependencies. Both lockfiles are committed as intended source
files; generated `.venv` directories and tool caches are not.

The future portable root `plugins/taskflow-agent-pack/plugin.json` must include
the canonical `$schema` URL and official-schema `name` field. The portable
specification makes `version` and `description` optional metadata; this project
nevertheless requires non-empty string values for `name`, `version`, and
`description` through project policy. The planned validation must keep those
responsibilities separate and confirm that the skill is under the fixed root
`skills/` directory.

## Exact repo-local discovery and staged MCP registration

The implementation will add `.agents/plugins/marketplace.json` with top-level
marketplace name `local-repo` and this repo-relative plugin entry:

```json
{
  "name": "local-repo",
  "plugins": [
    {
      "name": "taskflow-agent-pack",
      "source": { "source": "local", "path": "./plugins/taskflow-agent-pack" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Productivity"
    }
  ]
}
```

In Phase 1, it will add `.codex/config.toml` with only this repo-scoped plugin enablement key:

```toml
[plugins."taskflow-agent-pack@local-repo"]
enabled = true
```

The MCP registration is deliberately deferred until Phase 3, after the server,
`module-5/mcp/pyproject.toml`, and `uv.lock` exist. At that point, append the
following local stdio server entry to the existing `.codex/config.toml`; do not
register a server that is not yet present during Phase 1:

```toml
[mcp_servers.taskflow_readonly]
command = "uv"
args = ["run", "--project", "module-5/mcp", "python", "module-5/mcp/taskflow_readonly_server.py"]
```

The plugin enablement syntax must be checked during Phase 1 against CLI
`0.162.1`. The MCP server entry and its syntax must be checked during Phase 3.
The clean-clone gate must prove that the configured server starts and that
`get_taskflow_contract` is invokable; documented manual launching is not a
substitute. If the client rejects this local-server entry, implementation is
blocked until the configuration mechanism is verified and the affected planning
documents are updated consistently.

## Three-layer plugin validation

Validation is deliberately split into independent layers:

### Layer A — Official portable manifest schema

The real portable manifest is `plugins/taskflow-agent-pack/plugin.json`. It must
set `$schema` to
`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json` and pass the
canonical versioned Agent Plugins schema through the pinned `check-jsonschema`
CLI:

```bash
uvx --from check-jsonschema==0.38.2 check-jsonschema \
  --schemafile https://agent-plugins.org/schemas/1.0.0/plugin.schema.json \
  plugins/taskflow-agent-pack/plugin.json
```

This direct command is used during implementation Phase 1 as a standalone
positive check of the real manifest. It is not an additional required CI check.
Phase 4 introduces the canonical helper below as the single Layer A
positive/negative runner for CI and the demo.

The official schema requires `$schema` and `name`; it does not require
`version` or `description`. Layer A may access the pinned validator through
`uvx`, retrieve the canonical schema when uncached, and store that schema only
in a controlled temporary location. It may require network access to obtain
either resource. It may use the normal executable/dependency files in the
configured `uvx` cache but must not enumerate or inspect arbitrary home-directory
files. Layer A must not read secrets, credentials, AWS configuration, user-global
Codex configuration, or unrelated host files. There is no offline fallback that
reduces this check to required-key assertions.

### Layer B — Project policy and structural validation

`module-5/guardrails/validate_plugin_layout.py` will perform deterministic
project-specific metadata, filesystem, and marketplace checks without
reimplementing a JSON Schema engine. It will accept an optional `--repo-root`
for isolated temporary fixtures and otherwise resolve the repository root from
the validator location, so behavior does not depend on the caller's current
working directory. Layer B must confine every repository/fixture filesystem
read to that explicitly selected root and must reject resolved paths outside
it. It may not read secrets, credentials, AWS configuration, user-global Codex
configuration, or unrelated host files.

It will require a JSON-object manifest whose `name` is exactly
`taskflow-agent-pack`, with non-empty string `version` and `description`, and
whose identity agrees with `plugins/taskflow-agent-pack/`. It will require the
plugin directory, regular non-symlink root `plugin.json`, root `skills/`, and
regular `skills/taskflow-api-review/SKILL.md` at the supported
`skills/<skill-name>/SKILL.md` depth. Resolved paths and symlink traversal must
not escape the plugin root.

It will also validate `.agents/plugins/marketplace.json` as JSON with top-level
name `local-repo` and a `plugins` array; locate the intended plugin entry;
require `policy.installation`, `policy.authentication`, and `category`; and
resolve `source.path` as `./plugins/taskflow-agent-pack` from the repository/
marketplace root, not from `.agents/plugins/`. It must reject outside-repository
or differently resolving paths with useful nonzero diagnostics.

This validator is responsible for project policy, filesystem structure, and
marketplace consistency. It must not claim to perform Layer A schema validation.

### Layer C — Positive and negative tests

`module-5/guardrails/test_plugin_layout.py` will exercise the validator,
preferably with temporary repository fixtures. It will cover a valid layout;
missing root manifest, `skills/`, or `SKILL.md`; incorrect nesting; escaping
symlinks; mismatched identity; empty/missing `version` or `description`; and
incorrect or outside marketplace metadata. The explicit fixtures under
`module-5/tests/fixtures/plugin-manifests/` separate official schema negatives
from project-policy negatives.

The official schema negatives must use the actual pinned CLI and must verify the
expected validation reason, not merely observe a nonzero exit. The future
`module-5/guardrails/validate_official_plugin_schema.py` helper is the single
canonical Layer A positive/negative runner for CI and demo validation. Per
invocation it will first resolve and execute `check-jsonschema==0.38.2`,
retrieve the canonical schema URL into a controlled temporary file, fail
explicitly if retrieval or JSON parsing fails, and use that same schema file
for the real manifest and both malformed fixtures.

The helper will prefer a machine-readable diagnostic format from the pinned CLI
if that format is actually available and exposes the needed instance path and
validation keyword. Until that support is verified, it must use a bounded,
version-pinned compatibility strategy over combined stdout/stderr: the
missing-schema fixture must identify a required-property violation for
`$schema`, and the name-type fixture must identify a type violation at `name`
whose expected type is `string`. It must reject generic or unrelated output,
preserve stdout/stderr for diagnosis, and distinguish tool resolution,
network/retrieval, schema parsing, and validation failures. A CLI-output change
that prevents these checks must fail the helper and be recorded as a
compatibility limitation; it must never be treated as a successful negative
test or replaced with a key-presence assertion.

The planned CI command, using the locked Module 5 tooling environment, is:

```bash
uv run --project module-5 python module-5/guardrails/validate_official_plugin_schema.py
```

This helper is Layer A’s reproducible positive/negative runner; its use of the
published versioned schema remains the official JSON Schema check. The
missing-`version` and missing/empty-`description` cases remain Layer B project-
policy negatives and must not be described as official-schema failures.

## Architecture decisions

1. The reusable workflow is a read-only API-review procedure. It checks an
   OpenAPI change, compatibility, error/status behavior, and tests; it does not
   apply patches.
2. The specialized reviewer is an API reviewer configured with
   `sandbox_mode = "read-only"` and a small context/tool surface. Its
   instructions prohibit edits, deployment, AWS access, and production access.
   The instructions are not themselves enforcement: parent-session settings and
   explicit spawn/config overrides can affect effective permissions. The
   implementation must verify the effective mode before using it and must not
   claim shell invocation is disabled merely because the agent is read-only.
3. The MCP server exposes one narrowly scoped read-only contract tool. It uses a
   fixed TaskFlow source and an explicit endpoint/field allowlist. It has no
   arbitrary path argument, shell tool, write tool, credentials, or production
   connection.
4. Repo-local discovery is staged explicitly. In Phase 1,
   `.agents/plugins/marketplace.json` names the local marketplace and
   `.codex/config.toml` enables `taskflow-agent-pack@local-repo` only. In Phase
   3, after the MCP server and locked environment exist, the named local stdio
   server is appended to that existing config. Codex project trust is verified
   in a clean clone; no user-global configuration is edited.
5. CI is independent: `CI — Module 5` runs only Module 5 capability/guardrail
   validation and packaging checks. It does not call, chain from, or replace
   Module 3/4 deployment workflows.
6. CI negative tests are the effective guardrail; prompt instructions document
   intent but are not the security boundary.

## Independent CI and protected-path policy

The future `.github/workflows/ci-module-5.yml` will run on pull requests and
pushes affecting every Module 5 discovery or implementation path:

- `AGENTS.md`;
- `.agents/plugins/**`;
- `.codex/agents/**` and `.codex/config.toml`;
- `module-5/**`;
- `plugins/taskflow-agent-pack/**`; and
- `.github/workflows/ci-module-5.yml`.

It will have `contents: read`, no AWS permissions, no secrets, and no deployment steps.
It will run the official schema helper and project policy/filesystem/marketplace
checks in the locked `module-5` tooling project, then run MCP allowlist tests in
the independent locked `module-5/mcp` project. The workflow will also run positive
and negative plugin-layout tests and protected-path guardrail tests. Each project
environment must be synchronized with `uv sync --locked --project <path>` before
its commands run; CI must not depend on any developer machine's pre-existing
virtual environment.

The guardrail will reject a Module 5 change whose changed-file set includes:

- `.github/workflows/ci.yml` or `.github/workflows/deploy.yml`;
- any of the three existing Module 4 workflows;
- `module-3/infra/**`, `module-3/deploy/**`, or Module 3 production config;
- Module 4 deployment/infrastructure paths; or
- Module 3/4 application source, unless a future approved phase changes policy.

Negative tests will cover exact protected files, descendants, and unsafe path
normalization. The check must compare the base-to-head diff and handle a
missing parent commit deterministically.

## Clean-clone installation and verification plan

1. Clone the repository and check out the implementation branch.
2. Verify the expected commit and clean status.
3. Confirm `uv --version` is `0.12.23`, or record a compatibility decision.
4. Review `.agents/plugins/marketplace.json`, `plugins/taskflow-agent-pack/`,
   `.codex/config.toml`, and `.codex/agents/`.
5. Synchronize the validation/test environment with
   `uv sync --locked --project module-5`. This uses `module-5/pyproject.toml`
   and `module-5/uv.lock`, not an existing root or Module 3/4 environment.
   Generated project virtual environments must remain untracked/ignored.
6. Trust the repository/project in the Codex client if it requires trust for
   project `.codex/config.toml`; do not edit global Codex configuration. The
   client may maintain its normal plugin cache under the user home directory.
7. Verify `taskflow-agent-pack@local-repo` is enabled from repo-local config,
   the skill is discoverable, and the custom agent is discoverable. This check
   does not require an MCP registration before Phase 3.
8. Verify the effective custom-agent permission mode is read-only in the actual
   parent session; record inherited/overridden settings and do not proceed if
   the mode is broader than intended.
9. After Phase 3, synchronize the MCP environment from
   `module-5/mcp/pyproject.toml` and `module-5/mcp/uv.lock`, then verify that the
   server starts through the `.codex/config.toml` stdio registration and exposes
   only its documented tool.
10. Run plugin and protected-path checks through the `module-5` tooling project
    after its lockfile has been synchronized; run MCP-specific tests through the
    separate MCP project. Finish with `git diff --check` and `git diff --stat`.

No global package installation is required. The project dependencies are managed
by `uv` in project-local virtual environments from their lockfiles; `uvx` may
obtain the pinned CLI in its isolated cache, and schema retrieval may require
network access when uncached. The procedure must not edit global Codex
configuration or rely on pre-existing Module 3/4 virtual environments.

### Planned validation commands

Run these from the repository root after the implementation files exist:

```bash
uv sync --locked --project module-5
uv run --project module-5 python module-5/guardrails/validate_official_plugin_schema.py
uv run --project module-5 python module-5/guardrails/validate_plugin_layout.py
uv run --project module-5 pytest module-5/guardrails/test_plugin_layout.py -q
uv run --project module-5 pytest module-5/guardrails/test_protected_paths.py -q
# Set BASE_SHA and HEAD_SHA to the actual commit SHAs first.
uv run --project module-5 python module-5/guardrails/protected_paths.py --base "$BASE_SHA" --head "$HEAD_SHA"

# Phase 3 onward: the MCP server has its own locked project environment.
uv sync --locked --project module-5/mcp
uv run --project module-5/mcp pytest module-5/tests/test_mcp_allowlist.py -q
uv run --project module-5/mcp python module-5/mcp/taskflow_readonly_server.py --self-check

git diff --check
git diff --stat
```

All `module-5/guardrails` scripts and their pytest tests use the dedicated
`module-5` tooling project via `uv run --project module-5`. MCP-specific tests and
the server self-check use `uv run --project module-5/mcp`, whose dependencies and
lockfile are independent. Scripts are invoked by file path, not as
`python -m module_5...`; no importable `module_5` package is required. The MCP
command above is a server self-check; the acceptance demo must additionally
invoke the tool through the `.codex/config.toml` stdio registration.

## Phased implementation and gates

### Phase 1 — Skeleton and instructions

Add root instructions, marketplace, initial project config, plugin manifest,
and project-scoped agent. The Phase 1 `.codex/config.toml` contains only the
repo-local plugin enablement key; do not add the MCP server entry yet.

Gate: paths are correct, the repo-local marketplace points to the plugin, and
the portable root manifest contains the canonical `$schema` and official-schema
`name`. Run Layer A's standalone positive check against the real manifest.
The project policy requires non-empty string values for `name`, `version`, and
`description`. Layer B project-policy validation and Layer C positive/negative
tests are implemented and exercised in Phase 4 with the independent CI guardrail.
The plugin is enabled from repo-local config, and the agent has required fields
(`name`, `description`, `developer_instructions`) plus
`sandbox_mode = "read-only"`. Verify the effective mode rather than relying on
instructions alone.

### Phase 2 — Skill and portable package

Write and fixture-test the skill. Gate: it is invokable, repeatable,
tool-agnostic in its contract, produces review evidence without edits, and
plugin/skill discovery is validated separately from MCP.

### Phase 3 — Read-only MCP capability

Implement the fixed-source allowlisted server and its locked `pyproject.toml`/
`uv.lock`. Only after those files exist, add the MCP stdio registration to the
existing `.codex/config.toml`. Gate: the server is discoverable from a clean clone
through that registration; allowed queries work; unknown endpoint, file, write,
and shell-operation requests fail; no credentials or production network access
are needed. Plugin-layout policy tests and official-schema positive/negative checks
are implemented and run in Phase 4. Phase 3 focuses on the MCP server, its
allowlist tests, and invocation through the configured stdio registration.

### Phase 4 — CI guardrail and validation environments

Create `module-5/pyproject.toml` and generate `module-5/uv.lock` for
plugin/schema/layout validation and protected-path tests. Configure it as a
non-package tooling project (`package = false`), declare `pytest` as a
development dependency, set an explicit supported Python range, and lock the
resolved dependency set. Keep the MCP project at `module-5/mcp/` separate; its
`pyproject.toml` and `uv.lock` must define a compatible supported Python range,
include the MCP runtime dependencies, and declare `pytest` for
`module-5/tests/test_mcp_allowlist.py` as a development/test dependency. Configure
it as a non-package project (`package = false`) unless implementation deliberately
introduces a distributable Python package. Validate the Python range against the
course environment and record the interpreter used in clean-clone/CI evidence.

Implement the official-schema helper, project-policy/layout validator, positive
and negative tests, protected-path policy, and `CI — Module 5`. CI must run
`uv sync --locked --project module-5` before validation/guardrail commands and
`uv sync --locked --project module-5/mcp` before MCP tests. Gate: both project
environments reproduce from their lockfiles, the protected-path negative fixture
fails, the Module 5 positive fixture passes, all plugin schema/layout tests pass,
and the workflow has no deployment/AWS path. Never reuse or depend on the
developer's pre-existing root or Module 3/4 environments.

### Phase 5 — Isolated demo and evidence

Run the demo in a disposable worktree/branch, collect `docs/demo.md` evidence,
review the final diff, then discard the demo branch/worktree. Gate: every demo
step is observable and no demo-only change reaches `main`.

### Phase 6 — Final acceptance

Use `docs/acceptance.md` as the release gate. Any unverified client-version
behavior is recorded as a compatibility risk, not claimed as passing.

## Mandatory versus optional

Mandatory: the seven minimum capabilities, portable skill package plus separate
project agent, fixed allowlisted MCP tool, executable negative-test guardrail,
independent CI, clean-clone verification, isolated demo, permission note, and
final diff evidence.

Optional: a second skill, UI extension, signed plugin publication, remote MCP
deployment, richer schema analysis, or a custom agent loop. None may add
credentials, production access, or alter TaskFlow architecture.

## Compatibility risks and sources

Codex CLI `0.162.1` is the primary target, but plugin schema, custom-agent TOML,
MCP transport, hook trust, and local marketplace behavior can evolve. Verify the
installed client rather than assuming documentation is stable. The design uses
the [OpenAI plugin packaging guide](https://developers.openai.com/plugins/build/plugins),
the [Codex custom subagent guide](https://developers.openai.com/codex/subagents),
the [course Module 5 README](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/tree/main/05-agent-capabilities),
and its [FAQ](https://datatalksclub.github.io/faq/ai-dev-tools-zoomcamp.html#05-agent-capabilities).
