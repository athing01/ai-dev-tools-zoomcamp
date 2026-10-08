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

P6-B is a separate Homework 4 exercise against the `order-tracker` starter/fork. Homework 4 evidence is owned by that repository; the TaskFlow repository keeps only a reference/index and does not add order-tracker-specific runtime behavior.

## Module 3 Boundary

Module 4 extends the completed Module 3 baseline. The existing M3 release workflows remain protected and are not silently replaced or modified as part of normal Module 4 work.

```text
.github/workflows/ci.yml
.github/workflows/deploy.yml
```

Module 4 may reuse compatible foundations from the existing system, while keeping Module 4 scope and operational boundaries explicit.

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
