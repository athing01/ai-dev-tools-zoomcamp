# Module 4 Implementation Plan — DevOps and Observability for TaskFlow

## 1. Purpose

This implementation plan defines the minimum work required to implement Module 4 for TaskFlow.

The implementation supports the required operational loop:

> **Change → observe user impact → alert with context → investigate from evidence → authorize a bounded response or escalate → verify recovery → audit the code and response trail**

This is an implementation plan, not an architecture redesign. It translates the approved Module 4 Product Specification into implementation phases while preserving the Module 3 production baseline.

## 2. Sources and Implementation Boundaries

### 2.1 Authority Order

Implementation decisions must follow this order:

1. `module-4/docs/product-spec.md`
2. Official Module 4 lesson
3. Homework 4 requirements
4. Module 4 transcript
5. Companion article
6. Module 3 baseline and implementation context
7. Explicit project decisions made during implementation

The companion article may provide examples, but examples do not become requirements unless supported by a higher-priority source.

### 2.2 Protected Module 3 Baseline

Module 4 extends, but must not silently replace or alter, the existing Module 3 production baseline.

The following existing workflows are protected and must remain untouched:

```text
.github/workflows/ci.yml
.github/workflows/deploy.yml
```

Module 4 may reuse compatible existing foundations, including:

- Existing immutable container-artifact conventions.
- Existing release-manifest or release-record conventions.
- Existing AWS authentication and controlled execution patterns.
- Existing deployment mechanisms where appropriate.
- Existing backend application behavior and operational signals.

Module 4 must not require a specific DEV/PROD infrastructure topology, separate database, additional EC2 instance, or modification to the M3 CloudFormation stack.

### 2.3 Scope Limits

This plan intentionally excludes:

- SLOs, error budgets, and burn-rate alerting.
- Synthetic monitoring, RUM, profiling, and observability-cost management.
- Feature flags, canary deployment, blue/green deployment, or chaos engineering.
- A mandatory separate DEV runtime, database, stack, or AWS resource layout.
- Rebuilding a different artifact for production promotion.
- General-purpose autonomous remediation.
- Arbitrary production shell access, commands, or diagnostic queries.
- SBOMs, artifact signing, penetration testing, and a broader security program.
- A new M3 readiness endpoint.
- Hard-coded Homework 4 answers.

## 3. Required Module 4 Repository Structure

The Module 4 implementation must use the following paths and filenames.

```text
module-4/
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
    ├── operations-and-security-report.md
    ├── product-spec.md
    ├── homework-4-evidence.md
    └── acceptance-traceability-matrix.md
```

The required Module 4 workflow names are:

```text
.github/workflows/ci-module-4.yml
.github/workflows/deploy-module-4.yml
.github/workflows/promote-module-4.yml
```

No additional Module 4 workflow files are introduced by this plan.

## 4. Implementation Principles

- **Build once:** A release artifact is built once and receives an immutable identity.
- **Promote the same artifact:** PROD promotion reuses the already-built artifact deployed to DEV; it does not rebuild application source.
- **Protect M3:** Module 4 must not alter the existing M3 release workflows without an explicit future project decision.
- **Observe one important operation:** Complete end-to-end observability for one important backend endpoint or user-relevant operation before expanding coverage.
- **Evidence before reasoning:** The AI responder receives a bounded evidence packet rather than unrestricted access.
- **Read-only responder:** The responder is a headless system actor and does not receive general production credentials or arbitrary command execution.
- **Authorization is external:** Model confidence, recommendation, or free-form text cannot grant authority to execute an action.
- **Bounded autonomy:** Actions must be limited by an explicit policy and must be rejected or escalated when not authorized.
- **Independent verification:** Completion of an action does not prove recovery; the original impact condition must be checked independently.
- **Secret hygiene:** Secrets and credentials must not appear in telemetry, evidence packets, responder input, or audit outputs.
- **Auditable operation:** Release, alert, evidence, model/configuration, policy decision, action, verification, security review, and human disposition must be reconstructable.

## 5. Phase 3 — Release Behavior and Operational Identity

### Objective

Implement the minimum release behavior:

- New changes reach DEV automatically.
- PROD remains user-facing and is promoted manually.
- PROD promotion uses the same already-built artifact deployed to DEV.
- The deployed release is identifiable during operations and incident investigation.

