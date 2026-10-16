# Module 5 Acceptance Gates

This is the implementation-phase acceptance checklist. It is a plan, not a
test report; no checks are claimed to have passed in P1.

## Gate 0 — Planning and baseline

- [ ] Branch, HEAD, and working-tree status were verified.
- [ ] `module-3/AGENTS.md` and `module-4/AGENTS.md` were read.
- [ ] All five existing workflows and the current repository layout were
      inspected from the checkout.
- [ ] No existing file was edited by P1.
- [ ] Exactly the five requested planning Markdown files exist as P1 outputs.

## Gate 1 — Minimum capability traceability

- [ ] Root `AGENTS.md` exists and contains accurate project instructions.
- [ ] `.agents/plugins/marketplace.json` points to the repo-local
      `./plugins/taskflow-agent-pack` source with marketplace name `local-repo`.
- [ ] Phase 1 `.codex/config.toml` enables `taskflow-agent-pack@local-repo`
      through repo-local configuration only; it does not register MCP yet.
- [ ] `.codex/agents/**`, `.codex/config.toml`, `.agents/plugins/**`,
      `plugins/taskflow-agent-pack/**`, `AGENTS.md`, `module-5/**`, and
      `.github/workflows/ci-module-5.yml` are included in CI path filters.
- [ ] Portable root `plugin.json` uses the canonical `$schema` URL and passes
      official portable-schema validation, which requires `$schema` and `name`.
      Separately, Layer B project policy requires non-empty string `name`,
      `version`, and `description` values.
- [ ] Marketplace entry includes required `policy` and `category` metadata and
      points to the portable plugin directory.
- [ ] `validate_plugin_layout.py` passes the valid filesystem, project-policy,
      and marketplace structure.
- [ ] Portable plugin manifest packages one reusable skill.
- [ ] Skill can be invoked and produces a repeatable API-review result.
- [ ] `.codex/agents/taskflow-api-reviewer.toml` is discovered with
      `sandbox_mode = "read-only"`.
- [ ] The effective subagent permission mode is verified in the real parent
      session, including inherited/overridden settings; instructions alone are
      not treated as enforcement.
- [ ] Reviewer performs a specialized API review with file evidence.
- [ ] Phase 3 adds the `taskflow_readonly` stdio registration to the existing
      `.codex/config.toml` only after the locked `module-5/mcp` project exists.
- [ ] MCP server exposes the intended allowlisted read-only tool through that
      Phase 3 registration, and valid/invalid MCP calls are checked.
- [ ] `CI — Module 5` is independent and has no AWS/OIDC/secrets/deploy step.
- [ ] Protected-path negative test fails and Module 5-only positive test passes.
- [ ] Permissions note maps capabilities, data, and approval boundaries.

Phase ownership for the mandatory checks:

- [ ] Phase 1 runs the standalone pinned `check-jsonschema` command documented
      in `implementation-plan.md` against the real portable manifest as a
      positive check. This phase does not yet run the canonical helper or the
      schema-negative fixtures.
- [ ] Phase 1 validates repo-local plugin enablement, plugin discovery,
      custom-agent discovery, and effective read-only mode.
- [ ] Phase 2 validates reusable skill discovery and invocation.
- [ ] Phase 3 validates the locked MCP environment, adds the stdio registration,
      and verifies invocation through Codex and the repository configuration.
- [ ] Phase 4 runs `module-5/guardrails/validate_official_plugin_schema.py`
      against the real manifest and both
      `schema-invalid-missing-schema.json` and
      `schema-invalid-name-type.json`. It fails if the pinned CLI cannot be
      executed, the canonical schema cannot be retrieved/parsed, either
      malformed fixture passes, or output lacks the expected missing-`$schema`
      or non-string-`name` violation. This helper is the single required CI
      Layer A positive/negative check and uses one retrieved schema per run.
- [ ] Phase 4 creates `module-5/pyproject.toml` and `module-5/uv.lock` as a
      non-package tooling project with `pytest` declared and locked for plugin,
      schema, layout, and protected-path checks.
- [ ] Phase 4 synchronizes the validation/test project with
      `uv sync --locked --project module-5`, then runs Layer A, Layer B, plugin-
      layout tests, and protected-path tests from that environment.
- [ ] Phase 4 synchronizes the separate MCP project with
      `uv sync --locked --project module-5/mcp`, then runs
      `module-5/tests/test_mcp_allowlist.py` with that environment. The MCP
      project declares and locks both its server dependencies and test dependency.
- [ ] Phase 4 runs all positive and negative `test_plugin_layout.py` cases,
      including missing/empty `version` and `description` project-policy cases.

## Gate 2 — Clean-clone reproducibility

- [ ] Clean clone validates manifest and skill through the repo-local marketplace
      and Phase 1 `.codex/config.toml`, without global Codex changes.
- [ ] If project trust is required, it is verified in the Codex client without
      editing global Codex configuration. The client may maintain its normal
      plugin cache under the user home directory.
- [ ] Documented `uv 0.12.23` workflow is reproducible or exception recorded.
- [ ] `module-5/pyproject.toml` and `module-5/uv.lock` define a separate,
      reproducible validation/guardrail-test environment with `pytest` locked.
