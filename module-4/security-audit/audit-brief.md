# Module 4 P6-A — Security Audit Brief

## 1. Audit Objective

Conduct a bounded security review of the TaskFlow Module 4 implementation and operational incident-response surface, then produce evidence sufficient for final Module 4 acceptance.

The review is intended to establish whether the implemented controls preserve the following boundary:

```text
bounded evidence
→ structured analysis
→ schema validation
→ external authorization
→ bounded execution or escalation
→ independent recovery verification
→ auditable record
```

The security review must not convert the Module 4 responder into a general-purpose autonomous operator, and it must not redesign the existing TaskFlow architecture.

## 2. Audit Basis

This brief is based on the `ai-dev-tools-zoomcamp` repository at the verified P5 merge baseline:

```text
repository = git@github.com:athing01/ai-dev-tools-zoomcamp.git
branch = main
audit_commit = fba6a3945b0b59069580a2e2df6423f2503eb7eb
HEAD = fba6a3945b0b59069580a2e2df6423f2503eb7eb
origin/main = fba6a3945b0b59069580a2e2df6423f2503eb7eb
working tree = clean
merge = PR #29
```

A repository reference bundle was generated directly from Git at this immutable commit. The bundle records the exact audit paths, SHA-256 source manifest, incident-artifact hashes, workflow inventory, and the diff of the M3 protected workflows.

The Git repository and immutable commit above are the canonical P6-A source reference.

## 3. Bounded Audit Scope

### 3.1 TaskFlow application and M4 operational code

Review the parts of TaskFlow that directly participate in M4 operational behavior, including:

- TaskFlow backend/frontend operational surfaces relevant to P3–P5 behavior.
- M4 deployment and runtime configuration required to execute the incident-response path.
- M4 observability configuration used for incident detection and evidence reconstruction.
- M4 infrastructure/IAM configuration that governs the DEV operational boundary.

The review does not constitute a full application penetration test or broad enterprise security assessment.

### 3.2 Evidence collection controls

Review `collect-evidence.sh` and retained incident evidence for:

- fixed/bounded source queries;
- bounded time windows and payload sizes;
- read-only behavior;
- output minimization and secret exclusion;
- injection/path handling;
- source and incident scoping;
- evidence provenance and reconstruction value.

### 3.3 Responder task and adapter boundary

Review:

- `responder-task.md`;
- `responder.py`;
- `response.schema.json`;
- the mock and OpenAI-compatible adapter boundaries.

The review must determine whether untrusted evidence is treated as data rather than executable instructions and whether the responder can escape its intended incident scope.

### 3.4 Autonomy policy and bounded action handling

Review:

- `autonomy-policy.yaml`;
- `policy-gate.py`;
- `recover-task-list-dev-fault.sh`;
- `verify-recovery.sh`;
- `rollback.sh`.

The review must establish whether:

- deny-by-default behavior is enforceable;
- model confidence is separated from authority;
- only the named allowlisted action can be proposed;
- authorization is external to the model;
- the executor is fixed and bounded;
- execution preconditions are revalidated immediately before mutation;
- production and rollback remain outside the AI action path;
- recovery verification is independent of action execution.

### 3.5 Responder capabilities, tools, and credential boundaries

Review the actual capabilities of:

- the responder process;
- the evidence collector;
- the bounded executor;
- the GitHub Actions workflows that deploy/run M4;
- the M4 DEV EC2 runtime role;
- the responder model adapter configuration.

The review must explicitly document what the responder can read, what tools it can invoke through the surrounding operational system, what credentials exist at each boundary, and what systems are intentionally inaccessible.

## 4. Explicit Audit Exclusions

The following are outside the P6-A audit scope unless a source-derived issue makes them directly relevant:

- General enterprise security posture.
- Full penetration testing.
- SBOM generation/signing programs.
- New authentication/authorization architecture.
- SLO/error-budget programs.
- Chaos engineering or progressive delivery.
- General-purpose autonomous remediation.
- Homework 4 / order-tracker runtime behavior.
- Redesign of the M3 deployment architecture.

The existing M3 protected workflows remain in scope only for preservation verification; they must not be modified as part of P6-A.

## 5. Audit Questions

### A. Evidence collection

1. Can evidence collection be constrained to the intended incident, operation, environment, and time window?
2. Can unbounded queries, arbitrary commands, or arbitrary file reads be introduced through collector inputs?
3. Is evidence size bounded and is sensitive payload minimization enforced?
4. Is evidence provenance sufficient to reconstruct what was observed?

### B. Responder and adapter

1. Can evidence content override or inject instructions into the responder task?
2. Can the adapter be redirected to an unintended external endpoint through configuration or input?
3. Can the responder emit executable commands, credentials, or arbitrary action parameters?
4. Is schema validation enforced before any policy or authorization decision?
5. Are semantic checks stricter than the model's free-form output?
6. Are adapter failures handled without partial authorization or execution?

### C. Policy and execution