### Scope

This phase defines release behavior, not infrastructure topology.

It does not require:

- Separate DEV and PROD EC2 instances.
- Separate application stacks.
- Separate databases.
- A particular AWS resource layout.
- A particular GitHub trigger design beyond the required DEV and PROD behavior.

The exact workflow-trigger semantics remain an implementation decision, provided DEV receives qualifying changes automatically and PROD promotion remains manual.

### Components

| Component | Purpose |
|---|---|
| `.github/workflows/ci-module-4.yml` | Builds and validates the Module 4 release artifact using the selected implementation path |
| `.github/workflows/deploy-module-4.yml` | Deploys the already-built release artifact to DEV automatically |
| `.github/workflows/promote-module-4.yml` | Manually promotes an existing DEV release artifact to PROD |
| Existing artifact/release conventions | Preserve immutable artifact identity and release traceability |
| `module-4/docs/operations-and-security-report.md` | Later records release-to-incident linkage |

### Implementation Tasks

1. Define a release identity based on the existing immutable artifact identity and an associated commit or release reference.
2. Configure `ci-module-4.yml` to validate and build the release artifact once.
3. Preserve the artifact identity so it can be deployed to DEV and later promoted to PROD without rebuilding.
4. Configure `deploy-module-4.yml` to automatically deploy the built artifact to DEV after the applicable build and validation conditions are met.
5. Configure `promote-module-4.yml` as a manual promotion path.
6. Require the production promotion to reference an existing DEV release artifact.
7. Validate that the selected release artifact exists before promotion.
8. Record release identity, environment, deployment result, and promotion decision in a traceable release record.
9. Preserve the existing rollback principle: redeploy a previously known artifact rather than rebuild source.

### Verification

- A qualifying change results in automatic deployment to DEV.
- DEV deployment identifies the deployed artifact or release.
- PROD is not deployed by the automatic DEV deployment path.
- A human initiates or approves the PROD promotion.
- DEV and PROD records identify the same immutable artifact.
- Existing M3 workflows remain unchanged.

### Evidence

- A `deploy-module-4.yml` run showing DEV deployment and artifact identity.
- A `promote-module-4.yml` run showing manual PROD promotion.
- Release records showing the same artifact identity in DEV and PROD.
- Repository evidence confirming no modification to `.github/workflows/ci.yml` or `.github/workflows/deploy.yml`.

### Exit Gate

Phase 3 is complete when an already-built artifact reaches DEV automatically and can be promoted manually to PROD without a source rebuild.

### Deferred Decisions

- Exact DEV/PROD infrastructure boundary.
- Shared versus separate runtime or database resources.
- Exact release-record storage mechanism.
- Exact workflow trigger syntax and approval mechanism.
- Artifact retention configuration.

## 6. Phase 4 — Observability, Dashboard, and User-Impact Alert

### Objective

Provide end-to-end observability for at least one important TaskFlow backend endpoint or user-relevant operation, expose the operational signals through a dashboard, and trigger one real user-impact alert.

### Required Signals

The selected operation must produce:

- Metrics
- Traces
- Structured logs

The resulting telemetry must support correlation of:

- Application or service
- Environment, including DEV versus PROD
- Deployed release or version

Not every individual telemetry record must include every field, provided the available signals can be correlated during an incident investigation.

### Components

| Component | Purpose |
|---|---|
| `module-4/observability/collector.yaml` | Defines telemetry collection or routing configuration |
| `module-4/observability/compose.yaml` | Defines the selected observability runtime composition where needed |
| `module-4/observability/dashboard.json` | Defines the dashboard for the selected operation |
| `module-4/observability/alerts.yaml` | Defines the user-impact alert |
| Application instrumentation | Emits required metrics, traces, and structured logs |

### Implementation Tasks

1. Select one important backend endpoint or user-relevant operation.
2. Record why the selected operation is relevant to TaskFlow users.
3. Add minimum instrumentation for metrics, traces, and structured logs.
4. Configure telemetry collection through `collector.yaml`.
5. Use `compose.yaml` only to support the selected observability implementation; it must not impose a broader infrastructure redesign.
6. Ensure telemetry can distinguish:
   - The relevant application or service.
   - DEV from PROD.
   - The deployed release or version.
