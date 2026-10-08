# Module 4 P6-A — Security Audit Inventory

## 1. Purpose

This inventory establishes the concrete TaskFlow Module 4 security-review surface before scanner execution, model-assisted review, and human disposition.

The inventory is based on the verified `ai-dev-tools-zoomcamp` repository at immutable commit:

```text
repository = git@github.com:athing01/ai-dev-tools-zoomcamp.git
audit_commit = fba6a3945b0b59069580a2e2df6423f2503eb7eb
branch = main
HEAD = fba6a3945b0b59069580a2e2df6423f2503eb7eb
origin/main = fba6a3945b0b59069580a2e2df6423f2503eb7eb
working tree = clean
```

The P6 repository reference bundle records exact paths and SHA-256 values derived from this Git commit. The Git repository and immutable commit above are the canonical P6-A source reference.

## 2. Inventory Status Legend

| Status | Meaning |
|---|---|
| Observed | Control or implementation is visible in the supplied source |
| Evidence needed | Source suggests a control, but runtime/scanner/repository evidence is still required |
| Audit focus | Deliberately selected for security review; not a finding |
| Out of scope | Excluded by the P6-A boundary |

A source-level observation is not a confirmed security finding. Findings require provenance, review status, and human disposition.

### Repository source identity vs. P5 runtime release identity

The P6-A source/audit baseline is `fba6a3945b0b59069580a2e2df6423f2503eb7eb`. The material P5 incident artifacts record `release_sha = cfc5189ffe74e63510b5f041bf38e9b933c5ea9a` for the DEV runtime observed during that incident. These identities must not be conflated: the repository commit identifies the source under audit, while the incident release SHA identifies the deployed runtime associated with the incident evidence.

## 3. TaskFlow Application and Operational Surface

| Area | Primary paths | Observed control / boundary | Audit status |
|---|---|---|---|
| Backend application | `module-4/backend/` | M4 application implementation and tests | Observed; scanner review required |
| Frontend application | `module-4/frontend/` | M4 frontend implementation and tests | Observed; scanner review required |
| M4 release/deploy runtime | `module-4/deploy/`, `module-4/infra/` | Release manifests, EC2 runtime, deployment engine, environment configuration | Observed; credential/IAM review required |
| Observability | `module-4/observability/` | Metrics, traces, logs, dashboard, alert configuration | Observed; evidence/data-minimization review required |
| M4 DEV infrastructure | `module-4/infra/cloudformation/m4-dev.yaml` | Dedicated EC2 role, ECR, SSM parameter access, release artifacts, logging | Observed; IAM least-privilege evidence required |

## 4. Evidence Collection Surface

| Path | Observed behavior | Audit focus |
|---|---|---|
| `module-4/incident-response/collect-evidence.sh` | Read-only bounded collection from application/metrics/logs/traces | Query scope, time bounds, output minimization, command injection/path safety, secret handling |
| `module-4/incident-response/incidents/*/evidence.json` | Retained evidence packet with source statuses and safety metadata | Retention, provenance, data minimization, integrity |
| P5 final evidence | `incidents/p5-taskflow-final-20261006-053711/evidence.json` | Canonical material incident evidence | Evidence reconstruction and provenance |

Observed P5 evidence declares:

```text
arbitrary_commands = false
arbitrary_queries = false
full_application_response_retained = false
full_trace_payload_retained = false
production_access = false
secrets_included = false
```

These are implementation assertions that require audit evidence; they are not accepted as independent proof by themselves.

## 5. Responder Task and Adapter Boundary

| Path | Observed control | Audit focus |
|---|---|---|
| `module-4/incident-response/responder-task.md` | Explicit proposal-not-authority role; input limited to collector packet; no command/credential output | Prompt injection resistance, instruction/data separation, scope enforcement, output constraints |
| `module-4/incident-response/responder.py` | Fixed incident scope, bounded input/output sizes, schema validation, semantic action checks | Parser robustness, boundary bypass, network destination control, secret handling, failure behavior |
| OpenAI-compatible adapter in `responder.py` | `RESPONDER_BASE_URL`, `RESPONDER_MODEL`, `RESPONDER_PROVIDER`; API key from `RESPONDER_API_KEY` | Credential exposure, endpoint trust, model/configuration provenance, SSRF-style destination abuse |
| `module-4/incident-response/response.schema.json` | Structured output contract; provenance excludes credentials/secrets | Schema completeness, additional-field handling, dangerous data propagation |

## 6. Autonomy Policy and Bounded Action Surface

