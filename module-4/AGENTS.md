# AGENTS.md — TaskFlow Module 4 (`module-4/`)

## 1. Scope and Authority

This file governs work under `module-4/` and is subordinate to any repository-level instructions.

Module 4 implementation authority is:

1. `module-4/docs/product-spec.md`
2. Official Module 4 lesson
3. Homework 4 requirements
4. Module 4 transcript
5. Companion article
6. Module 3 baseline and implementation context
7. Explicit project decisions recorded during implementation
8. This file for day-to-day implementation rules

The Product Specification defines required product behavior. The implementation plan translates that behavior into phases. Do not promote an implementation detail into a product requirement without evidence from a higher-priority source or an explicit project decision.

## 2. Project Working Rules

- Work incrementally by phase.
- **1 phase = 1 branch = 1 pull request.**
- Prefer evidence, tests, diffs, and real command output over assumptions.
- Keep changes inside the current phase scope.
- Do not redesign architecture unless the current implementation is demonstrably unable to satisfy an approved requirement.
- When a requirement is already clear, implement it rather than reopening settled design decisions.
- Keep deferred implementation decisions explicit until the phase that owns them.

## 3. Module 3 Baseline Is Protected

Module 4 extends the completed Module 3 TaskFlow baseline.

Do not silently change or redesign the M3 production system.

These M3 workflows are protected and must remain untouched by normal M4 work:

```text
.github/workflows/ci.yml
.github/workflows/deploy.yml
```

Do not modify the completed M3 CloudFormation stack merely to introduce M4 behavior.

Existing M3 application, deployment, artifact, secret-handling, and controlled-execution patterns may be reused where they are compatible with M4 requirements.

Reuse does not imply that every M3 resource must be shared with M4. DEV/PROD resource boundaries and sharing decisions must remain explicit implementation decisions.

Do not change M3 production endpoints, DNS/HTTPS behavior, or production release behavior unless a later implementation decision explicitly requires and authorizes it.

## 4. Minimum Module 4 Scope

Implement only the approved minimum operational loop:

```text
Change
→ observe user impact
→ alert with context
→ investigate from evidence
→ authorize a bounded response or escalate
→ verify recovery
→ audit the code and response trail
```

Minimum capabilities:

- Automatic DEV availability/deployment for the M4 release path.
- Manual PROD promotion.
- Promotion of the same already-built immutable artifact from DEV to PROD.
- End-to-end observability for one important backend endpoint or user-relevant operation.
- Metrics, traces, and structured logs.
- A dashboard showing operational/user-impact signals.
- At least one real user-impacting application alert.
- Bounded, repeatable, read-only incident evidence collection.
- A headless, read-only AI responder with structured output.
- A vendor-neutral responder adapter boundary.
- External authorization separate from model confidence.
- Only explicitly permitted, bounded actions; otherwise escalation.
- Independent recovery verification.
- Security review with Semgrep, model-assisted review, human validation/disposition, capability/credential review, and Snyk Agent Scan.
- Running-system evidence sufficient for Homework 4.
- An auditable incident/security-review trail.

## 5. Explicit Non-Goals

Do not add the following as mandatory M4 scope:

- SLOs, error budgets, or burn-rate alerting.
- Synthetic monitoring, RUM, profiling, or observability-cost programs.
- Canary, blue/green, progressive delivery, feature flags, or chaos engineering.
- A mandatory separate DEV database, EC2 instance, application stack, or AWS topology.
- Rebuilding a different artifact for PROD.
- General-purpose autonomous remediation.
- Arbitrary production shell access or unrestricted diagnostic queries.
- SBOMs, artifact signing, penetration testing, or a broader security program.
- A new M3 readiness endpoint.
- Hard-coded Homework 4 answers.

## 6. Required Repository Paths and Filenames