7. Review telemetry fields and configuration to prevent secret or credential leakage.
8. Create `dashboard.json` to make health or user-impacting behavior visible.
9. Ensure dashboard evidence can distinguish the selected environment and deployed release.
10. Create `alerts.yaml` with at least one alert representing a real application failure affecting the selected operation.
11. Ensure the alert provides enough signal, environment, and release context to start an investigation.
12. Validate normal operation telemetry before reproducing the approved controlled failure.
13. Reproduce the approved failure only in the selected safe environment.
14. Confirm the failure appears in telemetry, the dashboard, and alert state.

### Verification

- The selected operation emits metrics, traces, and structured logs.
- Telemetry supports investigation by service, environment, and deployed release.
- The dashboard distinguishes DEV and PROD.
- The dashboard exposes relevant health or user-impacting behavior.
- A real user-impacting failure triggers the alert.
- The alert contains enough context to begin bounded evidence collection.
- Tested telemetry does not include credentials, tokens, secret values, or connection strings.

### Evidence

- Metrics for successful and controlled-failure operation runs.
- Trace evidence for the selected operation.
- Structured-log evidence for the selected operation.
- Dashboard evidence showing environment, release, and application behavior.
- Alert history or alert-state evidence for the controlled failure.
- Telemetry hygiene review evidence.

### Exit Gate

Phase 4 is complete when one important operation is observable end to end and its real user-impacting failure can begin an incident investigation.

### Deferred Decisions

- Selected telemetry backend.
- Selected dashboard implementation.
- Exact dashboard layout, panels, variables, and time ranges.
- Exact alert threshold, severity, routing, and notification method.
- Exact controlled failure scenario used for TaskFlow observability validation.

## 7. Phase 5 — TaskFlow Incident Response

### Objective

Implement the minimum incident-response flow for **TaskFlow**:

> **Alert → bounded read-only evidence → structured AI assessment → external authorization → bounded action or escalation → independent recovery verification**

### Scope correction

Phase 5 is **TaskFlow-only**.

The primary operational scenario is the real TaskFlow Phase 4 user-impact alert around:

```text
GET /api/tasks
operation = tasks.list
environment = DEV
controlled failure = Phase 4 approved fault mode
```

P5 must extend the already-proven P4 chain rather than introduce an order-tracker-derived incident into TaskFlow.

Homework 4 is a separate graded workstream using `order-tracker` and is not a P5 TaskFlow dependency.

This scenario is selected from TaskFlow P4 observability and is not derived from, nor required to reproduce, the `order-tracker` Homework 4 fault.

### Components

| Component | Purpose |
|---|---|
| `module-4/incident-response/collect-evidence.sh` | Collects bounded, repeatable, read-only TaskFlow incident evidence |
| `module-4/incident-response/responder-task.md` | Defines the headless responder task and evidence boundary |
| `module-4/incident-response/response.schema.json` | Defines and validates structured responder output |
| `module-4/incident-response/autonomy-policy.yaml` | Defines permitted bounded actions, authorization conditions, and escalation behavior |
| `module-4/incident-response/incidents/` | Stores or references auditable TaskFlow incident records |
| `module-4/incident-response/runbooks/rollback.sh` | Performs an approved bounded rollback using a known prior artifact |
| `module-4/incident-response/runbooks/verify-recovery.sh` | Independently verifies recovery or records escalation |

### 7.1 Bounded Evidence Collection

#### Implementation Tasks

1. Create `collect-evidence.sh` as a read-only collector.
2. Use only predefined, allowlisted evidence sources and checks.
3. Bound collection by:
   - affected TaskFlow operation
   - environment
   - incident time window
   - deployed release where available
4. Collect only evidence needed to investigate the TaskFlow incident, including as applicable:
   - application behavior
   - relevant metrics
   - relevant traces
   - relevant structured logs
   - alert state
   - environment and deployed release context
   - health evidence only when independently required by the TaskFlow Product Specification or P5 verification
5. Do not collect or expose secrets, credentials, arbitrary files, unrestricted logs, unrelated data, or arbitrary query/command text.
6. Make collection repeatable for the same incident context.
7. Produce a bounded evidence packet suitable for a headless responder.

#### Verification

- Evidence collection is read-only.
- Evidence sources and queries are allowlisted.
- Collection is bounded by operation, environment, time, and incident context.
- The generated packet contains sufficient investigation evidence.
- The collector does not expose secrets or credentials.

