# TaskFlow Module 3 Deployment

This document describes the current TaskFlow Module 3 deployment architecture and deployment configuration boundaries.

## Deployment Overview

TaskFlow is deployed as a single public application target on AWS.

Current public endpoints:

- Frontend: `https://app.zctaskflow.athing.cc/`
- Backend API: `https://api.zctaskflow.athing.cc/`
- API documentation: `https://api.zctaskflow.athing.cc/docs`

Module 3 uses a single production deployment target. Separate staging/production environments are outside the implemented Module 3 scope.

## Deployment Topology

```text
Internet
   |
   +--> app.zctaskflow.athing.cc
   |       |
   |       v
   |     Caddy :443/:80
   |       |
   |       v
   |     frontend :3000
   |
   +--> api.zctaskflow.athing.cc
           |
           v
         Caddy :443/:80
           |
           v
         backend :8000
           |
           v
      private RDS PostgreSQL
```

Supporting services:

```text
GitHub Actions
   |
   +--> GitHub OIDC --> AWS deploy role
   |
   +--> ECR --> immutable backend/frontend images
   |
   +--> S3 --> release manifests / deployment bundle / release state
   |
   +--> SSM Run Command --> EC2 deployment script
                        |
                        +--> SSM Parameter Store
                        |
                        +--> ECR image pull
                        |
                        +--> RDS migration
```

### AWS components

The selected deployment platform uses:

- Amazon EC2 for the application host
- Docker Compose for the application runtime
- Amazon ECR for backend/frontend images
- Amazon RDS for managed PostgreSQL
- AWS CloudFormation for stable infrastructure
- GitHub Actions with GitHub OIDC for CI/CD authentication
- AWS Systems Manager (SSM) for remote deployment execution
- SSM Parameter Store for runtime configuration/secrets
- Amazon S3 for deployment artifacts, release manifests, and release state
- Caddy for reverse proxy and automatic HTTPS/ACME

CloudFormation owns stable infrastructure. Normal application releases are not performed by treating CloudFormation as the application-release mechanism.

## EC2 Runtime

The EC2 host runs these Compose services:

- `caddy`
- `backend`
- `frontend`
- `migrate`

Only Caddy publishes host ports `80` and `443`.

Backend port `8000` and frontend port `3000` are internal container-network endpoints.

The backend uses the exact ECR image digest recorded in the release manifest. The frontend is likewise deployed by immutable ECR image digest.

## Build-Time and Runtime Configuration

TaskFlow intentionally separates non-secret frontend build configuration from backend runtime configuration.

| Variable | Scope | Nature | Example |
|---|---|---|---|
| `VITE_API_BASE_URL` | Frontend | Build-time, browser-visible, non-secret | `https://api.zctaskflow.athing.cc` |
| `DATABASE_URL` | Backend | Runtime, secret-bearing | assembled at deployment time |
| `CORS_ALLOWED_ORIGINS` | Backend | Runtime, exact-origin configuration | `https://app.zctaskflow.athing.cc` |
| `ACME_EMAIL` | Caddy | Runtime configuration | ACME account email |

`VITE_API_BASE_URL` is embedded during the frontend build and is therefore not treated as a secret.

For the public deployment, the frontend is built with:

```text
VITE_API_BASE_URL=https://api.zctaskflow.athing.cc
```

The browser talks directly to the public backend origin. There is no same-origin `/api` proxy layer.

## Secrets and Configuration Boundaries

Runtime database credentials are stored in AWS Systems Manager Parameter Store as `SecureString` parameters.

The EC2 instance role is permitted to retrieve the TaskFlow runtime parameters required by deployment.

The deployment script retrieves the runtime parameters and assembles:

```text
DATABASE_URL=postgresql+psycopg://<user>:<password>@<rds-endpoint>:5432/taskflow?sslmode=require
```

The generated runtime environment file is:

```text
/opt/taskflow/runtime.env
```

It is protected with file mode `0600`.

The runtime database identity is a dedicated application database role rather than the RDS master credential.

The RDS master secret is not used as the long-term application runtime credential.

Secrets must not be committed to Git, written into image layers, or emitted in CloudFormation outputs.

## Managed PostgreSQL

The deployed TaskFlow application uses Amazon RDS PostgreSQL.

The RDS instance is private to the VPC and is not exposed directly to the public internet.

The application reaches RDS from the EC2 host over the private network.

## Deployment-Time Migrations

Database migrations are a distinct deployment step.

The deployment sequence verifies RDS reachability and then runs:

```bash
alembic upgrade head
```

Migration failure stops the deployment before the backend update.

The application does not run `create_all()` for production deployment, and Alembic migrations are not launched automatically from application startup.

## P9 Automated Release Flow

Production application releases are driven by the successful completion of `CI — Module 3` on `main`.

The deployment workflow uses `workflow_run` and proceeds only when all of the following are true:

```text
workflow_run.conclusion == success
workflow_run.event == push
workflow_run.head_branch == main
```

Pull-request CI runs do not deploy.

The authoritative release identity is:

```text
github.event.workflow_run.head_sha
```

That exact SHA is checked out and verified before deployment. It is then reused for:

- infrastructure-change detection
- immutable ECR tags
- image-digest resolution
- release manifest naming and contents
- SSM deployment input
- release-state verification

The release sequence is:

```text
successful CI on main
-> workflow_run deployment gate
-> validate and check out exact release SHA
-> detect module-3/infra/** changes
-> configure AWS credentials through GitHub OIDC
-> read deployed CloudFormation outputs
-> build linux/amd64 backend/frontend images
-> push immutable sha-<release-SHA> ECR tags
-> resolve final image digests
-> apply CloudFormation only when infrastructure changed
-> create/upload release manifest to S3
-> invoke AWS-RunShellScript through SSM
-> /opt/taskflow/deploy.sh performs the EC2 release
-> wait for SSM success
-> verify P8 release-state content
-> smoke test public frontend
-> smoke test public tasks API
```

