# Module 4 Product Specification — DevOps and Observability for TaskFlow

## 1. Purpose

Module 4 equips TaskFlow with the minimum operational capabilities needed to safely release changes, observe user-impacting failures, investigate incidents with bounded evidence, authorize limited responses, verify recovery, and retain an auditable record.

The required operational loop is:

> **Change → observe user impact → alert with context → investigate from evidence → authorize a bounded response or escalate → verify recovery → audit the code and response trail**

This specification defines the required product behavior and evidence. It does not prescribe infrastructure topology, cloud resources, CI/CD tooling, telemetry backends, or implementation-specific schemas.

## 2. Product Context

TaskFlow enters Module 4 with the completed Module 3 application as its production baseline.

**Baseline protection requirement:** Existing M3 production behavior and resources must be protected while Module 4 capabilities are introduced. Any decision to share or separate infrastructure resources between DEV, PROD, and the existing M3 baseline is deferred to implementation and must be made explicitly.

The Module 4 product outcome is not a broader SRE platform. It is a minimum operational system that can demonstrate the lifecycle of a real application failure from release through evidence, response, verification, and audit.

## 3. Goals

The Module 4 product must provide the following capabilities:

- Automatically make new changes available in DEV.
- Manually promote a tested release to the user-facing PROD environment.
- Reuse the same already-built release artifact when promoting from DEV to PROD.
- Observe at least one important backend endpoint or user-relevant operation end to end.
- Detect at least one real user-impacting application failure with an alert.
- Collect bounded, repeatable, read-only incident evidence.
- Provide that evidence to a headless AI responder for structured investigation.
- Ensure model reasoning or confidence never independently authorizes execution.
- Permit only explicitly authorized, bounded actions; otherwise escalate.
- Independently verify whether recovery occurred after an action.
- Retain an auditable incident and security-review trail.
- Produce real running-system evidence sufficient to support Homework 4.

## 4. Non-Goals

Module 4 intentionally does not require:

- SLOs, error budgets, or burn-rate alerting.
- Synthetic monitoring, real-user monitoring, or profiling.
- Telemetry sampling, retention, or observability-cost strategy.
- Canary, blue/green, or progressive delivery.
- Feature flags or chaos testing.
- On-call ownership processes, incident command, or blameless postmortems.
- A mandatory AWS architecture, EC2 topology, database topology, or container-orchestration platform.
- SBOMs, artifact signing, build-provenance infrastructure, or penetration testing.
- A general-purpose autonomous production agent.
- A general-purpose production diagnostic shell.

## 5. DEV and PROD Release Behavior

### 5.1 DEV Behavior

DEV must receive new application changes automatically.

DEV serves as the environment in which a newly built release can be deployed and observed before production promotion.

### 5.2 PROD Behavior

PROD is the user-facing environment.

A release must not be automatically promoted to PROD merely because it was deployed to DEV. Production promotion must require an explicit manual approval or trigger.

### 5.3 Artifact Promotion

A PROD promotion must reuse the already-built release artifact that was deployed and tested in DEV.

The product must preserve the ability to identify the deployed release in both environments. It must not require rebuilding a different artifact specifically for PROD.

### 5.4 Deferred Infrastructure Boundary

This specification does not require:

- Separate EC2 instances.
- Separate application stacks.
- Separate databases.
- A particular registry, deployment system, or cloud-resource layout.

The concrete DEV/PROD boundary and any resource-sharing decision will be made during implementation, while preserving the M3 production baseline.

## 6. Observability

### 6.1 End-to-End Coverage

At least one important TaskFlow backend endpoint or user-relevant operation must be instrumented end to end.

The instrumented operation must expose the following signal types:

- **Metrics:** Evidence of application behavior and outcomes, including the relevant HTTP or operation result.
- **Traces:** Evidence that supports following the relevant request or operation through its processing path.
- **Structured logs:** Queryable event records that support investigation of the request, failure, or related operation.

### 6.2 Correlation and Release Context

The instrumented endpoint or service must expose enough correlated telemetry metadata to allow an operator to distinguish:

- The application or service involved.
- The environment, including DEV versus PROD.
- The deployed version or release involved in the incident.

The exact telemetry schema and which individual signal carries each field are implementation decisions.

### 6.3 Secret and Credential Hygiene

Telemetry, incident evidence, dashboards, and AI-responder inputs must not expose secrets or credentials.

## 7. Dashboard

A dashboard must make the minimum operational signals visible for the instrumented endpoint or user-relevant operation.

The dashboard must enable an operator to distinguish:

- DEV from PROD.
- Deployed version or release.
- Application health and user-impacting behavior.

The product does not require a particular dashboard platform, panel layout, visual design, time-range control, variable name, or fixed set of panels.