### 7.2 Structured AI Responder

#### Implementation Tasks

1. Create `responder-task.md` for a headless, read-only responder.
2. Feed the responder only the bounded evidence packet.
3. Require structured output with at least:
   - incident identifier
   - evidence summary
   - likely or contributing cause
   - confidence or uncertainty
   - proposed bounded action, where appropriate
   - escalation decision
   - rationale
   - missing evidence
4. Validate output against `response.schema.json` before authorization handling.
5. Record model/provider/adapter/configuration references needed to reconstruct the response.
6. Keep the responder interface vendor-neutral.

#### Safety Boundary

The model is a **proposal source**, not an authority source.

It must not receive:

- general production credentials
- arbitrary production shell access
- unrestricted diagnostic queries
- permission to execute free-form model output

#### Verification

- The responder receives only bounded evidence.
- The responder produces schema-valid output.
- Invalid or incomplete output is rejected.
- The responder cannot use arbitrary commands or unrestricted production access.
- Model/provider/configuration references are retained with the incident record.

### 7.3 External Authorization and Bounded Autonomy

#### Implementation Tasks

1. Create `autonomy-policy.yaml`.
2. Define the permitted bounded TaskFlow action types.
3. Define preconditions for each permitted action.
4. Define actions requiring human approval.
5. Define actions that must be rejected or escalated.
6. Keep authorization outside the model.
7. Never convert free-form responder text directly into executable commands.
8. Record:
   - proposed action
   - authorization decision
   - approval, when required
   - actual action
   - escalation outcome, when applicable

#### Bounded Action Rule

A rollback may be used only as an explicitly authorized bounded operation using a previously known immutable release artifact. It must not rebuild source code.

The exact action set and approval mechanism remain P5 implementation decisions, subject to the Product Specification and safety rules.

#### Verification

- A proposed non-permitted action is rejected or escalated.
- Model confidence alone cannot execute an action.
- Every actual action has a recorded external authorization decision.
- The executor receives a bounded action request rather than unvalidated model text.

### 7.4 Independent Recovery Verification

#### Implementation Tasks

1. Create `runbooks/verify-recovery.sh`.
2. Re-check the original TaskFlow user-impacting condition independently after any authorized action.
3. Record exactly one of:
   - `verified`
   - `unresolved`
   - `inconclusive`
4. Do not treat responder conclusion or action attempt as proof of recovery.
5. Use relevant TaskFlow application behavior and, where useful, correlated metrics/logs/traces/alert state.
6. Escalate unresolved or inconclusive results.

#### Recovery Rule

```text
Action attempted
    !=
Recovery verified
```

### Incident Traceability

Each material TaskFlow incident must be reconstructable through:

```text
Incident
→ deployed release
→ user impact
→ alert
→ bounded evidence
→ model/configuration
→ proposed action
→ authorization
→ actual action
→ recovery verification / escalation
```

The exact incident-record storage format remains an implementation decision.

### Phase 5 Verification

The phase must demonstrate a real TaskFlow alert flowing through the complete bounded loop, with either:

```text
authorized bounded action → independently verified recovery
```

or:

```text
bounded assessment → external rejection/escalation → recorded escalation
```

### Exit Gate

Phase 5 is complete when a real TaskFlow alert can produce bounded evidence, structured read-only AI assessment, an externally authorized bounded action or escalation, and an independently verified recovery status.

### Explicit P5 Non-Goals

Do not add order-tracker-specific behavior to TaskFlow, including:

- `/api/orders`
- order IDs such as `standard-1001` or `express-1002`
- order-specific seeded data
- order-specific date-calculation faults
- homework-specific health-check behavior
- any TaskFlow application change whose only justification is Homework 4

### Deferred Decisions

- AI vendor, model, and adapter implementation.
- Exact action set permitted by `autonomy-policy.yaml`.
- Exact approval mechanism.
- Incident-record format and storage implementation.
- Exact recovery-verification queries and checks.

## 8. Phase 6 — Finalization with Two Controlled Workstreams

Phase 6 remains **one top-level phase**. It contains two explicitly separated sub-plans:

```text
P6-A  TaskFlow security audit + final acceptance
P6-B  Homework 4 / order-tracker execution
```

