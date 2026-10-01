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
- Selected operation and controlled Homework 4 failure scenario.

## 7. Phase 5 — Bounded Evidence, AI Responder, Authorization, and Recovery Verification

### Objective

Implement the minimum incident-response flow:

> **Alert → bounded read-only evidence → structured AI assessment → external authorization → bounded action or escalation → independent recovery verification**

### Scope

The AI responder is a read-only system actor. It receives bounded evidence and produces structured output through a vendor-neutral adapter.

The responder must not receive:

- General production credentials.
- Arbitrary command execution.
- Unrestricted production queries.
- Authority granted by its own confidence or recommendation.

### Components

| Component | Purpose |
|---|---|
| `module-4/incident-response/collect-evidence.sh` | Collects bounded, repeatable, read-only incident evidence |
| `module-4/incident-response/responder-task.md` | Defines the responder task, evidence boundary, and expected behavior |
| `module-4/incident-response/response.schema.json` | Defines and validates structured responder output |
| `module-4/incident-response/autonomy-policy.yaml` | Defines permitted bounded actions, authorization conditions, and escalation behavior |
| `module-4/incident-response/incidents/` | Stores or references auditable incident records |
| `module-4/incident-response/runbooks/rollback.sh` | Performs an approved rollback through a bounded procedure |
| `module-4/incident-response/runbooks/verify-recovery.sh` | Independently verifies recovery or records escalation |

### 7.1 Bounded Evidence Collection

#### Implementation Tasks

1. Create `collect-evidence.sh`.
2. Limit collection to predefined, read-only, allowlisted evidence sources and checks.
3. Bound collection by the affected operation, environment, incident time window, and deployed release where available.
4. Collect only evidence needed to investigate:
   - Application behavior.
   - Relevant metrics.
   - Relevant traces.
   - Relevant structured logs.
   - Alert state.
   - Environment and deployed release context.
   - Health-check evidence required by Homework 4.
5. Ensure the collector does not retrieve or output secrets, credentials, arbitrary files, unrestricted logs, or unrelated system data.
6. Ensure the collector does not accept arbitrary command text or arbitrary query text.
7. Ensure the collector can be rerun for the same incident condition.

#### Verification

- Evidence collection is read-only.
- Evidence sources and queries are allowlisted.
- Collection is bounded by operation, environment, time, and incident context.
- The generated packet contains sufficient investigation evidence.
- The collector does not expose secrets or credentials.

### 7.2 Structured AI Responder

#### Implementation Tasks

1. Create `responder-task.md`.
2. Define the responder as a headless, read-only system actor.
3. Require the responder to identify:
   - Likely cause or contributing cause.
   - Supporting evidence.
   - Confidence or uncertainty.
   - Proposed bounded action when appropriate.
   - Escalation when it cannot determine a safe action.
4. Create `response.schema.json`.
5. Validate responder output against the schema before it enters authorization handling.
6. Record the model, provider, adapter, and relevant configuration reference used for each response.
7. Implement the responder through a vendor-neutral structured-output interface or adapter.

#### Required Structured Output

The schema must support, at minimum:

| Field | Purpose |
|---|---|
| Incident identifier | Links the response to the incident trail |
| Evidence summary | Identifies evidence reviewed |
| Likely or contributing cause | States the evidence-based assessment |
| Confidence or uncertainty | Makes limits visible |
| Proposed bounded action | Provides a recommended action when appropriate |
| Escalation decision | Indicates when a safe action cannot be determined |
| Rationale | Explains the assessment |
| Missing evidence | Identifies evidence gaps, if any |

#### Verification

- The responder receives only bounded evidence.
- The responder produces output valid against `response.schema.json`.
- Invalid or incomplete output is rejected.
- The responder cannot use arbitrary commands or unrestricted production access.
- The model/provider/configuration reference is retained with the incident record.

### 7.3 External Authorization and Bounded Autonomy

#### Implementation Tasks

1. Create `autonomy-policy.yaml`.
2. Define explicitly permitted bounded action types.
3. Define the conditions under which each permitted action may proceed.
4. Define actions requiring human approval.
5. Define actions that must be rejected or escalated.
6. Ensure the authorization or policy evaluation occurs outside the model.
7. Ensure free-form responder output is never directly executable.
8. Record:
   - The proposed action.
   - Authorization decision.
   - Required approval, where applicable.
   - Actual action taken.
   - Escalation outcome, where applicable.

The exact autonomy-level taxonomy and policy-engine technology remain implementation decisions.

#### Verification

- A proposed non-permitted action is rejected or escalated.
- Model confidence alone cannot execute an action.
- Any actual action has a recorded external authorization decision.
- The executor receives a bounded action request rather than unvalidated model text.

### 7.4 Recovery Verification

#### Implementation Tasks

1. Create `runbooks/verify-recovery.sh`.
2. Independently evaluate the original user-impacting condition after an authorized action.
3. Record one of the following outcomes:
   - Verified recovery.
   - Unresolved failure.
   - Inconclusive result requiring escalation.
4. Do not treat an action attempt or responder conclusion as proof of recovery.
5. Use relevant application behavior, metrics, dashboard state, alert state, and required health-check evidence.