## 8. User-Impact Alerting

At least one alert must represent a real user-impacting application failure.

A resource-only condition, such as high CPU usage without demonstrated impact on application behavior, does not satisfy this requirement.

The alert must provide sufficient context to begin investigation, including:

- The affected application signal or failure condition.
- Relevant environment context.
- Relevant deployed release context.

The exact alert fields, severity model, ownership metadata, notification destination, and dashboard links are implementation choices unless required by the chosen implementation.

## 9. Bounded Evidence Collection

The system must provide a mechanism to collect incident evidence before AI reasoning or remediation is attempted.

Evidence collection must be:

- **Read-only:** It must not change application, infrastructure, deployment, or data state.
- **Allowlisted:** It may use only predefined permitted queries, checks, or data sources.
- **Bounded:** It must collect only the evidence needed to investigate the alert rather than allowing unrestricted exploration.
- **Repeatable:** The same incident-evidence process can be rerun for a comparable alert condition.
- **Investigation-ready:** It must provide enough information to understand relevant application behavior, telemetry, and deployed version or change context.

The evidence collector must not permit arbitrary production queries, unrestricted shell commands, or general-purpose diagnostic access.

## 10. AI Responder

### 10.1 Role

The AI responder is a system actor that serves as a read-only, headless first responder for alerts.

It receives the bounded evidence packet and produces a structured investigation result through a vendor-neutral structured-output interface or adapter.

The selected model or vendor is an implementation choice and is not a product requirement.

### 10.2 Required Response Capability

The responder’s structured output must enable the system and human reviewer to determine:

- The likely cause or contributing cause of the incident, based on the supplied evidence.
- The responder’s confidence or uncertainty.
- A proposed bounded action when a safe authorized action can be identified.
- Whether escalation is required because the cause, evidence, or safe response cannot be determined.

The responder must remain read-only during investigation. It must not receive general production credentials or arbitrary command-execution capability.

## 11. Authorization and Safety Boundary

The product must maintain a clear separation between model reasoning and authority to act.

**Core safety rule:** Model confidence must not itself grant permission to execute an action.

The system must provide:

- An explicit action allowlist.
- Defined bounded autonomy or authorization conditions.
- An authorization or policy boundary external to the model.
- Rejection or escalation when a requested or proposed action is not authorized.
- A record of the authorization decision and any action actually taken.

The exact autonomy taxonomy, approval workflow, policy engine, action format, and enforcement mechanism are deferred to implementation.

## 12. Recovery Verification

After a remediation action is taken, the system must independently verify whether the intended recovery occurred.

Recovery verification must:

- Evaluate the original affected behavior or user-impact condition.
- Distinguish verified recovery from an unresolved failure.
- Record the verification result.
- Escalate when recovery cannot be verified.

A completed action alone is not evidence of successful recovery.

The verification mechanism and checks are implementation decisions, provided they are independent of the responder’s unsupported assertion that the incident is resolved.

## 13. Security Audit

The product must support recurring security review with the following minimum components:

- **Semgrep scanning:** Deterministic security scanning.
- **Model-assisted review:** Review that can identify or assess findings with contextual assistance.
- **Human validation and disposition:** Human review to validate, reject, prioritize, or otherwise disposition findings.
- **Capability and credential-boundary review:** Review of the responder’s allowed capabilities, accessible credentials, and operational boundaries.
- **Finding provenance:** Records sufficient to identify where a security finding originated and how it was reviewed.
- **Snyk Agent Scan:** Assessment of the AI responder’s attack surface.

The responder must be treated as part of the system attack surface. Its review must account for its capabilities, credentials, tool access, and provenance.

This requirement does not expand into a broader security program or require SBOMs, signing, build-provenance infrastructure, or penetration testing.

## 14. Incident Traceability and Auditability

The system must retain an auditable incident trail that connects, at minimum:

> **Incident → deployed version → user impact → alert → evidence → model/configuration used → proposed action → authorization decision → actual action taken → recovery verification or escalation → security finding/review where applicable → human disposition**

The traceability requirement applies to material incidents handled through the Module 4 operational loop.

The product does not prescribe a storage technology, database design, directory structure, event schema, or incident-management platform. The retained record must simply make the lifecycle reconstructable for review.

## 15. Homework 4 Acceptance Target

Module 4 must make it possible to generate real evidence from the running system for the Homework 4 scenario.

The product must support evidence sufficient to determine:

