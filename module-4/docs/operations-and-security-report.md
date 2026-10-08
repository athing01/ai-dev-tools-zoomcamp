# Operations and Security Report

## Operations

### Operational Model

Module 4 operational response follows a bounded, evidence-first loop:

```text
Change
→ observe user impact
→ alert with context
→ collect bounded read-only evidence
→ structured AI assessment
→ schema validation
→ external authorization
→ bounded action or escalation
→ independent recovery verification
→ audit record
```

The responder is an analysis component, not an execution authority. Model confidence, free-form model output, and responder recommendations do not grant permission to mutate the runtime. Authorization is enforced outside the model, and any bounded action is implemented by a fixed executor whose scope and preconditions are independently revalidated before mutation.

P5 applies this model to the TaskFlow `tasks.list` operation in the DEV environment. The implemented allowlisted recovery action is:

```text
recover_task_list_dev_fault
```

The action is limited to the TaskFlow DEV backend runtime and is not available for production operations.

### Release and Operational Identity

Module 4 operational evidence is linked to an immutable release identity. The P5 final incident record is associated with release SHA:

```text
cfc5189ffe74e63510b5f041bf38e9b933c5ea9a
```

The P5 implementation was subsequently merged through pull request `#29`:

```text
implementation commit = 8de1a6f
merge commit           = fba6a39
```

The merged release was deployed to the M4 DEV environment and smoke-tested successfully.

Operational release identity is preserved through the existing M4 release-manifest and deployment mechanisms. Application rollback remains an operational concern separate from the P5 AI incident-response action path; the P5 incident loop does not allow the responder to trigger rollback.

### Material Incident

The material P5 incident is:

```text
incident_id = p5-taskflow-final-20261006-053711
operation   = tasks.list
environment = dev
alert_uid   = taskflow-p4-tasks-list-failure
```

The affected user operation was:

```text
GET /api/tasks
```

The observed failure produced an HTTP 503 response. The collected evidence correlated application behavior, metrics, structured logs, and traces to the same operational context.

The evidence packet records:

- application HTTP 503 behavior for `GET /api/tasks`;
- error telemetry for the `tasks.list` operation;
- structured failure logging identifying the controlled P4 fault;
- a correlated `tasks.list` trace;
- DEV environment context;
- release identity;
- alert context for the affected operation.

The final bounded evidence packet is retained at:

```text
module-4/incident-response/incidents/p5-taskflow-final-20261006-053711/evidence.json
```

### Responder Assessment

The structured responder assessment was produced using:

```text
model      = gpt-oss:20b
provider   = litellm
adapter    = openai-compatible-v1
configuration_ref = local-litellm-gpt-oss:20b
```

The responder determined that the evidence supported a controlled fault affecting `tasks.list`, but the bounded evidence packet did not establish the exact runtime precondition:

```text
TASKFLOW_P4_FAULT_MODE=list_fail
```

Therefore the responder did not propose the allowlisted recovery action.

The recorded assessment was:

```text
confidence      = medium
proposed_action = null
escalation      = escalate
```

The responder explicitly treated the missing fault-mode signal as uncertainty rather than inferring it from the expected incident scenario.

### Authorization and Response Decision

The responder output passed the structured response boundary but did not itself authorize execution.

The P5 authorization record therefore records:

```text
decision            = not_authorized
action_authorized  = false
execution_permitted = false
```

The resulting response path was:

```text
bounded assessment
→ external authorization not granted
→ escalation without execution
```

No P5 runtime mutation was performed for this incident.

The authorization decision is retained at:

```text
module-4/incident-response/incidents/p5-taskflow-final-20261006-053711/authorization-decision.json
```

### Recovery Verification

Recovery is treated as an independent verification step rather than an implication of responder success or action execution.

The P5 verification checked the original user-impacting operation:

```text
GET https://dev-api.zctaskflow.athing.cc/api/tasks
```

The recorded result was:

```text
result           = verified
http_status      = 200
json_array       = true
mutation_performed = false
```

The verification therefore established that the current TaskFlow DEV operation was healthy while explicitly recording that no P5 recovery action had been executed.

The verification record is retained at:

```text
module-4/incident-response/incidents/p5-taskflow-final-20261006-053711/recovery-verification.json
```

The operational rule is:

```text
Action attempted
    !=
Recovery verified
```

### Bounded Recovery and Rollback Boundaries

The P5 automated-response path is intentionally narrow.

The only allowlisted mutation is:

```text
recover_task_list_dev_fault
```

Its permitted effect is limited to changing the DEV controlled-fault mode from `list_fail` to `off` and recreating the backend service. The executor revalidates all required execution preconditions immediately before mutation.

The P5 responder cannot:

- execute arbitrary shell commands;
- access production;
- request production credentials;
- modify arbitrary files or configuration;
- perform database operations;
- invoke deployment tooling;
- trigger rollback;
- reinterpret authorization policy.

Application rollback is implemented as a separate manually authorized operational runbook. It reuses existing immutable release artifacts and the established M4 deployment engine rather than becoming an AI-controlled action.

### Auditability

The material incident can be reconstructed from the following records:

```text
incident-record.json
    ↓
evidence.json
    ↓
responder-response-ai.json
    ↓
authorization-decision.json
    ↓
recovery-verification.json
```

The incident record preserves the relationship between:

