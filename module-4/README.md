# Module 4 — DevOps and Observability for TaskFlow

Module 4 extends TaskFlow with the minimum operational capabilities needed to safely release changes, observe user-impacting failures, investigate incidents with bounded evidence, authorize limited responses, verify recovery, and retain an auditable operational and security trail.

Module 4 supports the operational loop:

> **Change → observe user impact → alert with context → investigate from evidence → authorize a bounded response or escalate → verify recovery → audit the code and response trail**

## Module 4 Scope

Module 4 is organized around four implementation phases:

### Phase 3 — Release Behavior and Operational Identity

- Automatically make qualifying changes available in DEV.
- Keep PROD as a manually promoted, user-facing environment.
- Promote the same already-built immutable release artifact from DEV to PROD rather than rebuilding source.
- Preserve release identity so deployed versions remain traceable during operations and incident investigation.

### Phase 4 — Observability, Dashboard, and User-Impact Alert

- Provide end-to-end observability for one important TaskFlow backend endpoint or user-relevant operation.
- Emit metrics, traces, and structured logs.
- Correlate telemetry with the application/service, environment, and deployed release.
- Provide a dashboard showing health or user-impacting behavior.
- Detect a real user-impacting application failure with an actionable alert.

### Phase 5 — TaskFlow Incident Response

The incident-response path is intentionally bounded:

```text
Alert
→ bounded read-only evidence
→ structured AI assessment
→ external authorization
→ bounded action or escalation
→ independent recovery verification
```

The TaskFlow P5 scenario is based on the existing P4 `tasks.list` user-impact alert:

```text
GET /api/tasks
operation = tasks.list
environment = DEV
```

The responder is a proposal/analysis component, not an authority source. It receives bounded evidence, produces structured output, and cannot directly authorize or execute arbitrary commands. Only explicitly permitted and externally authorized actions may execute; otherwise the incident is escalated. Recovery is verified independently from the action attempt.

### Phase 6 — Finalization

Phase 6 contains two separate workstreams:

```text
P6-A  TaskFlow security audit + final acceptance
P6-B  Homework 4 / order-tracker execution
```

P6-A covers Semgrep, Snyk Agent Scan, model-assisted review, human validation and disposition, responder capability and credential boundaries, finding provenance, and final TaskFlow operational/security traceability.