| Homework evidence area | Required capability |
|---|---|
| Health-check behavior | Determine the actual health-check result from the running system |
| Lookup metric HTTP status | Determine the HTTP status recorded by the relevant application metric |
| Grafana-observed HTTP status | Determine the HTTP status visible through the dashboarded metric |
| Alert state | Determine the state of the relevant user-impacting or 5xx alert |
| Agent response | Retrieve the structured response produced by the AI responder |
| Underlying application problem | Determine the likely root cause or document why escalation was required |

The specification does not hard-code the expected homework answers. The running system, its telemetry, its alert state, and the responder output must generate the evidence needed to answer the homework questions.

## 16. Acceptance Criteria

Module 4 is accepted when all of the following are demonstrable.

### 16.1 Release Behavior

- New changes are automatically deployed or made available in DEV.
- PROD remains user-facing and requires manual promotion.
- PROD promotion reuses the same already-built release artifact rather than rebuilding a different artifact.
- The deployed release can be distinguished between DEV and PROD.

### 16.2 Observability and Alerting

- At least one important backend endpoint or user-relevant operation has metrics, traces, and structured logs.
- The available telemetry supports correlation of application or service, environment, and deployed release for investigation.
- Telemetry does not leak secrets or credentials.
- A dashboard makes environment, deployed release, and application health or user-impacting behavior distinguishable.
- At least one alert represents a real user-impacting application failure and provides sufficient investigation context.

### 16.3 Investigation and AI Response

- Evidence collection is read-only, allowlisted, bounded, repeatable, and sufficient to investigate the alert.
- The AI responder receives bounded evidence rather than unrestricted production access.
- The responder produces structured output through a vendor-neutral interface or adapter.
- The structured output identifies a likely or contributing cause, states confidence or uncertainty, and proposes a bounded action or escalation.

### 16.4 Safety and Recovery

- The system has an explicit action allowlist and an authorization boundary external to the model.
- Model confidence cannot independently authorize execution.
- Unauthorized actions are rejected or escalated.
- Any action actually taken is recorded.
- Recovery is independently verified against the original impact condition.
- Unverified recovery results in escalation.

### 16.5 Security and Auditability

- Recurring Semgrep scanning, model-assisted review, and human validation/disposition are supported.
- Snyk Agent Scan is used to review the responder attack surface.
- The responder’s capability and credential boundaries are reviewed.
- Security findings retain provenance and review status.
- An incident trail can connect the incident lifecycle from deployed version through response, verification or escalation, relevant security review, and human disposition.

### 16.6 Homework 4 Evidence

- The running system can generate evidence sufficient to answer the Homework 4 questions about health-check behavior, HTTP status in metrics and Grafana, alert state, agent response, and the underlying application problem.
- Homework answers are derived from system evidence rather than embedded or hard-coded into the product.

## 17. Requirement Source / Provenance

| Requirement area | Primary source / provenance | Boundary |
|---|---|---|
| DEV automatic updates, PROD manual promotion, reuse of built artifact | Official Module 4 lesson; M3 baseline context | Required product behavior; infrastructure boundary is deferred |
| Preserve M3 baseline while introducing M4 | M3 baseline; explicit project decision | Project constraint |
| One important endpoint with metrics, traces, and structured logs | Official Module 4 lesson | Required minimum observability scope |
| Environment and deployed-release correlation | Official Module 4 lesson; M3 baseline context | Required investigation capability; exact telemetry schema is deferred |
| Secret and credential hygiene in telemetry | Official Module 4 lesson | Required |
| Dashboard showing application-specific operational signals | Official Module 4 lesson; companion article | Dashboard capability is required; dashboard design is deferred |
| One real user-impact alert with useful context | Official Module 4 lesson | Required; alert schema is deferred |
| Read-only, allowlisted, bounded, repeatable evidence | Official Module 4 lesson | Required |
| Read-only headless responder and vendor-neutral structured adapter | Official Module 4 lesson | Required; model and vendor selection are deferred |
| Confidence does not equal permission; allowlist and external authorization | Official Module 4 lesson | Required; autonomy taxonomy and policy mechanism are deferred |
| Independent recovery verification or escalation | Official Module 4 lesson | Required; verification mechanism is deferred |
| Semgrep, model-assisted review, human validation, responder attack-surface review, Snyk Agent Scan | Official Module 4 lesson | Required security-audit minimum |
| Incident lifecycle traceability | Official Module 4 lesson; M3 baseline context | Required; storage technology and schema are deferred |
| Evidence for health check, metrics, Grafana, alert, agent response, and diagnosis | Homework 4 | Required acceptance target; answers are not prescribed |
| AWS, CloudFormation, ECR, Prometheus, Loki, Tempo, and Grafana examples | Companion article and transcript | Implementation examples, not mandatory product requirements |
| Resource-sharing decision between DEV, PROD, and M3 | Explicit project decision | Deferred to implementation; M3 production resources remain protected |