This preserves the existing Phase 6 structure without creating an additional top-level phase.

### 8.1 P6-A — TaskFlow Security Audit and Final Acceptance

#### Objective

Complete the TaskFlow Module 4 security review, operational documentation, incident/audit traceability, and final acceptance evidence.

#### Security Audit Tasks

1. Complete `module-4/security-audit/audit-brief.md`.
2. Define the limited audit scope for:
   - TaskFlow application and Module 4 operational code
   - evidence collection controls
   - responder task and adapter boundary
   - autonomy policy and bounded action handling
   - responder capabilities, tools, and credential boundaries
3. Configure or run the required Semgrep scanning through the permitted Module 4 workflow implementation.
4. Run Snyk Agent Scan for the responder attack surface.
5. Conduct model-assisted review of relevant findings/configuration.
6. Require human validation and disposition of findings.
7. Complete `findings.schema.json` and retain provenance for each finding.
8. Complete `capability-table.md` covering:
   - read-only evidence available to responder
   - prohibited systems/data/credentials
   - available tools and restrictions
   - arbitrary command execution unavailable
   - credential boundaries
   - authorization boundary
   - model/provider/configuration reference approach

Raw scanner or model output is not a confirmed finding until human validation/disposition is recorded.

#### Final TaskFlow Documentation

Complete:

```text
module-4/security-audit/
├── audit-brief.md
├── findings.schema.json
├── capability-table.md
└── runs/

module-4/docs/
├── operations-and-security-report.md
├── homework-4-evidence.md
└── acceptance-traceability-matrix.md
```

`homework-4-evidence.md` is an evidence index for the separately executed Homework 4 workstream. It must not imply that order-tracker is part of the TaskFlow runtime architecture. The file must begin with this exact boundary statement:

> **Evidence Index Only — Authoritative Homework 4 Evidence Resides in the Order-Tracker Fork.**

The index must reference, rather than duplicate, authoritative homework evidence.

#### Final TaskFlow Verification

Confirm:

- P3 release behavior remains correct.
- P4 observability remains correct.
- P4 alert remains actionable.
- P5 incident response is bounded, authorized, and auditable.
- M3 protected workflows remain unchanged.
- Security findings have human disposition.
- The material TaskFlow incident and security-review trail is reconstructable.

#### P6-A / P6-B Independence Rule

P6-A TaskFlow acceptance and P6-B Homework submission are independently evidenced; neither workstream changes or validates the other system's runtime behavior.

#### P6-A Exit Gate

P6-A is complete when TaskFlow security-review evidence, operational documentation, acceptance traceability, and the material incident/audit trail are complete and evidence-backed.

### 8.2 P6-B — Homework 4 / Order-Tracker Execution Sub-Plan

#### Objective

Complete the separately graded Homework 4 exercise against the official `order-tracker` starter/fork and generate the live evidence required for the homework submission.

#### Repository Boundary

Homework 4 uses its own application repository:

```text
alexeygrigorev/order-tracker
        ↓
student homework fork / repository
```

This repository is independent from the TaskFlow Module 4 project repository.

#### Homework Repository Provenance

The P6-B record must identify the exact repository lineage used for the graded homework. At minimum, record:

- **Upstream repository:** the official `alexeygrigorev/order-tracker` repository.
- **Homework fork/repository:** the student's fork/repository used for the submission.
- **Branch and/or commit SHA:** the exact revision from which the homework evidence was produced.
- **Evidence ownership:** authoritative Homework 4 runtime output, incident records, dashboard/telemetry observations, responder output, fix/recovery evidence, and submission answers belong to the homework fork/repository.

The provenance record must make it possible to trace each submitted answer back to the exact homework repository revision that generated the evidence.

#### H4-0 — Homework Repository Preflight

Tasks:

- Verify the homework repository and branch state.
- Read the official Homework 4 requirements and submission questions.
- Confirm local/runtime prerequisites.
- Identify the baseline endpoints and seeded data required by the homework.
- Keep homework changes inside the homework repository unless the official requirement explicitly requires otherwise.

Exit evidence: a reproducible baseline with the exact homework repository and requirements identified.

#### H4-1 — Run the App

Tasks:

- Start the homework application using the prescribed workflow.
- Verify the homework health-check behavior from the running application.
- Capture raw command output as evidence.

