# Module 4 P6-A — Capability and Credential Boundary Table

## Purpose

This table documents the capabilities that exist around the TaskFlow Module 4 incident-response path and separates:

```text
responder analysis capability
≠
operational execution capability
≠
deployment capability
≠
production capability
```

The table is an audit baseline derived from the supplied P5 implementation snapshot. It records observed boundaries and questions to verify; it does not by itself establish that every boundary is secure.

## 1. Capability Boundary Matrix

| Component / identity | Can read / receive | Can invoke / control | Explicitly cannot / intended boundary | Audit evidence required |
|---|---|---|---|---|
| `responder.py` | Bounded JSON evidence packet; responder task; environment/model configuration supplied to the process | Structured analysis through the configured responder adapter | No direct shell execution; no direct Docker control; no direct authorization authority; no production action path | Source review; runtime invocation evidence; process environment review |
| Mock responder adapter | Bounded incident evidence and task prompt | Produces structured response for conservative local testing | Does not infer missing fault-mode evidence; does not authorize or execute | Source review + test evidence |
| OpenAI-compatible adapter | Responder task, bounded evidence, `RESPONDER_MODEL`; API credential from `RESPONDER_API_KEY`; endpoint from `RESPONDER_BASE_URL` | Outbound HTTPS request to configured responder endpoint | Does not itself authorize an action or run commands | Source review; configuration/secret injection evidence; endpoint-control review |
| Evidence collector | Fixed TaskFlow DEV incident identifiers, release SHA, bounded time window, alert state; telemetry endpoints through local LGTM container | Read-only telemetry queries; application check used for evidence; Docker read operations needed to reach telemetry | No application mutation; no arbitrary command supplied through incident inputs | Collector source; command traces; artifact review; bounded-input tests |
| `response.schema.json` boundary | Responder output | Defines structured response contract | Does not authorize execution or supply command text | Schema validation evidence |
| `policy-gate.py` | Incident metadata, responder response, policy | Produces authorization-required / escalation decision record | Does not itself execute the recovery action; model confidence is not authority | Policy-gate test evidence; source review |
| `autonomy-policy.yaml` | Fixed policy configuration | Declares deny-by-default behavior and the single allowlisted action | Production action denied; arbitrary actions denied; rollback outside AI allowlist | Policy file + policy-gate verification |
| `recover-task-list-dev-fault.sh` | Human authorization JSON and fixed runtime state | Fixed Docker/Compose operations against the DEV backend; changes only the controlled fault mode and recreates backend | No arbitrary command payload; no production target; no database operation; no deployment tooling; no rollback | Source review; executor dry-run/tests; runtime execution artifact if authorized |
| `verify-recovery.sh` | Public TaskFlow DEV `GET /api/tasks` response | Performs independent HTTP verification | Does not mutate runtime; must not treat action attempt as recovery proof | Source + verification record |
| `rollback.sh` | Existing immutable release/deployment inputs | Manual rollback procedure through established deployment engine | Not available through P5 AI action allowlist; not an autonomous responder capability | Runbook review + authorization boundary evidence |

## 2. Credential Boundary Matrix

| Credential / identity | Where used | Intended authority | Prohibited use / audit question | Evidence required |
|---|---|---|---|---|
| `RESPONDER_API_KEY` | OpenAI-compatible responder adapter process | Authenticate the responder request to its configured model endpoint | Must not appear in evidence packets, structured response, incident artifacts, logs, or model-visible output | Secret injection path; log/error review; artifact scan |
| `RESPONDER_BASE_URL` | Responder adapter | Select responder endpoint | Verify whether endpoint can be redirected to an unintended destination by untrusted input or environment mutation | Configuration provenance; endpoint validation evidence |
| GitHub OIDC identity for M4 CI | `.github/workflows/ci-module-4.yml` | Obtain the M4 CI AWS role | Must not be usable to obtain M4 PROD promotion privileges | Workflow permissions + IAM trust-policy evidence |
| GitHub OIDC identity for M4 DEV deploy | `.github/workflows/deploy-module-4.yml` | Deploy M4 DEV and invoke intended DEV SSM operations | Must not obtain production role or arbitrary account privileges | Workflow + role trust/policy evidence |
| GitHub OIDC identity for M4 PROD promote | `.github/workflows/promote-module-4.yml` | Manually authorized DEV→PROD promotion | Must remain separated from automatic DEV deployment and responder action path | Environment/protection + role trust/policy evidence |
| M4 DEV EC2 instance role | M4 DEV runtime | Read required SSM/ECR/S3/KMS/log resources needed by application deployment/runtime | Must not become responder production authority; wildcard resources require least-privilege review | CloudFormation/IAM evidence; policy simulation or equivalent review |

## 3. Responder-to-Executor Trust Chain

The intended trust chain is:

```text
alert
  ↓
bounded evidence
  ↓
responder analysis
  ↓
structured response validation
  ↓
external/manual authorization
  ↓
fixed allowlisted executor
  ↓
independent recovery verification
```

The following transitions are intentionally **not** trusted:

```text
model confidence → authorization
free-form model text → shell command
responder output → production access
P5 AI loop → rollback
action attempt → recovery proof
```

## 4. Capability Separation Required for P6-A Acceptance

P6-A should not be accepted until evidence supports all of the following:

- The responder cannot execute arbitrary shell commands through its normal analysis interface.
- The responder cannot select an arbitrary action identifier or arbitrary action parameters that reach the executor.
- The responder cannot authorize its own proposed action.
- The single allowlisted action is constrained to TaskFlow DEV and `tasks.list` scope.
- The executor revalidates authorization, environment, alert, operation, and runtime preconditions immediately before mutation.
- The executor does not obtain production credentials or invoke the rollback runbook.
- Recovery verification is a separate operation and its result records whether mutation actually occurred.
- Responder/API credentials are not copied into incident evidence or response records.
- GitHub M4 workflow roles remain separated from the responder action path.
- M3 protected workflows remain unchanged.

## 5. Known Audit Questions — Not Findings

The following remain questions until evidence and human disposition exist:

1. Whether the responder adapter's configurable endpoint is sufficiently constrained to prevent unintended destination selection.
2. Whether the responder API credential can leak through adapter errors, logs, environment capture, or retained artifacts.
3. Whether Docker/Compose privileges available to the fixed executor exceed the declared recovery effect set.
4. Whether M4 EC2 `kms:Decrypt` wildcard resource scope is appropriately constrained by the service condition and runtime need.
5. Whether GitHub `workflow_run` and OIDC trust boundaries fully prevent untrusted workflow content from inheriting privileged AWS access.
6. Whether workflow/SSM command construction has any path from untrusted repository content to privileged runtime mutation.

These questions must not be pre-labeled as vulnerabilities. Scanner output, source review, and human disposition determine the final status.

## 6. P5 Boundary Reminder

The P5 incident under review recorded:

```text
proposed_action     = null
action_authorized   = false
execution_permitted = false
mutation_performed  = false
recovery            = verified
```

This table therefore must not describe the material P5 incident as an AI-performed recovery. The current-state verification was independent of any P5 mutation.