### CI gate and release identity

The deployment job does not use `github.sha` as the application release identity.

The exact upstream CI `head_sha` is preserved end-to-end so that the same source revision is built, tagged, manifested, deployed, and verified.

### AWS authentication

The deployment workflow uses GitHub OIDC with the existing:

```text
taskflow-github-deploy
```

IAM role.

The workflow does not introduce long-lived AWS access keys or secret-based AWS authentication.

The role's CloudFormation permissions are managed through the CloudFormation template and scoped to the existing TaskFlow resources required by the release workflow.

### Container build and ECR

Both application images are built for:

```text
linux/amd64
```

The immutable image tags are:

```text
taskflow/backend:sha-<release-SHA>
taskflow/frontend:sha-<release-SHA>
```

The workflow supports idempotent handling of an already-existing immutable tag and then resolves the final image digest.

The release manifest uses the resolved `sha256:` digests rather than relying on tags for deployment identity.

### Frontend production build

The production frontend build uses exactly:

```text
VITE_API_BASE_URL=https://api.zctaskflow.athing.cc
```

This is a public build-time configuration value and is not treated as a secret.

### Conditional CloudFormation

CloudFormation is invoked only when the release contains changes under:

```text
module-3/infra/**
```

The implemented P9 comparison uses the release commit's first-parent range:

```text
RELEASE_SHA^..RELEASE_SHA
```

For a merge-to-main release, the first parent represents the main-branch state immediately before the merge.

The workflow creates and inspects a change set before execution and rejects resource replacements or conditional replacements rather than silently applying them.

CloudFormation is therefore used for stable infrastructure updates, not as the normal application-release mechanism.

### Release manifest

The release manifest is uploaded to:

```text
s3://<ReleaseArtifactBucketName>/manifests/<release-SHA>.json
```

The manifest contains the release SHA and resolved backend/frontend image digests.

It does not contain runtime credentials, database passwords, or other secret values.

### SSM deployment

The deployment workflow invokes:

```text
AWS-RunShellScript
```

against the EC2 target identified by:

```text
tag:TaskFlow=true
```

The command invokes the existing P8 deployment engine:

```bash
TASKFLOW_RELEASE_BUCKET=<release-bucket>   /opt/taskflow/deploy.sh manifests/<release-SHA>.json
```

The workflow waits for the SSM invocation to reach `Success`.

`deploy.sh` remains responsible for the EC2-side deployment sequence, including exact-image deployment, runtime secret retrieval, RDS connectivity, migrations, service updates, readiness checks, and release-state writing.

## Release-State Verification

After SSM succeeds, the GitHub Actions workflow reads:

```text
release-state/<release-SHA>.json
```

from the release artifact bucket.

The workflow verifies that the release-state content matches:

```text
.git_sha         == <release-SHA>
.backend_image   == <backend ECR URI>@<resolved backend digest>
.frontend_image  == <frontend ECR URI>@<resolved frontend digest>
```

The workflow does not create or overwrite the P8-owned release-state object.

## Public Smoke Tests

The automated release verifies the public application after the EC2 deployment completes.

Frontend:

```text
https://app.zctaskflow.athing.cc/
```

Expected:

```text
HTTP 200
```

Tasks API:

```text
https://api.zctaskflow.athing.cc/api/tasks
```

Expected:

```text
HTTP 200
valid JSON array
```

The P9 merge-to-main release path was exercised successfully through SSM deployment, release-state verification, and the public smoke tests.

## Current Deployment Verification

The current AWS deployment has been verified with:

```text
https://app.zctaskflow.athing.cc/     -> HTTP 200
https://api.zctaskflow.athing.cc/api/tasks -> HTTP 200 + JSON array
```

Caddy successfully obtained ACME certificates for both public hostnames.

## Rollback and Recovery

The documented rollback model is to redeploy a previously deployed immutable application release by running the EC2 deployment script against its existing S3 release manifest. The target release is verified before execution, including manifest integrity, release-state, ECR digest availability, database compatibility, and infrastructure compatibility.

Database handling favors backward-compatible migrations so an application-image rollback remains feasible. The deployment path does not automatically run `alembic downgrade`; an RDS snapshot restore is the data-recovery path of last resort.

P10 verified the rollback and recovery path against the existing production deployment target using existing release artifacts. The rehearsal rolled back from the current release to the previous deployed release, verified the deployed release-state and public services, and then recovered to the current release and re-verified the public services.

The complete operational procedure, exact commands, stop-the-line conditions, and rehearsal evidence are documented in [`docs/release-process.md`](release-process.md).

## Operational Documentation

- Testing strategy and local verification: [`docs/testing.md`](testing.md)
- Release, rollback, and recovery runbook: [`docs/release-process.md`](release-process.md)

## Operational Boundaries

| Layer | Responsibility |
|---|---|
| CloudFormation | Stable AWS infrastructure |
| GitHub Actions | CI, image build/push, manifest, deployment trigger, public smoke |
| EC2 | Docker Compose runtime and controlled deployment script |
| ECR | Immutable application images |
| RDS | Managed PostgreSQL |
| SSM | Remote execution and runtime parameter retrieval |
| S3 | Deployment bundle, release manifests, release state |
| Caddy | Public HTTP/HTTPS entrypoint and TLS |

## Out of Scope

The Module 3 deployment documentation does not define:

- separate staging and production environments
- staging/production configuration parity
- Kubernetes
- a separate authentication system
- a provider-independent deployment abstraction