Exit evidence: a running application and observed health-check evidence sufficient for the homework question.

#### H4-2 — Instrument One Endpoint

Tasks:

- Select the endpoint required by the official homework question.
- Add the minimum telemetry needed by the homework.
- Verify the actual HTTP status and route attributes from runtime evidence.
- Do not hard-code expected answer values.

Exit evidence: runtime telemetry proving the selected endpoint's observed status/route behavior.

#### H4-3 — Build the Telemetry Pipeline

Tasks:

- Configure the telemetry pipeline required by Homework 4.
- Ensure the course-approved dashboard/telemetry stack exposes the required evidence.
- Correlate request, log, and trace evidence where required.

Exit evidence: dashboard plus matching metrics/logs/traces sufficient to answer the homework telemetry question from live evidence.

#### H4-4 — Configure the Alert

Tasks:

- Implement the alert condition required by Homework 4.
- Verify the alert behavior for the required failure/non-failure cases.
- Capture the actual rule/alert state from the running homework system.

Exit evidence: observed alert state, not an answer inferred from source code.

#### H4-5 — Build / Exercise the Automatic Responder

Tasks:

- Configure the homework responder path required by the official assignment.
- Exercise the responder against the designated test condition.
- Preserve the structured responder output and incident record.
- Verify that the responder capability/authorization boundaries meet the homework requirements and explicit safety constraints.

Exit evidence: retained incident record containing the responder assessment and outcome.

#### H4-6 — Controlled Incident and Agent Fix

Tasks:

- Trigger or reproduce the designated Homework 4 application failure.
- Confirm the alert fired.
- Collect the evidence required to diagnose the incident.
- Run the homework-required agent/fix workflow in its permitted sandbox or bounded environment.
- Validate the change with the required tests and replay/rebuild checks.
- Keep go/no-go decisions under code-enforced gates and explicit assignment constraints rather than model free-form authority.

Exit evidence:

```text
failure
→ alert
→ evidence
→ diagnosis
→ bounded agent/fix activity
→ validation
→ recovery result
```

#### H4-7 — Recovery and Evidence Capture

Tasks:

- Independently verify that the original homework failure condition is resolved.
- Preserve the incident record, commit reference, and runtime verification.
- Capture the exact observed outputs needed for submission.

Exit evidence: reproducible evidence package from the running homework system.

#### H4-8 — Submission Evidence Mapping

Map evidence to every Homework 4 question, distinguishing:

- raw command output
- runtime metrics
- dashboard observations
- Loki/Tempo or equivalent correlation
- alert state
- responder result
- incident diagnosis
- fix/recovery evidence
- commit or incident-record references

Do not write answers into application behavior or alter telemetry solely to force expected values.

#### P6-B Exit Gate

Homework 4 is complete when every submission answer is supported by observed evidence or a retained incident record in the **order-tracker homework repository**, the exact upstream/fork/branch-or-commit provenance is recorded, and the submission can be reconstructed independently from those records.

`module-4/docs/homework-4-evidence.md` in the TaskFlow repository is **reference/index-only**. It may record repository path, incident ID, commit SHA, timestamps, and links/references, but it is not an authoritative copy of Homework 4 evidence.

## 9. Acceptance Traceability Matrix

