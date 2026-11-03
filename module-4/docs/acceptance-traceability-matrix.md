# Module 4 P6-A — Acceptance Traceability Matrix

## Purpose

This matrix maps the approved Module 4 product requirements to the implemented TaskFlow capability and the evidence retained during P3–P6-A.

The matrix is an acceptance aid, not a replacement for the underlying evidence. A requirement is marked accepted only where the cited implementation and evidence together support the claim.

## 1. Traceability

| ID | Product requirement | Implementation / control | Evidence | Status |
|---|---|---|---|---|
| PS-01 | New changes become available in DEV automatically. | M4 DEV release/deployment workflow and deployment runtime. | `.github/workflows/ci-module-4.yml`; `.github/workflows/deploy-module-4.yml`; `module-4/docs/deployment.md`; `module-4/docs/release-process.md`; [M4 CI #36](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41619409483); [DEV #34](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41619655181) | Accepted |
| PS-02 | PROD promotion requires an explicit manual promotion boundary. | Separate M4 promotion workflow with explicit production promotion path. | `.github/workflows/promote-module-4.yml`; `module-4/docs/deployment.md`; [PROD promotion #2](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41623688998) | Accepted |
| PS-03 | PROD reuses the same already-built release artifact rather than rebuilding. | Release manifest and exact image-digest promotion model. | `module-4/docs/release-process.md`; M4 promotion workflow; [CI #36](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41619409483); [PROD promotion #2](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41623688998) | Accepted |
| PS-04 | The deployed release remains identifiable in the operational trail. | Release SHA and release-state/manifest linkage. | `module-4/docs/release-process.md`; P5 incident record; [CI #36](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41619409483); [DEV #34](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41619655181); [PROD promotion #2](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41623688998); `module-4/incident-response/incidents/p5-taskflow-final-20261006-053711/incident-record.json` | Accepted |
| PS-05 | At least one important operation is observed end to end with metrics, traces, and structured logs. | `GET /api/tasks` / `tasks.list` instrumentation and telemetry stack. | `module-4/observability/collector.yaml`; `module-4/observability/dashboard.json`; `module-4/observability/alerts.yaml`; P5 incident evidence | Accepted |
| PS-06 | A real user-impacting application failure produces an actionable alert. | `tasks.list` failure alert for the controlled DEV fault. | `module-4/observability/alerts.yaml`; alert UID `taskflow-p4-tasks-list-failure`; P5 incident record/evidence | Accepted |
| PS-07 | Incident evidence is bounded, read-only, repeatable, and investigation-ready. | Fixed evidence collection script and bounded incident packet. | `module-4/incident-response/collect-evidence.sh`; `module-4/incident-response/incidents/p5-taskflow-final-20261006-053711/evidence.json` | Accepted |
| PS-08 | The bounded evidence is supplied to a headless AI responder with structured output. | Responder task, adapter, and response schema boundary. | `module-4/incident-response/responder-task.md`; `module-4/incident-response/response.schema.json`; `responder-response-ai.json` | Accepted |
| PS-09 | Model confidence or recommendation never independently authorizes execution. | External authorization and policy-gate boundary. | `module-4/incident-response/autonomy-policy.yaml`; `authorization-decision.json`; P5 incident record | Accepted |
| PS-10 | Only explicitly permitted bounded actions may execute; otherwise escalate. | Single DEV allowlisted action `recover_task_list_dev_fault`; deny-by-default policy. | `module-4/incident-response/autonomy-policy.yaml`; `module-4/incident-response/runbooks/`; P5 authorization record | Accepted |
| PS-11 | Recovery is independently verified against the original user-impacting condition. | Dedicated recovery verification step separate from responder/executor success. | `module-4/incident-response/runbooks/verify-recovery.sh`; `recovery-verification.json` | Accepted |
| PS-12 | The material incident trail is auditable and reconstructable. | Incident record links release, alert, evidence, responder assessment, authorization, action disposition, and recovery verification. | `module-4/incident-response/incidents/p5-taskflow-final-20261006-053711/`; `module-4/docs/operations-and-security-report.md` | Accepted |
| PS-13 | Module 4 has a security review using scanner evidence, model-assisted review, human disposition, and capability/credential review. | P6-A security audit artifacts and structured findings. | `module-4/security-audit/audit-brief.md`; `capability-table.md`; `findings.schema.json`; `scanner-runbook.md`; `runs/` | Accepted with documented Snyk limitation |
| PS-14 | The completed M3 baseline remains protected during M4 work. | M3 CI remains active; automatic production deployment is retired; the original deployment workflow is archived; shared AWS infrastructure is retained for M4. | `.github/workflows/ci.yml`; `.github/workflows/deploy.yml` (manual-only retirement entrypoint); `module-3/docs/archive/deploy-m3.yml`; `module-3/docs/post-course-lifecycle.md`; `M4-P6A-002.json`; security audit inventory | Accepted |
| PS-15 | Homework 4 remains a separate evidence workstream and does not redefine TaskFlow acceptance. | Separate P6-B repository/evidence boundary. | `module-4/docs/homework-4-evidence.md`; P6 implementation-plan boundary | Accepted as ownership boundary |

## 2. P6-A Security Finding Traceability

| Finding ID | Observation | Human disposition | Verification / evidence |
|---|---|---|---|
| `M4-P6A-001` | 19 mutable M4 GitHub Action references | Confirmed — remediate | Pinned workflow files; final Semgrep `m4_mutable_action_results=0`; remediation checkpoint `7906eb5f...` |
| `M4-P6A-002` | 15 inherited M3 mutable Action references | Informational observation / out of scope | Protected M3 workflow files; explicit human disposition |
| `M4-P6A-003` | `workflow_run` target-code checkout pattern | False positive / not applicable | Reviewed gate conditions, immutable `head_sha` checkout, and revision verification |
| `M4-P6A-004` | Bun minimum release age of 24h vs scanner's 7d recommendation | Confirmed — accepted risk | `module-4/frontend/bunfig.toml`; explicit human disposition |
| `M4-P6A-005` | Missing uv dependency cooldown | Confirmed — remediate | `exclude-newer = "7 days"`; `uv lock --check`; `uv sync --locked`; final `uv_cooldown_results=0` |
| `M4-P6A-006` | Dynamic responder URL passed to `urllib` | False positive / not applicable | Operator-controlled responder configuration review; explicit boundary condition |

## 3. Final Acceptance Statement

P6-A TaskFlow acceptance is supported when all of the following are true:

```text
[✓] P3 release behavior and release identity remain evidenced
[✓] P4 observability and user-impact alert remain evidenced
[✓] P5 bounded incident-response loop is reconstructable
[✓] external authorization remains separate from model output
[✓] recovery verification is independent of action attempt
[✓] security findings have explicit human dispositions
[✓] actionable P6-A hardening findings are remediated and verified
[✓] M3 CI remains active; automatic deployment is retired and archived; shared infrastructure remains available for M4
[✓] material TaskFlow incident and security-review trail is reconstructable
[✓] Homework 4 remains a separate P6-B evidence stream
```

Snyk Agent Scan is recorded as an inconclusive scanner limitation rather than a clean result; this does not get converted into a zero-risk assertion.

## 4. Evidence Ownership and Scope

P6-A owns the TaskFlow security and operational acceptance evidence in this repository.

P6-B owns the Homework 4 runtime evidence in the separate order-tracker homework repository.

Neither workstream is permitted to substitute its evidence for the other's runtime behavior.

## 5. Post-acceptance M4 Release Verification — November 3, 2026

This section records the M4 deployment performed after the original
P6-A acceptance baseline. It supplements the historical traceability
records and does not alter the original P5/P6-A evidence identities.

```text
release_sha = 07273bb6931673fc8b4b8c64e2eff7967e86a6cc
```

| Stage | Workflow run | Verification |
|---|---|---|
| M4 CI and image publication | [CI #36](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41619409483) | CI passed; immutable images and release manifest published |
| DEV deployment | [DEV #34](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41619655181) | Release state matched SHA/digests; frontend and Tasks API smoke tests passed |
| Manual PROD promotion | [PROD #2](https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/41623688998) | Existing release promoted; PROD release state matched SHA/digests; frontend and Tasks API smoke tests passed |

The image digests verified in both environments are:

| Image | SHA-256 digest |
|---|---|
| Backend | `sha256:f65fd38aa0f9194e95fca60998f798d8862f16308daec64d767eacab9ac1a589` |
| Frontend | `sha256:f82f381968a4f21c357988e92f4b755a62b30f31c416f7375c3422f67a6c93ad` |

The PROD promotion reused the DEV release manifest and runtime
bundle without rebuilding the application images. The promotion
workflow verified the PROD release-state record against the exact
Git SHA and both manifest image references.

These checks represent point-in-time deployment evidence and
smoke tests, not a continuous availability guarantee.