| Path | Observed control | Audit focus |
|---|---|---|
| `module-4/incident-response/autonomy-policy.yaml` | Deny-by-default; one allowlisted action; DEV-only scope; human authorization required | Policy completeness, bypass paths, environment separation, effect minimization |
| `module-4/incident-response/policy-gate.py` | Authorization metadata validation and policy boundary enforcement | Authorization parsing, replay/expiry checks, action/environment mismatch handling |
| `module-4/incident-response/runbooks/recover-task-list-dev-fault.sh` | Fixed executor; immediate precondition revalidation; backend-only recreation; image/runtime preservation checks | Command construction, Docker capability, TOCTOU assumptions, filesystem permissions, secret leakage |
| `module-4/incident-response/runbooks/verify-recovery.sh` | Independent current-state verification | Independence from executor, verification integrity, escalation semantics |
| `module-4/incident-response/runbooks/rollback.sh` | Separate manual rollback path; not in AI action allowlist | Boundary separation, authorization handling, immutable artifact use |

## 7. Credential and Infrastructure Boundary

| Surface | Observed implementation | Audit focus |
|---|---|---|
| GitHub Actions AWS access | M4 CI/deploy/promote workflows use GitHub OIDC with `id-token: write` | Role trust, environment protection, permission scope, workflow trigger abuse |
| M4 DEV deploy role | `taskflow-m4-dev-deploy` referenced by deploy workflow | Least privilege and DEV-only access |
| M4 PROD promotion role | `taskflow-m4-prod-promote` referenced by manual promotion workflow | Production boundary, environment approval, role trust |
| M4 DEV EC2 role | `taskflow-m4-dev-ec2-role` | SSM/ECR/S3/KMS/log permissions and least privilege |
| Responder credential | `RESPONDER_API_KEY` supplied via environment | Secret storage/injection path and exposure surface |
| Responder endpoint | `RESPONDER_BASE_URL` supplied via environment | Allowed destination / endpoint trust |

### Specific source-level attention area

The M4 DEV EC2 role includes a wildcard resource for `kms:Decrypt` while constraining the service via `kms:ViaService` to SSM. The audit must verify whether this is an accepted least-privilege boundary or a material over-permission.

This is an **audit question, not a confirmed finding**.

## 8. GitHub Workflow Surface

| Workflow | Observed purpose | Audit focus |
|---|---|---|
| `.github/workflows/ci-module-4.yml` | M4 CI, integration/F2B tests, image build/publish, release manifest | Supply-chain permissions, AWS role scope, untrusted PR input handling |
| `.github/workflows/deploy-module-4.yml` | Automatic DEV deployment after successful main CI | `workflow_run` trust boundary, exact-SHA checkout, OIDC role, SSM command construction |
| `.github/workflows/promote-module-4.yml` | Manual DEV→PROD promotion | Environment approval, input validation, artifact provenance, OIDC production role |
| `.github/workflows/ci.yml` | M3 CI | **Protected / do not modify**; verify unchanged |
| `.github/workflows/deploy.yml` | M3 deployment | **Protected / do not modify**; verify unchanged |

## 9. P5 Material Incident Evidence

Canonical incident:

```text
incident_id = p5-taskflow-final-20261006-053711
operation   = tasks.list
environment = dev
alert_uid   = taskflow-p4-tasks-list-failure
```

Observed release lineage recorded in the canonical incident evidence:

```text
release_sha = cfc5189ffe74e63510b5f041bf38e9b933c5ea9a
```

P5 response outcome recorded in the supplied artifacts:

```text
proposed_action     = null
action_authorized   = false
execution_permitted = false
mutation_performed  = false
recovery            = verified
```

The independent verification returned HTTP 200 with a JSON array. This inventory does not interpret that result as evidence that the responder performed recovery.

## 10. Missing P6-A Artifacts at Inventory Start

The supplied P5 snapshots do not yet contain the final P6-A deliverables:

```text
module-4/security-audit/audit-brief.md
module-4/security-audit/findings.schema.json
module-4/security-audit/capability-table.md
module-4/security-audit/runs/
module-4/docs/operations-and-security-report.md
module-4/docs/homework-4-evidence.md
module-4/docs/acceptance-traceability-matrix.md
```

This is the expected starting state for P6-A finalization, subject to repository state verification after the P6 branch is created.

## 11. Audit Evidence Still Required

1. Semgrep result covering the defined TaskFlow/M4 source scope.
2. Snyk Agent Scan evidence covering the responder attack surface.
3. Model-assisted review record with explicit provenance and bounded inputs.
4. Human validation/disposition for every reported finding, including explicit treatment of false positives and accepted risks.
5. Capability/credential boundary evidence.
6. Final acceptance traceability linking P3/P4/P5 behavior to implementation and evidence.
7. Verification that M3 protected workflows remain unchanged.