`runbooks/rollback.sh` may be used only as a bounded, authorized rollback procedure. It must use a prior known release artifact rather than trigger a source rebuild.

#### Verification

- Recovery verification evaluates the original affected operation or user-impact condition.
- Recovery can be distinguished from unresolved or inconclusive outcomes.
- Failed or inconclusive verification results in escalation.
- Rollback, if used, is recorded as an authorized action and is followed by independent verification.

### Incident Traceability

Each material incident must be reconstructable through:

```text
Incident
→ deployed version
→ user impact
→ alert
→ evidence
→ model/configuration used
→ proposed action
→ authorization decision
→ actual action taken
→ recovery verification or escalation
→ security finding/review where applicable
→ human disposition
```

The storage technology and exact incident-record schema remain implementation decisions. The `incidents/` directory must preserve or reference the material necessary to reconstruct this trail.

### Exit Gate

Phase 5 is complete when a real alert can produce bounded evidence, structured read-only AI assessment, externally authorized bounded action or escalation, and independently verified recovery status.

### Deferred Decisions

- AI vendor, model, and adapter implementation.
- Exact action set permitted by `autonomy-policy.yaml`.
- Exact approval mechanism.
- Incident-record format and storage implementation.
- Exact recovery-verification queries and checks.

## 8. Phase 6 — Security Audit, Homework Evidence, and Final Acceptance

### Objective

Implement the minimum required security review and produce live running-system evidence for Homework 4 and final Module 4 acceptance.

### Components

| Component | Purpose |
|---|---|
| `module-4/security-audit/audit-brief.md` | Defines minimum audit scope, review process, and evidence expectations |
| `module-4/security-audit/findings.schema.json` | Defines structured security findings and provenance fields |
| `module-4/security-audit/capability-table.md` | Documents responder capabilities and credential boundaries |
| `module-4/security-audit/runs/` | Stores or references audit-run evidence |
| `module-4/docs/homework-4-evidence.md` | Records Homework 4 evidence generated by the running system |
| `module-4/docs/operations-and-security-report.md` | Reconstructs incident and security-review trail |
| `module-4/docs/acceptance-traceability-matrix.md` | Maps Product Specification requirements to implementation and evidence |

### 8.1 Security Audit

#### Implementation Tasks

1. Create `audit-brief.md`.
2. Define the limited audit scope for:
   - Application and Module 4 operational code.
   - Evidence collection controls.
   - Responder task and adapter boundary.
   - Autonomy policy and bounded action handling.
   - Responder capabilities, tools, and credential boundaries.
3. Configure recurring Semgrep scanning through the permitted Module 4 workflow implementation.
4. Run Snyk Agent Scan for the responder attack surface.
5. Conduct model-assisted review of relevant findings and configuration.
6. Require human validation and disposition of security findings.
7. Create `findings.schema.json`.
8. Ensure each finding includes:
   - Finding identifier.
   - Origin, such as Semgrep, Snyk Agent Scan, model-assisted review, or human review.
   - Relevant code, configuration, release, or responder reference.
   - Supporting evidence.
   - Review status.
   - Human disposition.
   - Remediation status where applicable.
9. Create `capability-table.md`.
10. Document:
   - Read-only evidence available to the responder.
   - Prohibited systems, data, and credentials.
   - Available tools and their restrictions.
   - Confirmation that arbitrary command execution is unavailable.
   - Credential boundaries.
   - Authorization boundary.
   - Model/provider/configuration reference approach.

Raw scanner or model output must not be treated as confirmed without human validation.

### 8.2 Homework 4 Evidence Run

#### Implementation Tasks

1. Use the approved controlled failure scenario in the selected safe environment.
2. Generate evidence from the running system. Do not hard-code outcomes or answers.
3. Record evidence sufficient to determine:
   - Health-check behavior.
   - Relevant metric HTTP status.
   - Grafana-observed HTTP status.
   - Relevant alert state.
   - AI responder structured response.
   - Underlying application problem, or why escalation was required.
4. Store or reference the resulting evidence in `homework-4-evidence.md`.
5. Keep M3 readiness behavior separate from the Homework 4 health-check requirement unless the authoritative course source explicitly establishes their relationship.

### 8.3 Final Documentation and Acceptance

#### Implementation Tasks

1. Complete `operations-and-security-report.md`.
2. Reconstruct at least one material incident through:

```text
Incident
→ deployed version
→ user impact
→ alert
→ evidence
→ model/configuration used
→ proposed action
→ authorization decision
→ actual action taken
→ recovery verification or escalation
→ security finding/review where applicable
→ human disposition
```

3. Complete `acceptance-traceability-matrix.md`.
4. Map every Product Specification acceptance requirement to:
   - Implementation component.
   - Validation method.
   - Evidence location.
   - Result or documented limitation.

### Verification

- Semgrep evidence exists.
- Snyk Agent Scan evidence exists for the responder attack surface.
- Model-assisted review is recorded.
- Human validation and disposition are recorded.
- Responder capabilities and credential boundaries are documented.
- Security findings retain provenance.
- Homework 4 evidence is generated by the running system.
- The full incident trail is auditable.
- The acceptance traceability matrix covers all Product Specification acceptance requirements.