| Requirement / evidence | Owner | Phase | Primary evidence |
|---|---|---:|---|
| DEV receives qualifying changes automatically | TaskFlow | P3 | DEV deployment record |
| PROD promotion is manual | TaskFlow | P3 | Manual promotion record |
| PROD reuses already-built artifact | TaskFlow | P3 | Matching immutable artifact identity |
| M3 workflows remain protected | TaskFlow | P3–P6 | No unintended changes to `ci.yml` / `deploy.yml` |
| One important operation has metrics, traces, and structured logs | TaskFlow | P4 | Correlated telemetry evidence |
| Environment and release are distinguishable | TaskFlow | P3–P4 | Release + telemetry evidence |
| Telemetry does not expose secrets or credentials | TaskFlow | P4–P6 | Telemetry/security review |
| Dashboard shows health or user-impacting behavior | TaskFlow | P4 | Dashboard evidence |
| Real user-impact alert exists | TaskFlow | P4 | Alert evidence |
| Evidence collection is read-only, bounded, allowlisted, repeatable | TaskFlow | P5 | Evidence packet + collector review |
| AI responder is read-only and structured | TaskFlow | P5 | Schema-valid responder result |
| Authorization is external to model confidence | TaskFlow | P5 | External authorization decision |
| Recovery is independently verified or escalated | TaskFlow | P5 | Verification/escalation record |
| Semgrep scanning | TaskFlow | P6-A | Security audit run |
| Model-assisted security review | TaskFlow | P6-A | Security review record |
| Human validation and disposition | TaskFlow | P6-A | Findings disposition |
| Snyk Agent Scan covers responder attack surface | TaskFlow | P6-A | Snyk Agent Scan evidence |
| Capability and credential boundary reviewed | TaskFlow | P6-A | `capability-table.md` |
| Material TaskFlow incident trail auditable | TaskFlow | P5–P6-A | Incident record + final report |
| Homework health-check evidence | order-tracker | P6-B | Homework runtime evidence |
| Homework endpoint metric HTTP status | order-tracker | P6-B | Runtime metric evidence |
| Homework dashboard/telemetry evidence | order-tracker | P6-B | Dashboard + telemetry evidence |
| Homework alert state | order-tracker | P6-B | Live alert/rule state |
| Homework responder evidence | order-tracker | P6-B | Incident/responder record |
| Homework diagnosis/fix/recovery evidence | order-tracker | P6-B | Incident record + runtime verification |
| Homework submission answers | order-tracker evidence | P6-B | Evidence-to-question mapping |
| TaskFlow `homework-4-evidence.md` ownership boundary | TaskFlow index + order-tracker authoritative evidence | P6-A/P6-B | Reference-only index with provenance links |

### Ownership Rule

A Homework 4 evidence row does **not** mean that TaskFlow must implement the corresponding order-tracker feature.

## 10. Final Completion Checklist

### TaskFlow Release / Deployment

- [ ] P3 DEV and PROD release behavior remains correct.
- [ ] PROD promotion reuses the same immutable artifact.
- [ ] Release identity remains traceable.
- [ ] Existing M3 workflows remain unchanged.

### TaskFlow Observability / Alerting

- [ ] P4 end-to-end observability remains functional.
- [ ] Metrics, traces, and structured logs correlate for `tasks.list`.
- [ ] Dashboard identifies environment and release.
- [ ] The real P4 user-impact alert remains actionable.
- [ ] Telemetry remains free of secret material.

### TaskFlow Incident Response

- [ ] Evidence collection is read-only, allowlisted, bounded, and repeatable.
- [ ] Evidence is limited to the affected TaskFlow operation and incident context.
- [ ] Responder receives only bounded evidence.
- [ ] Responder output is schema-valid.
- [ ] Model/provider/configuration provenance is recorded.
- [ ] Authorization is external to model confidence.
- [ ] Unauthorized actions are rejected or escalated.
- [ ] Any action is bounded and explicitly authorized.
- [ ] Recovery verification is independent.
- [ ] Unverified recovery produces escalation.
- [ ] Incident traceability is reconstructable.

### TaskFlow Security / Audit

- [ ] Semgrep evidence exists.
- [ ] Snyk Agent Scan evidence exists for the responder attack surface.
- [ ] Model-assisted review is recorded.
- [ ] Human validation/disposition is recorded.
- [ ] Capability and credential boundaries are documented.
- [ ] Security findings retain provenance.
- [ ] Final operations/security report is complete.
- [ ] Acceptance traceability matrix is complete.

### Homework 4 / Order-Tracker

- [ ] Homework repository is separate from TaskFlow project repository.
- [ ] Health-check answer is supported by runtime evidence.
- [ ] Endpoint metric HTTP status is supported by runtime telemetry.
- [ ] Dashboard/Loki/Tempo evidence is retained where required.
- [ ] Alert state is observed from the running system.
- [ ] Responder output is retained in an incident record.
- [ ] The underlying application problem is supported by evidence.
- [ ] Agent/fix validation and recovery are evidenced.
- [ ] Every submission question maps to evidence.
- [ ] No homework answer is hard-coded.

## Scope Revision Summary

This revision makes a **scope correction, not an architecture redesign**.