1. Is the allowlist deny-by-default?
2. Can an unlisted action reach an executor?
3. Can a valid action ID be executed outside DEV or outside `tasks.list` scope?
4. Are runtime preconditions independently revalidated immediately before mutation?
5. Can the executor alter services, images, runtime variables, databases, release state, or artifacts outside its declared effect set?
6. Can a responder trigger rollback or production activity indirectly?
7. Is recovery verification independent from the mutation mechanism?

### D. Credentials and infrastructure

1. Are responder credentials isolated from the responder's output and evidence records?
2. Is the responder endpoint configuration sufficiently constrained and auditable?
3. Are GitHub OIDC trust relationships and repository/environment boundaries consistent with the intended deployment roles?
4. Are M4 DEV and PROD IAM scopes appropriately separated?
5. Are wildcard resource permissions justified and minimized?
6. Can workflow input or untrusted repository content reach privileged shell/SSM commands without adequate validation?

## 6. Required Audit Methods

### 6.1 Semgrep

Run the required Semgrep scan against the bounded TaskFlow/M4 source scope defined by this brief. Retain:

- scanner version;
- rule/configuration reference;
- commit/release identity scanned;
- command/configuration used;
- raw result;
- normalized finding records where applicable;
- scan timestamp.

The raw scanner output is evidence, not a confirmed finding.

### 6.2 Snyk Agent Scan

Run Snyk Agent Scan against the responder attack surface, including the responder task/adapter/tool boundary and relevant agent/tool configuration.

Retain:

- scanner/version information;
- exact target/source scope;
- configuration/skills or scan mode used;
- raw output;
- finding provenance;
- review and disposition linkage.

The raw scan is evidence, not a confirmed finding.

### 6.3 Model-assisted review

Use a bounded model-assisted review only as an analysis aid over:

- the audit inventory;
- scanner outputs;
- responder/policy configuration;
- relevant workflow/IAM excerpts;
- material P5 incident artifacts.

The model must not be treated as an authority source and must not execute changes.

The model-assisted review record must identify:

- model/provider/configuration reference;
- review input set;
- questions or review rubric;
- resulting candidate findings/observations;
- uncertainty or limitations.

### 6.4 Human validation and disposition

Every candidate finding must receive an explicit human disposition before it is presented as a confirmed finding.

Permitted dispositions should distinguish at least:

- confirmed — remediate;
- confirmed — accepted risk;
- false positive / not applicable;
- informational observation;
- requires further evidence.

A finding is not complete until its provenance and disposition are retained.

## 7. Finding Evidence Requirements

Each finding record must be traceable to:

```text
finding ID
→ origin/tool
→ scanner/model version
→ source/configuration reference
→ supporting evidence
→ review status
→ human disposition
→ remediation status, where applicable
```

The eventual `findings.schema.json` must enforce these provenance fields.

## 8. Initial Audit Attention Areas

The following are deliberate review targets derived from the supplied implementation. They are **not pre-declared findings**:

1. Boundedness and injection resistance of evidence collection.
2. OpenAI-compatible adapter destination and credential boundary.
3. Semantic enforcement between model output, policy gate, authorization, and executor.
4. Docker/Compose capability available to the fixed DEV executor.
5. GitHub `workflow_run` and OIDC privilege boundaries.
6. DEV/PROD IAM separation.
7. Least-privilege treatment of M4 EC2 SSM, KMS, ECR, S3, and logging permissions.
8. Protection against secret disclosure through logs, error paths, incident artifacts, or model provenance.
9. Independence and integrity of recovery verification.
10. Preservation of M3 protected workflows during P6-A.

## 9. Required Audit Evidence Layout

The P6-A audit evidence should resolve to:

```text
module-4/security-audit/
├── audit-brief.md
├── findings.schema.json
├── capability-table.md
└── runs/
    ├── inventory.md
    ├── semgrep.*
    ├── snyk-agent-scan.*
    ├── model-assisted-review.*
    └── human-disposition.*
```

The exact file extensions may follow the tool output format, but the run records must preserve reproducibility and provenance.

## 10. Acceptance Criteria for the Security Review

P6-A security review is acceptable only when:

- the bounded audit scope is complete;
- required Semgrep evidence exists;
- required Snyk Agent Scan evidence exists;
- model-assisted review is retained and clearly identified as advisory;
- all candidate findings have human validation/disposition;
- responder capability and credential boundaries are documented;
- findings have provenance sufficient for reconstruction;
- no unreviewed scanner/model output is presented as a confirmed finding.

This security-review acceptance is one input to, not a substitute for, the broader P6-A final acceptance gate.

## 11. Known Limitations at Audit Start

1. The repository reference bundle is a derived evidence bundle and does not include `.git` metadata; Git provenance was independently verified from the repository at audit start.
2. Runtime AWS/GitHub environment state is not established by source inspection alone.
3. IAM role trust policies referenced by workflows are not fully represented by the supplied workflow files; CloudFormation/runtime IAM evidence is required.
4. No P6 security-audit artifacts are present yet in the supplied P5 snapshot.
5. Scanner results have not yet been executed and therefore no security finding is asserted by this brief.

## 12. Audit Principle

```text
Source observation != confirmed finding
Scanner output  != confirmed finding
Model output    != authority

Evidence
→ validation
→ human disposition
→ accepted finding / observation
```
