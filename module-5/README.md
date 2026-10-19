# Module 5 — Agent Extension Pack

Module 5 adds a repository-scoped Codex extension pack for **read-only TaskFlow API contract review**. It packages a reusable Skill, a specialized API-reviewer subagent, a narrowly allowlisted MCP contract-inspection server, and independent validation/CI guardrails.

The extension is advisory review tooling. It does not authorize application changes, deployment, infrastructure operations, or production access. Module 3 and Module 4 application behavior, infrastructure, and existing workflows remain protected.

## What is included

- **Portable plugin** — `plugins/taskflow-agent-pack/plugin.json` defines `taskflow-agent-pack` and packages the reusable `taskflow-api-review` Skill.
- **Repository-local marketplace** — `.agents/plugins/marketplace.json` registers the local plugin source under `local-repo`.
- **Custom API reviewer** — `.codex/agents/taskflow-api-reviewer.toml` describes a specialized reviewer with a requested `read-only` sandbox mode. Effective permissions must be checked in the actual Codex session; the TOML setting alone is not enforcement evidence.
- **Read-only MCP contract tool** — `module-5/mcp/taskflow_readonly_server.py` reads the fixed Module 3 OpenAPI contract and exposes allowlisted contract queries. It is not a general filesystem, shell, database, AWS, or HTTP client.
- **Validation and guardrails** — `module-5/guardrails/` contains official-schema validation, project layout/policy validation, protected-path checks, and tests.
- **Independent CI** — `.github/workflows/ci-module-5.yml` validates Module 5 separately from the protected Module 3/4 workflows.

## Module 5 requirements mapping

The table maps the course's seven minimum requirements to their implementation and recorded verification evidence.

| Minimum requirement | Implementation | Verification evidence |
|---|---|---|
| Project instructions | `AGENTS.md` | Instructions and repository boundaries recorded in the demo and acceptance documentation |
| Reusable workflow, skill, or command | `plugins/taskflow-agent-pack/skills/taskflow-api-review/SKILL.md` | Skill invocation recorded during clean-clone validation after explicit marketplace registration and plugin installation |
| Specialized subagent | `.codex/agents/taskflow-api-reviewer.toml` | Recorded child session and effective read-only permission evidence in `module-5/docs/acceptance.md` |
| MCP tool or server | `module-5/mcp/taskflow_readonly_server.py` | Allowed and rejected requests, MCP tests, and server self-check |
| Hook or guardrail | `module-5/guardrails/` | Positive and negative tests, including protected-path rejection |
| Plugin or extension package, or custom agent | `plugins/taskflow-agent-pack/plugin.json` and `.agents/plugins/marketplace.json` | Official-schema and layout validation; successful plugin use after explicit marketplace registration and installation |
| Permission/security note | `module-5/docs/permissions.md` | Capability, data-access, and approval-boundary documentation |

The extension also includes independent CI in `.github/workflows/ci-module-5.yml` and a disposable workflow demonstration documented in `module-5/docs/demo.md`.

**Discovery and permission limitations:** The recorded clean-clone test does not establish automatic marketplace discovery without registration. Read-only mode is not claimed to disable shell execution, and a failed DNS probe alone is not proof of the cause of network denial. See `module-5/docs/acceptance.md` and `module-5/docs/permissions.md` for the recorded evidence and limitations.

## Repository map

The tree below highlights the repository paths relevant to Module 5 and is relative to the repository root. Unrelated modules and existing workflow files are omitted. Module 5 files live under `module-5/`; the plugin, Codex configuration, and Module 5 CI workflow are at the repository level.

```text
ai-dev-tools-zoomcamp/
├── AGENTS.md
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── .codex/
│   ├── agents/
│   │   └── taskflow-api-reviewer.toml
│   └── config.toml
├── .github/
│   └── workflows/
│       └── ci-module-5.yml
├── plugins/
│   └── taskflow-agent-pack/
│       ├── plugin.json
│       └── skills/
│           └── taskflow-api-review/
│               └── SKILL.md
└── module-5/
    ├── README.md
    ├── implementation-plan.md
    ├── docs/
    │   ├── acceptance.md
    │   ├── agent-extension-pack.md
    │   ├── permissions.md
    │   └── demo.md
    ├── guardrails/
    │   ├── validate_official_plugin_schema.py
    │   ├── validate_plugin_layout.py
    │   ├── protected_paths.py
    │   ├── test_plugin_layout.py
    │   └── test_protected_paths.py
    ├── mcp/
    │   ├── README.md
    │   ├── pyproject.toml
    │   ├── taskflow_readonly_server.py
    │   └── uv.lock
    ├── tests/
    │   ├── fixtures/
    │   │   └── plugin-manifests/
    │   │       ├── schema-invalid-missing-schema.json
    │   │       └── schema-invalid-name-type.json
    │   └── test_mcp_allowlist.py
    ├── pyproject.toml
    └── uv.lock
```

