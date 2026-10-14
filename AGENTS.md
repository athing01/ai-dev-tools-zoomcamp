# Repository Instructions

## 1. Authority and Scope

- Follow the instructions in this file and all applicable instructions in
  subdirectories. Module-specific instructions and their authoritative product
  specifications remain relevant to work inside those modules.
- For Module 5 implementation, treat `module-5/implementation-plan.md` and
  `module-5/docs/acceptance.md` as the primary implementation plan and acceptance
  gate. The other Module 5 design, permissions, and demo documents provide
  supporting decisions.
- Implement only the current approved phase. Do not silently expand scope,
  change agreed architecture, skip acceptance gates, or implement deferred work
  early.
- If implementation evidence contradicts the plan, stop and report the evidence
  and proposed resolution before changing the agreed design.

## 2. Repository Map

- `module-2/`: earlier TaskFlow learning module and its local instructions.
- `module-3/`: TaskFlow application, API contract, tests, and infrastructure.
  Read `module-3/AGENTS.md` before work in this subtree.
- `module-4/`: TaskFlow operations, observability, incident response, and security
  work. Read `module-4/AGENTS.md` before work in this subtree.
- `module-5/`: Agent Extension Pack implementation plan, acceptance gates,
  validation tooling, MCP capability, security notes, and demo evidence.
- `plugins/taskflow-agent-pack/`: portable plugin package and reusable skills.
- `.agents/plugins/marketplace.json`: repository-local plugin marketplace.
- `.codex/config.toml`: repository-scoped Codex settings.
- `.codex/agents/`: project-scoped Codex custom agents.
- `.github/workflows/`: GitHub Actions workflows. Preserve existing module
  workflow boundaries.

Generated `.venv`, `node_modules`, caches, and other generated dependency
directories are not authoritative inventories of project capabilities.

## 3. Protected Module 3 and Module 4 Boundaries

Module 5 must not alter the existing Module 3/4 application behavior,
architecture, infrastructure, deployment paths, or production configuration.

Treat the following existing workflows as protected:
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`
- `.github/workflows/ci-module-4.yml`
- `.github/workflows/deploy-module-4.yml`
- `.github/workflows/promote-module-4.yml`

Do not edit Module 3/4 application source, infrastructure, deployment
configuration, or production settings as part of Module 5. Do not add AWS
permissions, credentials, secrets, production connections, or deployment
capabilities to the extension pack.

The future Module 5 CI workflow must remain independent of the Module 3/4
deployment workflows. Its exact path and permissions are governed by the
implementation plan.

## 4. Module 5 Phase Boundaries

- Phase 1 adds only the root instructions, repo-local marketplace, initial
  repo-scoped Codex plugin configuration, portable plugin manifest, and custom
  API-reviewer agent.
- Phase 2 owns the reusable skill implementation and its tests.
- Phase 3 owns the read-only MCP server, its separate locked environment, and
  the later MCP registration in `.codex/config.toml`.
- Phase 4 owns the validation project, schema/layout helpers, protected-path
  guardrail, tests, and independent CI workflow.
- Phase 5 owns the disposable demo and its evidence.
- Phase 6 owns final acceptance against `module-5/docs/acceptance.md`.

During Phase 1, `.codex/config.toml` must contain only the repo-local plugin
enablement specified in the plan. Do not register an MCP server before Phase 3
and before its server project and lockfile exist. Do not create Phase 2–6
implementation files early.

The portable manifest belongs at
`plugins/taskflow-agent-pack/plugin.json`. Keep portable metadata free from
machine-specific paths and credentials. The official schema requires `$schema`
and `name`. Project policy separately requires non-empty string values for
`name`, `version`, and `description`.

## 5. Permissions and Security

The API reviewer requests `sandbox_mode = "read-only"`. Its instructions and
configuration are not by themselves proof of the effective permissions.
Verify the effective mode in the real parent session before using the reviewer
for acceptance or demo work. Do not assume read-only mode disables shell
invocation or outbound network access.

Never work around project-discovery or trust issues by editing user-global
Codex configuration. Verify repository trust through the intended client flow.
Distinguish policy restrictions from technically enforced controls, and do not
claim network isolation unless the effective sandbox/network policy has been
verified.

The extension pack is advisory API-review tooling, not deployment authorization.
Do not access AWS, secrets, production services, or unrelated host files. Avoid
destructive commands and do not make application changes while performing a
read-only review.

## 6. Tooling and Validation

Use the pinned course tooling. The planned validation environment uses
`uv 0.12.23`; record any verified compatibility exception rather than silently
changing versions.

For Phase 1:
- Parse all JSON and TOML files with the appropriate parser.
- Validate the real portable manifest with the pinned official
  `check-jsonschema==0.38.2` command and the canonical versioned schema.
- Test repo-local plugin and custom-agent discovery in the actual Codex client.
- Verify the effective read-only permission mode; do not infer it from the
  TOML setting alone.
- Run `git diff --check` and inspect the final diff.

Do not install project dependencies or create Python environments in Phase 1.
The official schema check may use `uvx` and require network access when the
validator or canonical schema is not cached. Report failures and limitations
accurately; never report an unexecuted check as passed.

For every phase, prefer focused checks first. Review changes for secrets,
unintended files, protected Module 3/4 modifications, and scope creep. Record
the actual commands and results supporting each acceptance decision.