When implementing the Module 4 lesson deliverables, use these exact paths and names. Do not substitute near-equivalent filenames.

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
├── docs/
│   ├── product-spec.md
│   ├── operations-and-security-report.md
│   ├── homework-4-evidence.md
│   └── acceptance-traceability-matrix.md
└── implementation-plan.md
```

Module 4 GitHub workflow files live at repository root and use these exact names:

```text
.github/workflows/ci-module-4.yml
.github/workflows/deploy-module-4.yml
.github/workflows/promote-module-4.yml
```

Do not create alternative M4 workflow names merely for convenience.

## 7. Phase Boundaries

Implementation begins at Phase 3 because Phase 0–2 are already completed project phases.

### Phase 3 — Release Behavior and Operational Identity

Focus on:

- Automatic DEV release behavior.
- Manual PROD promotion.
- Build once / promote the same immutable artifact.
- Release identity and traceability.
- Protection of M3 workflows and production baseline.

Do not lock a specific GitHub trigger mechanism unless the phase's evidence requires it and the decision is explicitly made.

### Phase 4 — Observability, Dashboard, and User-Impact Alert

Focus on one important endpoint or user-relevant operation and provide:

- Metrics.
- Traces.
- Structured logs.
- Correlation to service/application, environment, and deployed release.
- Dashboard visibility.
- One real user-impacting alert.
- Secret/credential hygiene.

Use the exact required files in `module-4/observability/`.

### Phase 5 — Bounded Evidence, AI Responder, Authorization, and Recovery Verification

Focus on:

- Read-only, allowlisted, bounded, repeatable evidence collection.
- Structured responder output validated against `response.schema.json`.
- Vendor-neutral adapter boundary.
- External authorization through `autonomy-policy.yaml`.
- Bounded action execution only.
- Escalation when evidence or authorization is insufficient.
- Independent recovery verification.

The responder is a system actor, not an authority source.

### Phase 6 — Security Audit, Homework Evidence, and Final Acceptance

Focus on:

- Semgrep.
- Snyk Agent Scan for the responder attack surface.
- Model-assisted review.
- Human validation/disposition.
- Capability and credential boundary review.
- Finding provenance.
- Homework 4 evidence from the running system.
- Final incident/security traceability.

Keep Phase 6 combined. Do not split it into extra phases without an explicit project decision.

## 8. Observability Rules

Instrument only the minimum important operation needed to satisfy the requirement before expanding coverage.

Telemetry must not expose:

- passwords
- API keys
- tokens
- database credentials
- connection strings containing secrets
- other secret material

Do not assume that a resource-level signal such as high CPU is sufficient for the user-impact alert. The alert must represent a real application/user-impacting failure.

The exact telemetry backend, dashboard layout, alert threshold, routing, and schema are implementation decisions unless required by a higher-priority source.

## 9. Incident Evidence Rules

Evidence collection must be:

- Read-only.
- Allowlisted.
- Bounded.
- Repeatable.
- Investigation-ready.

Do not allow arbitrary production queries, arbitrary shell commands, unrestricted log retrieval, or general-purpose diagnostic access.

Evidence should be limited by the relevant incident context, including the affected operation, environment, time window, and deployed release where available.

Evidence must be collected before AI reasoning or remediation is attempted.

## 10. AI Responder Safety Rules

The responder must receive only the bounded evidence packet.

The responder must not receive general production credentials or arbitrary command-execution capability.

Structured responder output must be validated before it reaches authorization handling.

At minimum, the response must make the following reconstructable:

- incident identifier
- evidence considered
- likely/contributing cause
- confidence or uncertainty
- proposed bounded action, where applicable
- escalation decision
- rationale
- missing evidence, where applicable

Model confidence, recommendation, or free-form output never grants permission to execute an action.

Authorization must occur outside the model.

## 11. Recovery Rules

An action attempt is not proof of recovery.

After an authorized action, independently evaluate the original affected operation or user-impact condition.

The result must distinguish among:

- verified recovery
- unresolved failure
- inconclusive result requiring escalation

Rollback, when used, must be a bounded authorized procedure using a known prior release artifact rather than rebuilding source.

## 12. Homework 4 Rules

Homework 4 answers must be derived from evidence generated by the running system.

Do not hard-code expected answers into application behavior, evidence scripts, dashboards, alerts, or documentation.

Do not automatically equate the M3 readiness behavior with the Homework 4 health-check requirement unless authoritative course material explicitly establishes that relationship.

Evidence must be sufficient to determine the actual:

- health-check behavior
- relevant metric HTTP status
- Grafana-observed HTTP status
- alert state
- AI responder structured response
- underlying application problem or documented escalation

## 13. Security and Audit Rules

Security findings must retain provenance sufficient to identify their source and review path.

Raw scanner or model output is not a confirmed security finding until human validation/disposition is recorded.

The responder's capabilities, tools, credential access, prohibited access, and external authorization boundary must be documented.

The material incident trail must be reconstructable as:

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

## 14. Documentation Rules

Keep these documents aligned with the implementation:

- `module-4/docs/product-spec.md` — approved product requirements.
- `module-4/implementation-plan.md` — implementation phases, scope, gates, and deferred decisions.
- `module-4/docs/operations-and-security-report.md` — operational and security audit trail.
- `module-4/docs/homework-4-evidence.md` — live evidence for Homework 4.
- `module-4/docs/acceptance-traceability-matrix.md` — requirement-to-evidence mapping.

Do not silently change the Product Specification to make implementation easier. Resolve conflicts by following the authority order above.

## 15. Testing and Verification

Before completing a phase:

1. Run the most relevant automated tests and lint/check commands already established by the repository.
2. Validate changed configuration and scripts with the appropriate parser/linter when available.
3. Prefer integration or running-system verification for operational behavior that cannot be proven by static tests.
4. Inspect the final diff for accidental M3 changes.
5. Record evidence for the phase exit gate.

Do not claim an operational capability is working based only on configuration existence. Verify the behavior in the target environment where the phase requires runtime evidence.

## 16. Git and Change Discipline

Keep each phase in its own branch and pull request.

Before committing:

```bash
git diff --check
git status --short
git diff --cached --check
```

Review the staged diff for:

- unintended M3 changes
- secrets or credentials
- generated artifacts that should not be committed
- scope creep
- inconsistent filenames or workflow references

Use focused commits that describe the actual phase work.

## 17. Definition of Done for an M4 Change

An M4 change is ready to merge only when:

- It satisfies the applicable Product Specification and implementation-plan requirement.
- It stays within the current phase scope.
- Required tests/checks pass or a documented limitation explains why they cannot.
- Runtime behavior is verified where required.
- No protected M3 workflow was modified accidentally.
- No secrets or credentials are exposed.
- Evidence needed for the phase exit gate is available.
- Documentation and traceability references use the exact required filenames.