## Quick validation

Use the pinned course toolchain (`uv 0.12.23`). Run these commands from the repository root.

```bash
uv --version

# Set up the isolated validation/guardrail environment.
uv sync --locked --project module-5

# Layer A: official portable plugin JSON Schema validation.
uv run --locked --project module-5 \
  python module-5/guardrails/validate_official_plugin_schema.py

# Layer B: repository layout and project policy.
uv run --locked --project module-5 \
  python module-5/guardrails/validate_plugin_layout.py

# Layer C: positive and negative guardrail cases.
uv run --locked --project module-5 \
  pytest module-5/guardrails/test_plugin_layout.py -q
uv run --locked --project module-5 \
  pytest module-5/guardrails/test_protected_paths.py -q

# The MCP server has its own locked environment.
uv sync --locked --project module-5/mcp
uv run --locked --project module-5/mcp \
  pytest module-5/tests/test_mcp_allowlist.py -q
uv run --locked --project module-5/mcp \
  python module-5/mcp/taskflow_readonly_server.py --self-check
```

The official schema validator may need network access when its pinned tool or canonical schema is not cached. Its helper uses explicit manifest/schema inputs; it does not inspect user-global Codex settings, AWS configuration, credentials, or secrets. The MCP server is synchronized separately so its dependencies do not pollute the validation project.

The same validation layers are wired into `CI — Module 5`. Consult the latest workflow result and `docs/acceptance.md` for recorded command output and detailed acceptance evidence.

## Enabling the plugin in Codex

The repository configuration enables `taskflow-agent-pack@local-repo`; the MCP registration is added in Phase 3 after the MCP project and lockfile exist.

Codex client discovery and trust behavior is environment-dependent. In the recorded clean-clone validation, the client prompted for project trust; trust was accepted, after which plugin use succeeded. The marketplace was explicitly registered and the plugin installed in a temporary `CODEX_HOME` before Skill invocation, using the equivalent of:

```bash
codex plugin marketplace add "$PWD"
codex plugin add taskflow-agent-pack@local-repo
codex plugin list --marketplace local-repo
```

This demonstrates successful use after explicit registration and installation. **It does not prove automatic discovery by a Codex Home where the marketplace has not been registered.** The test used a temporary Codex home; avoid editing global Codex configuration just to work around project discovery or trust behavior.

## Security and permission boundaries

- The API reviewer is intended for review-only work: contract changes, compatibility risks, HTTP/schema/error behavior, repository implications, and missing tests.
- The reviewer’s TOML requests `sandbox_mode = "read-only"`. In the recorded child session, the effective managed permission profile reported a restricted filesystem and `network = restricted`; `test -w .` returned `no`. Shell execution remained available, so this project does **not** claim that read-only mode disables shell invocation.
- A single non-production `HEAD` request to `https://example.com` failed with a DNS resolution error (`curl` exit code `6`, HTTP status `000`). That result is consistent with the recorded network restriction, but the error alone does not prove its cause or establish destination-specific behavior. No production endpoint was contacted.
- The MCP server accepts only its documented allowlisted contract queries against the fixed OpenAPI source. Invalid queries and out-of-scope paths are rejected. It does not expose shell, write, database, or AWS tools.
- CI is independent of deployment, has `contents: read`, and contains no AWS/OIDC credentials or deploy step. Do not add production access, secrets, credentials, or deployment capabilities to the extension pack.

For the detailed capability/data/approval matrix, read [`docs/permissions.md`](docs/permissions.md). Read [`docs/acceptance.md`](docs/acceptance.md) for the gates and evidence, and [`docs/demo.md`](docs/demo.md) for demo scope and limitations.

## Demo scope

The TaskFlow `GET /api/tasks/count` example was used only as a disposable Module 5 workflow demonstration in a temporary worktree. The demo change was not merged to the primary branch and is not part of the Module 3 product behavior. Its implementation, review, test results, cleanup, and remaining limits are recorded in [`docs/demo.md`](docs/demo.md).

## Further reading

- [`implementation-plan.md`](implementation-plan.md) — phase plan and decisions.
- [`docs/agent-extension-pack.md`](docs/agent-extension-pack.md) — extension package design.
- [`docs/acceptance.md`](docs/acceptance.md) — acceptance gates and verification evidence.
- [`docs/permissions.md`](docs/permissions.md) — capabilities, data exposure, and approval boundaries.
- [`docs/demo.md`](docs/demo.md) — disposable demo and execution record.