```text
incident
→ deployed release
→ user impact
→ alert
→ bounded evidence
→ responder model/configuration
→ assessment
→ authorization decision
→ execution disposition
→ independent recovery verification
```

The complete P5 incident record is:

```text
module-4/incident-response/incidents/p5-taskflow-final-20261006-053711/incident-record.json
```

### Operational Limitations

The P5 implementation demonstrates bounded incident response for the selected TaskFlow DEV scenario. It does not establish a general-purpose autonomous remediation system.

## Security Review

### Audit Scope and Method

P6-A security review covers the TaskFlow Module 4 application and operational surface, evidence collection controls, responder task and adapter boundary, bounded autonomy policy and execution path, responder capabilities and credential boundaries, GitHub workflow trust boundaries, and the protection of the M3 baseline.

The canonical source baseline for the review is:

```text
repository = ai-dev-tools-zoomcamp
audit_commit = fba6a3945b0b59069580a2e2df6423f2503eb7eb
```

The P5 incident runtime identity remains distinct:

```text
incident release_sha = cfc5189ffe74e63510b5f041bf38e9b933c5ea9a
```

Scanner/model output is treated as evidence only. Human validation and disposition are required before an observation is represented as a confirmed finding.

### Semgrep Review

The baseline Semgrep run used:

```text
Semgrep = 1.179.0
scope   = module-4 .github/workflows
results = 39
severity = WARNING 37, MEDIUM 2
parser/partial-parsing records = 9
```

The 39 observations were normalized into six review groups. The parser/partial-parsing records are retained as scanner coverage limitations rather than findings.

Two actionable groups were remediated during P6-A:

```text
M4 mutable GitHub Actions references
→ pinned to verified full commit SHAs
→ final m4_mutable_action_results = 0

uv dependency cooldown
→ exclude-newer = "7 days"
→ final uv_cooldown_results = 0
```

The final verification scan was run against remediation checkpoint:

```text
7906eb5fbe3c75bb967926e048b28d4cbf912931
```

Final evidence identity:

```text
semgrep.json
  sha256 = 5e315c008f13f7e55d98689e2373b91b66af8bad40852d814fd06c01733bf695

run-metadata.txt
  sha256 = b48e659d64f8627ec675e3944ebbf727e7282ec6952f35779d08f4bb41ed28c8
```

The retained final scan completed successfully with exit code `0`, 19 remaining observations, 18 WARNING and 1 MEDIUM. No M4 mutable-action or uv cooldown observation remained.

The earlier uv remediation verification is also retained:

```text
semgrep.json
  sha256 = 9f14c0c8cb6d06558f3e497711c66308cd27c52ca5f33047ac178661b7d55185

run-metadata.txt
  sha256 = bde294368bfed77c2cddf8cec271d398aee9cdbab3b26e1059281bd33adb0120
```

### Snyk Agent Scan Limitation

Snyk Agent Scan was attempted against the responder task surface:

```text
module-4/incident-response/responder-task.md
```

The direct CLI result did not complete analysis successfully. A byte-identical fixture was also attempted, but the service returned an HTTP 429 daily usage-limit error before risk analysis completed. The Snyk Web Skill Inspector upload likewise reported that analysis could not be completed.

These results are retained as scanner limitations/inconclusive evidence. They are not represented as a clean scan and are not converted into a zero-risk conclusion. No production responder artifact was modified to accommodate the scanner.

### Human Validation and Structured Findings

Human review recorded explicit dispositions for all six grouped Semgrep observations. The normalized structured finding records are:

```text
M4-P6A-001  M4 mutable GitHub Actions         confirmed-remediate      remediated
M4-P6A-002  M3 inherited mutable Actions      informational-observation not-required
M4-P6A-003  workflow_run checkout              false-positive-not-applicable not-required
M4-P6A-004  Bun release age                    confirmed-accepted-risk  not-required
M4-P6A-005  uv dependency cooldown             confirmed-remediate      remediated
M4-P6A-006  responder dynamic URL              false-positive-not-applicable not-required
```

The structured records are retained under:

```text
module-4/security-audit/runs/findings/
```

and validate against:

```text
module-4/security-audit/findings.schema.json
```

The human disposition worksheet is retained at:

```text
module-4/security-audit/runs/human-disposition.md
```

The two remediation findings preserve their original `remediate` disposition and record the later verification as `remediated`.

### Security Review Conclusion

The P6-A security review found two actionable hardening gaps within scope and verified both remediations. The remaining observations are either inherited from the protected M3 baseline, false positives under the reviewed configuration, or an explicitly accepted hardening gap.

The review does not establish a general absence of security risk. Its conclusion is bounded by the audited source revision, reviewed runtime configuration, scanner coverage limitations, and explicit human dispositions.

## Final P6-A Acceptance

The material TaskFlow operational and security trail is now reconstructable through:

```text
release identity
→ P5 incident
→ alert
→ bounded evidence
→ responder configuration and assessment
→ external authorization decision
→ execution disposition
→ independent recovery verification
→ scanner evidence
→ structured findings
→ human disposition
→ remediation verification
```

P6-A acceptance is therefore based on evidence-backed completion of the TaskFlow security-review artifacts, operational report, incident/security traceability, and final review dispositions. Homework 4 remains a separate P6-B workstream and is not part of the TaskFlow runtime acceptance decision.