- **P0–P4 remain completed/frozen.** No completed Phase 3 or Phase 4 behavior is reopened.
- **P5 is explicitly TaskFlow-only.** The existing P4 `tasks.list` alert/failure path becomes the primary incident-response scenario.
- **Homework 4 is separated from TaskFlow.** The graded homework is executed against the independent `order-tracker` starter/fork.
- **Phase 6 remains one top-level phase.** It now contains P6-A for TaskFlow finalization and P6-B for Homework 4 execution.
- **Homework evidence ownership is corrected.** Authoritative Homework 4 evidence belongs to the order-tracker workstream; the TaskFlow repository may retain only a reference/index.
- **Homework provenance is explicit.** P6-B records the upstream repository, homework fork/repository, branch and/or commit SHA, and the authoritative evidence location.
- **Required artifact names remain unchanged.** `collect-evidence.sh`, `response.schema.json`, `autonomy-policy.yaml`, `rollback.sh`, `verify-recovery.sh`, security-audit artifacts, and required workflow names are preserved.
- **M3 remains protected.** No M3 production workflow or production baseline change is implied by this revision.
- **No homework-driven TaskFlow features are permitted.** Order-specific endpoints, seeded data, faults, or health behavior must not be added to TaskFlow solely to satisfy Homework 4.
- **Product Specification remains frozen by default.** Any direct contradiction discovered in the Product Specification must be resolved explicitly through the authority order; it must not be silently rewritten to fit implementation.

## Revision Decision Register

### DEC-REV-01 — Application Boundary

**Decision:** TaskFlow is the Module 4 project target; `order-tracker` is the Homework 4 target.

**Reason:** The homework is a separately graded exercise against the order-tracker starter/fork and must not redefine TaskFlow requirements.

### DEC-REV-02 — P5 Incident Target

**Decision:** P5 uses the existing TaskFlow P4 `tasks.list` alert/failure path.

**Reason:** It is already implemented and observable, so P5 should extend a proven signal rather than import a different application's incident domain.

### DEC-REV-03 — Phase 6 Structure

**Decision:** Keep Phase 6 as one top-level phase and add P6-A and P6-B sub-plans.

**Reason:** Preserves the established phase structure while restoring correct ownership.

### DEC-REV-04 — Product Specification

**Decision:** Do not rewrite `module-4/docs/product-spec.md` solely to accommodate Homework 4.

**Reason:** The Product Specification remains the highest-priority project contract. Scope is corrected at implementation-plan/evidence ownership level first.

### DEC-REV-05 — No Homework-Driven TaskFlow Features

**Decision:** Do not add order-tracker endpoints, seeded data, order-specific faults, or homework-only health behavior to TaskFlow.

### DEC-REV-06 — Independent Evidence

**Decision:** TaskFlow P5 evidence and Homework 4 evidence must be independently reproducible from their respective running systems / incident records.

### DEC-REV-07 — Homework Evidence Provenance

**Decision:** P6-B must record upstream repository, homework fork/repository, branch and/or commit SHA, with authoritative Homework evidence retained in the homework fork/repository.

### DEC-REV-08 — Homework Evidence Index

**Decision:** `module-4/docs/homework-4-evidence.md` is reference/index-only and must carry the explicit authoritative-evidence boundary header.

### DEC-REV-09 — P5 Recovery Environment

**Decision:** All P5 recovery actions and recovery verification are executed against
M4 DEV only. M4 PROD is explicitly out of scope for P5 incident-response
action execution.

**Reason:** P5 needs to demonstrate the bounded authorization and independent
recovery-verification loop without introducing production risk.
Production remains untouched during P5 validation.

## Revision Acceptance Gate

Before creating the P5 branch:

- [ ] P0–P4 are still treated as completed.
- [ ] P5 is explicitly TaskFlow-only.
- [ ] The primary P5 incident is the existing `tasks.list` alert/failure.
- [ ] Homework 4 is explicitly separated from TaskFlow implementation.
- [ ] Phase 6 remains the only remaining top-level phase.
- [ ] P6-A and P6-B ownership is explicit.
- [ ] The acceptance matrix assigns homework evidence to order-tracker.
- [ ] P6-B records upstream, fork/repository, and branch/commit provenance.
- [ ] TaskFlow `homework-4-evidence.md` is explicitly reference/index-only.
- [ ] Product Specification has not been silently rewritten.
- [ ] No new TaskFlow feature is justified solely by Homework 4.