- [ ] `module-5/mcp/pyproject.toml` and `module-5/mcp/uv.lock` define the
      independent MCP server/test environment as a non-package project unless a
      distributable package is deliberately introduced; it locks MCP dependencies
      and the test dependency without polluting the plugin/layout validator project.
- [ ] Both projects declare compatible supported Python ranges; clean-clone/CI
      evidence records the interpreter used.
- [ ] A clean clone can run `uv sync --locked --project module-5` and all
      validation/guardrail commands without relying on pre-existing virtual
      environments. After Phase 3, the MCP project can likewise sync from its
      own lockfile and run the MCP allowlist test/self-check.
- [ ] `uvx` network requirements for the pinned validator/schema are documented;
      no offline required-key fallback is used. No global package installation
      is required; `uvx` may populate its isolated cache and schema retrieval
      may require network access when uncached.
- [ ] Plugin and custom-agent paths are repository-scoped and portable.
- [ ] Layer A uses its controlled temporary schema location plus its explicitly
      named manifest/fixture inputs; Layer B is confined to the selected
      repository/fixture root, and Layer C uses only explicit test fixtures.
- [ ] No validator inspects secrets, credentials, AWS configuration, user-global
      Codex configuration, or unrelated host files. Package-manager reads of its
      own executable/dependency cache are separate from validator input access.
- [ ] No credentials, secrets, production URLs, or AWS permissions are needed.

## Gate 3 — Isolated TaskFlow demo (execution results)

The temporary `GET /api/tasks/count` feature was implemented and reviewed
only in the disposable worktree. It remains outside the approved Module 3
product scope. This is a deliberate exception for Module 5 workflow testing;
it does not authorize merging or deploying the feature.

- [x] Demo worktree identity, baseline commit, and clean initial status verified.
- [x] Root instructions, Module 3 instructions, product specification, and
      relevant API/repository/test sources read.
- [x] Installed plugin Skill invoked in an isolated temporary Codex Home.
- [x] Specialized API reviewer invoked before and after implementation.
- [x] Configured MCP stdio integration returned an allowed response and rejected
      an invalid query.
- [x] Static plugin validation and real Codex discovery were checked separately.
- [x] Plugin-layout, protected-path, and MCP allowlist suites passed.
- [x] Focused endpoint tests passed: 2 passed.
- [x] Complete Module 3 backend test suite passed: 79 passed, 2 deprecation
      warnings, using `uv run --locked pytest -q`.
- [x] Runtime OpenAPI generation validation passed.
- [x] `git diff --check` passed; the implementation changes are confined to the
      10 intended Module 3 demo files.
- [x] Primary worktree remained clean during demo verification.
- [x] Project owner approved the final documentation diff on 2026-10-16.
- [x] Demo worktree removed, local demo branch deleted, and cleanup verified.
      The diff was archived before cleanup at `/tmp/m5-taskflow-api-count-demo.patch`
      (SHA-256 recorded in `module-5/docs/demo.md`).

The initial Codex session encountered hanging API tests. Subsequent WSL terminal
runs passed both focused endpoint tests and the complete backend suite, so the
earlier HTTP-test concern did not reproduce in the terminal run. No dependency
pin or lockfile changes were made to work around that session issue.

The SQLAlchemy repository tests use their own test setup and passed as part of
the backend suite. However, the PostgreSQL integration assertion added in
`module-3/tests/integration/test_crud.py` was not run against PostgreSQL because
`TEST_DATABASE_URL` was unset. Do not claim PostgreSQL integration verification.

Runtime plugin installation and Skill invocation required explicit local
marketplace registration and installation in a temporary `CODEX_HOME`.
Automatic discovery by an otherwise unregistered Codex Home remains unverified.

## Gate 4 — Regression and security review

- [ ] Existing Module 3 and Module 4 workflows are byte-for-byte unchanged.
- [ ] Module 3/4 infrastructure, deployment, application, and production
      configuration are unchanged.
- [ ] TaskFlow product behavior and architecture are unchanged on primary.
- [ ] No MCP request can perform arbitrary reads, shell execution, writes,
      database access, or production network access.
- [ ] No claim is made that the subagent cannot invoke a shell unless the
      selected client configuration demonstrably enforces that; the verified
      control is effective read-only behavior and no deployment/access.
- [ ] Any claim that production network access is technically blocked is
      backed by verification of the effective sandbox/network policy in the
      target WSL2 environment; otherwise, it is documented as a policy boundary,
      not an enforced control.
- [ ] Guardrail tests cover exact paths, descendants, traversal, and normal
      Module 5 changes.
- [ ] Missing/empty `version` and `description` are rejected by project policy,
      without attributing those failures to the official schema.
- [ ] Final diff contains only intended Module 5 files; generated dependency
      directories are excluded.

## Mandatory versus optional outcome

All unchecked mandatory items block acceptance. Optional improvements such as a
second skill, UI extension, remote MCP deployment, plugin publication, or custom
autonomous loop are outside the gate and cannot compensate for a missing
minimum capability.

## Evidence package

The final handoff should link or attach clean-clone output, plugin and agent
discovery output, skill and reviewer output, allowed/rejected MCP calls,
positive/negative guardrail output, independent CI result, and final diff review
with proof that the demo-only branch/worktree was discarded.
