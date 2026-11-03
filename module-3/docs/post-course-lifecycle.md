# Module 3 Post-course Lifecycle

Decision date: 2026-11-03

Status: Course acceptance completed; automatic deployment retired.

## 1. Decision

Module 3 completed its course implementation and acceptance lifecycle
in September 2026.

The post-course operational decision is:

- Retire Module 3 automatic production deployment.
- Keep Module 3 CI active for continuing code-quality validation.
- Retain the existing shared AWS infrastructure for Module 4.
- Do not delete, replace, or recreate the shared AWS resources.
- Keep the historical Module 3 deployment implementation and evidence
  in the repository.
- Do not use historical Module 3 deployment or rollback commands
  against the current shared EC2 runtime.

The M3 deployment workflow remains as a manual-only retirement notice.
It has no AWS permissions and performs no deployment.

## 2. Historical Acceptance Evidence

### P8 — EC2 Runtime Deployment

PR #2: feat(m3): add EC2 runtime deployment

https://github.com/athing01/ai-dev-tools-zoomcamp/pull/2

The PR verification record documented:

- EC2 bootstrap completed successfully.
- Backend and frontend deployed using immutable ECR image digests.
- RDS connectivity and Alembic migration succeeded.
- Caddy obtained HTTPS certificates for both public hostnames.
- Public frontend returned HTTP 200.
- Public API /api/tasks returned HTTP 200 and a JSON array.
- Release state was recorded for:
  d75c893f26d34a7e852c75663cb6c9ee05967c3e

### P9 — Automated CI/CD Deployment

Successful deployment:

- GitHub Actions run #11
- Date: 2026-09-28
- Release SHA:
  c04f832b62c17df074e4a1a06e8c13acc3685a03

https://github.com/athing01/ai-dev-tools-zoomcamp/actions/runs/36456229892

Verified execution included:

- Exact upstream CI release SHA validation.
- Immutable ECR image build and push.
- Image digest resolution.
- S3 release manifest creation.
- SSM deployment completed successfully.
- P8 release-state matched the requested SHA and image digests.
- Public frontend and Tasks API smoke tests succeeded.

Historical issue and correction:

- P9 run #10 completed SSM deployment successfully but failed
  during post-deployment release-state verification because the
  deployment role lacked S3 HeadObject/GetObject access.
- PR #16 added the required release-state read permission.
- P9 run #11 subsequently passed the complete deployment workflow.

### P10 — Rollback and Recovery

Evidence is recorded in:

module-3/docs/release-process.md
Section 9: P10 Rollback and Recovery Rehearsal

The recorded rehearsal:

- Started from release c04f832.
- Rolled back to release 38ca2e4 through SSM.
- Verified release state and public services.
- Recovered to release c04f832 through SSM.
- Re-verified release state and public services.

The rollback and recovery were executed through SSM. Both
completed successfully, followed by release-state and public
frontend and API verification.

### P12 — Final Verification

PR #19: chore(m3): complete final verification

https://github.com/athing01/ai-dev-tools-zoomcamp/pull/19

Merged: 2026-09-29

The final verification record covered:

- Acceptance criteria through AC-9.4.
- AC-1.3 PostgreSQL enum verification.
- Clean-clone Docker Compose startup.
- PostgreSQL and Alembic migration flow.
- CI/CD deployment evidence.
- Secret and configuration hygiene.
- T1-T17 implementation-plan items.
- P10 rollback and recovery rehearsal.

## 3. Current Shared AWS Infrastructure Snapshot

Read-only verification performed on 2026-11-03.

### CloudFormation

Stack status: UPDATE_COMPLETE

All 27 stack resources reported CREATE_COMPLETE or UPDATE_COMPLETE.

### RDS

- PostgreSQL 16.13.
- Status: available.
- PubliclyAccessible: false.
- StorageEncrypted: true.
- MultiAZ: false.
- Located in TaskFlow VPC.

The RDS master secret is managed by RDS through Secrets Manager.

CloudTrail attributed the 2026-10-31 credential rotation to
AWS-managed RDS service activity. Secrets Manager recorded
RotationSucceeded. No user-initiated credential reset was
identified in the inspected event sequence.

### EC2 and SSM

- EC2 instance state: running.
- System, instance, and attached EBS status checks: ok.
- SSM managed-instance status: Online.

The shared EC2 host currently serves Module 4 PROD and follows
its deployment contract. It must not be targeted by retired M3
deployment procedures.

### ECR

Both TaskFlow ECR repositories reported:

- IMMUTABLE tag mutability.
- AES256 encryption.
- ScanOnPush enabled.

### S3 Artifact Bucket

Verified:

- All four public-access-block settings enabled.
- Versioning enabled.
- AES256 default encryption.
- Incomplete multipart uploads expire after 7 days.
- Noncurrent manifest versions expire after 30 days.

### CloudWatch and SSM Logging

SSM command logs were retained in CloudWatch.

- Retention: 30 days.
- An SSM stderr log stream was found.
- The log stream contained the M3 Deploy run #17 failure output.

## 4. Post-course Runtime Boundary

On 2026-11-03, M3 Deploy run #17 reached the shared EC2 host but
stopped during pre-deployment configuration validation. The host's
current Module 4 deployment contract was incompatible with the
retired Module 3 workflow. The deployment sequence did not proceed,
and the run did not deploy an M3 application release.

This is not evidence that the historical M3 P8/P9 deployment
lifecycle failed. M3 had previously completed the documented
P8 deployment, P9 release, P10 rehearsal, and P12 verification.

Do not rerun M3 deployment or rollback workflows against the
current shared EC2 instance.

## 5. Retirement Boundaries

The following remain unchanged:

- Module 3 application source code.
- Module 3 CI workflow.
- Module 3 CloudFormation template.
- Historical deployment scripts and documentation.
- Existing shared AWS resources.
- Module 4 CI, DEV deployment, and manual PROD promotion workflows.

The following lifecycle transition is made:

- Module 3 automatic deployment is disabled.
- The M3 deploy workflow becomes a manual-only no-op notice.
- Module 4 continues using the existing shared AWS infrastructure.

No AWS resources are deleted, stopped, replaced, or recreated
as part of this retirement.

## 6. Separate Module 4 Follow-up

The 2026-11-03 M4 CI run #33 encountered an immutable ECR tag
collision while publishing the backend image.

This is a separate Module 4 image-publishing issue. Retiring
M3 automatic deployment prevents future automatic M3 releases
from competing with M4, but does not resolve an already-existing
immutable tag collision.

It must be handled as a separate M4 CI/CD issue.

## 7. Final Lifecycle Outcome

Module 3 course acceptance is preserved as historical evidence.

Module 3 CI remains active.

Module 3 automatic production deployment is retired.

Shared AWS infrastructure remains available for Module 4.

No AWS resource retirement or migration is performed.