P6-B is a separate Homework 4 exercise against the [`order-tracker` repository](https://github.com/athing01/order-tracker). Homework 4 evidence is owned by that repository; the TaskFlow repository keeps only a reference/index and does not add order-tracker-specific runtime behavior.

## Deployed Environments

TaskFlow Module 4 uses separate DEV and PROD deployment
environments.

- **DEV** receives qualifying changes pushed to `main`
  after successful Module 4 CI validation.
- **PROD** requires explicit manual promotion of an existing
  immutable release artifact that has been deployed to DEV.

| Environment | Frontend | API Documentation |
|---|---|---|
| DEV | [TaskFlow DEV](https://dev-app.zctaskflow.athing.cc/) | [API Docs](https://dev-api.zctaskflow.athing.cc/docs) |
| PROD | [TaskFlow PROD](https://app.zctaskflow.athing.cc/) | [API Docs](https://api.zctaskflow.athing.cc/docs) |

The frontend and API documentation endpoints in both
environments returned HTTP 200 when checked on
November 3, 2026.

### Verified Release — November 3, 2026

The current M4 release was built once, deployed to DEV, and
then promoted to PROD using the same immutable image digests.

```text
release_sha = 07273bb6931673fc8b4b8c64e2eff7967e86a6cc
```

| Stage | Workflow run | Result |
|---|---|---|
| M4 CI and immutable image build | [CI #36](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41619409483) | Success |
| M4 DEV deployment | [DEV #34](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41619655181) | Success |
| Manual M4 PROD promotion | [PROD #2](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41623688998) | Success |

The immutable ECR image digests recorded in the release manifest
and verified in both environment release-state records are:

| Image | SHA-256 digest |
|---|---|
| Backend | `sha256:f65fd38aa0f9194e95fca60998f798d8862f16308daec64d767eacab9ac1a589` |
| Frontend | `sha256:f82f381968a4f21c357988e92f4b755a62b30f31c416f7375c3422f67a6c93ad` |

The PROD workflow promoted the existing release artifact from
DEV; it did not rebuild the application images. Both DEV and
PROD release-state checks matched the requested Git SHA and
exact image digests. Frontend and Tasks API smoke tests passed
in both environments.

The workflow runs above provide point-in-time deployment and
smoke-test evidence; they are not a continuous availability
guarantee.

For deployment history and operational evidence, see:
- [DEV deployment workflow](../.github/workflows/deploy-module-4.yml)
- [PROD promotion workflow](../.github/workflows/promote-module-4.yml)
- [Module 4 implementation plan](implementation-plan.md)
- [Operations and Security Report](docs/operations-and-security-report.md)
- [Acceptance Traceability Matrix](docs/acceptance-traceability-matrix.md)

## Module 3 Boundary

Module 4 builds on the completed Module 3 application baseline.

Module 3 course acceptance was completed in September 2026.
M3 automatic production deployment was retired on November 3, 2026.
Module 3 CI remains active.

The historical M3 deployment workflow is preserved in
[`module-3/docs/archive/deploy-m3.yml`](../module-3/docs/archive/deploy-m3.yml),
and the post-course lifecycle decision and acceptance evidence are
documented in [`module-3/docs/post-course-lifecycle.md`](../module-3/docs/post-course-lifecycle.md).

Module 4 continues to use the shared AWS infrastructure
established for the TaskFlow application baseline.

This infrastructure reuse is independent of the M3
deployment lifecycle. M3 automatic production deployment
has been retired, while M3 CI remains active.

The repository-level M3 workflows are:

- `.github/workflows/ci.yml` — active M3 CI
- `.github/workflows/deploy.yml` — manual-only retirement
  entrypoint; no AWS deployment is performed.

Module 4 uses its own release workflows:

- `.github/workflows/ci-module-4.yml`
- `.github/workflows/deploy-module-4.yml`
- `.github/workflows/promote-module-4.yml`

## Key Module 4 Artifacts

```text
module-4/
├── implementation-plan.md
├── observability/
│   ├── collector.yaml
│   ├── compose.yaml
│   ├── dashboard.json
│   └── alerts.yaml
├── incident-response/
│   ├── collect-evidence.sh
│   ├── responder-task.md
│   ├── response.schema.json
│   ├── autonomy-policy.yaml
│   ├── incidents/
│   └── runbooks/
│       ├── rollback.sh
│       └── verify-recovery.sh
├── security-audit/
│   ├── audit-brief.md
│   ├── findings.schema.json
│   ├── capability-table.md
│   └── runs/
└── docs/
    ├── product-spec.md
    ├── operations-and-security-report.md
    ├── homework-4-evidence.md
    └── acceptance-traceability-matrix.md
```

## Documentation

- [`docs/product-spec.md`](docs/product-spec.md) — approved Module 4 product requirements.
- [`implementation-plan.md`](implementation-plan.md) — phases, scope, verification gates, and explicit project decisions.
- [`docs/operations-and-security-report.md`](docs/operations-and-security-report.md) — operational incident and security-review trail.
- [`docs/acceptance-traceability-matrix.md`](docs/acceptance-traceability-matrix.md) — requirement-to-implementation and evidence traceability.
- [`security-audit/audit-brief.md`](security-audit/audit-brief.md) — P6-A security-review scope and evidence rules.
- [`security-audit/capability-table.md`](security-audit/capability-table.md) — responder capabilities and credential boundaries.
- [`docs/homework-4-evidence.md`](docs/homework-4-evidence.md) — reference/index only for the separate Homework 4 workstream.

## Scope Principles

Module 4 intentionally does not become a general-purpose autonomous remediation system or a broader SRE platform. The implementation keeps evidence bounded and read-only, authorization external to model confidence, actions explicitly allowlisted and bounded, recovery verification independent, and secrets excluded from telemetry and incident evidence.