### Exit Gate

Phase 6 is complete when security-review evidence, Homework 4 evidence, and the end-to-end incident trail are available and traceable.

### Deferred Decisions

- Exact recurrence schedule or invocation timing for security review.
- Exact reviewer assignment and finding-disposition workflow.
- Controlled failure implementation details.
- Storage mechanism for audit-run artifacts.

## 9. Acceptance Traceability Matrix

| Product requirement | Phase | Primary implementation artifact | Required evidence |
|---|---:|---|---|
| DEV receives qualifying changes automatically | 3 | `deploy-module-4.yml` | DEV deployment record |
| PROD promotion is manual | 3 | `promote-module-4.yml` | Manual promotion record |
| PROD reuses already-built artifact | 3 | Release record and promotion logic | Matching DEV/PROD artifact identity |
| M3 workflows remain protected | 3–6 | M4-only workflow additions | No changes to `ci.yml` and `deploy.yml` |
| One important operation has metrics, traces, and structured logs | 4 | Instrumentation and `collector.yaml` | Correlated signal evidence |
| Environment and release are distinguishable | 3–4 | Release record, telemetry, dashboard | DEV/PROD and release evidence |
| Telemetry does not expose secrets or credentials | 4 | Instrumentation and collector review | Sanitized telemetry review |
| Dashboard shows health or user-impacting behavior | 4 | `dashboard.json` | Dashboard evidence |
| Real user-impact alert exists | 4 | `alerts.yaml` | Alert state for controlled application failure |
| Evidence collection is read-only, bounded, allowlisted, and repeatable | 5 | `collect-evidence.sh` | Evidence packet and collector review |
| AI responder is read-only and structured | 5 | `responder-task.md`, `response.schema.json` | Validated responder result |
| Authorization is external to model confidence | 5 | `autonomy-policy.yaml` | Rejected or escalated unauthorized-action case |
| Recovery is independently verified or escalated | 5 | `verify-recovery.sh` | Verification or escalation record |
| Semgrep scanning occurs | 6 | Security audit evidence in `runs/` | Semgrep result |
| Model-assisted security review occurs | 6 | Security finding/review record | Model-review evidence |
| Human validation and disposition occur | 6 | Findings record | Human disposition |
| Snyk Agent Scan covers responder attack surface | 6 | Security audit evidence in `runs/` | Snyk Agent Scan result |
| Capability and credential boundary is reviewed | 6 | `capability-table.md` | Boundary review |
| Incident trail is auditable | 5–6 | Incident record and final report | Linked lifecycle record |
| Homework 4 answers derive from real evidence | 6 | `homework-4-evidence.md` | Health, metrics, Grafana, alert, responder, and diagnosis evidence |

## 10. Final Completion Checklist

### Release Behavior

- [ ] DEV receives qualifying changes automatically.
- [ ] PROD remains user-facing and requires manual promotion.
- [ ] PROD promotion reuses the already-built artifact.
- [ ] DEV and PROD can be correlated to the deployed release identity.
- [ ] Existing M3 workflows remain unchanged.

### Observability and Alerting

- [ ] At least one important backend endpoint or user-relevant operation has metrics, traces, and structured logs.
- [ ] Telemetry supports distinction of application/service, environment, and release.
- [ ] Dashboard evidence distinguishes DEV and PROD.
- [ ] Dashboard evidence shows health or user-impacting behavior.
- [ ] At least one alert represents a real user-impacting application failure.
- [ ] Telemetry, dashboard data, and evidence packets do not expose secrets or credentials.

### Incident Response

- [ ] Evidence collection is read-only, allowlisted, bounded, and repeatable.
- [ ] The responder receives only bounded evidence.
- [ ] The responder produces schema-valid structured output.
- [ ] The responder identifies likely cause, confidence, bounded action, or escalation.
- [ ] The responder cannot use arbitrary commands or general production credentials.
- [ ] `autonomy-policy.yaml` defines permitted bounded actions and escalation handling.
- [ ] Authorization is external to model confidence.
- [ ] Unauthorized actions are rejected or escalated.
- [ ] Recovery verification is independent of the responder’s conclusion.
- [ ] Unverified recovery results in escalation.

### Security and Auditability

- [ ] Semgrep scanning is implemented.
- [ ] Model-assisted review is recorded.
- [ ] Human validation and disposition are recorded.
- [ ] Snyk Agent Scan evidence exists for the responder attack surface.
- [ ] Responder capability and credential boundaries are documented.
- [ ] Security findings retain provenance.
- [ ] Incident traceability is reconstructable.

### Homework 4

- [ ] Running-system evidence determines health-check behavior.
- [ ] Running-system evidence determines relevant metric HTTP status.
- [ ] Running-system evidence determines Grafana-observed HTTP status.
- [ ] Running-system evidence determines alert state.
- [ ] Running-system evidence retains the structured responder response.
- [ ] Running-system evidence supports the underlying-problem diagnosis or documented escalation.
- [ ] Homework answers are not hard-coded.
