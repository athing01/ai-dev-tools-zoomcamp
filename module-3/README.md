# Module 3 — Test, Containerize, and Deploy TaskFlow

TaskFlow is a full-stack mini Kanban board originally built for Module 2.

Module 3 extends the existing application with:

- PostgreSQL
- Alembic migrations
- real PostgreSQL integration tests
- frontend-to-backend integration tests
- Docker images and Docker Compose
- GitHub Actions CI/CD
- public AWS deployment

## Local Development

The local development stack uses Docker Compose:

```text
postgres -> migrate -> backend -> frontend
```

### Prerequisites

For the full local stack:

- Docker with Docker Compose support

For running the test suites directly on the host:

- `uv` for the backend
- Bun for the frontend

No AWS credentials are required for local development or the local test suites.

### Start the Local Stack

From a clean clone:

```bash
git clone https://github.com/athing01/ai-dev-tools-zoomcamp.git
cd ai-dev-tools-zoomcamp/module-3

docker compose up -d --build
```

Check the service state:

```bash
docker compose ps
```

The expected stack contains:

- `postgres` healthy
- `migrate` completed successfully
- `backend` running
- `frontend` running

### Access the Local Application

Frontend:

```text
http://localhost:3000
```

Backend API:

```text
http://localhost:8000
```

Quick checks:

```bash
curl -fsS http://localhost:3000/
curl -fsS http://localhost:8000/api/tasks
```

The API request should return a JSON array.

The local frontend is built with:

```text
VITE_API_BASE_URL=http://localhost:8000
```

The backend allows the local frontend origin:

```text
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Stop the Local Stack

```bash
docker compose down
```

The PostgreSQL data is stored in the named volume:

```text
taskflow_postgres_data
```

The volume survives `docker compose down`, so database data persists across a later:

```bash
docker compose up -d
```

## Testing

### Backend unit tests

```bash
cd module-3/backend
uv run pytest
```

These tests use the in-memory repository and do not require PostgreSQL.

### Frontend unit tests

```bash
cd module-3/frontend
bun run test
```

### Backend PostgreSQL integration tests

Start a dedicated PostgreSQL test database:

```bash
docker run -d --name tf-test-pg \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=taskflow_test \
  -p 127.0.0.1:55002:5432 \
  postgres:16
```

Then:

```bash
cd module-3/backend

TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
uv run pytest ../tests/integration/ -v
```

The integration fixture prepares the schema using Alembic.

### Frontend-to-backend (F2B) integration tests

Start the backend against the same PostgreSQL test database:

```bash
cd module-3/backend

TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
CORS_ALLOWED_ORIGINS="http://localhost:3000" \
uv run uvicorn taskflow_backend.app:create_app --factory --host 0.0.0.0 --port 8000
```

In another shell:

```bash
cd module-3/frontend

TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
VITE_API_BASE_URL="http://localhost:8000" \
bun run test:f2b
```

The F2B tests use the real `taskService.ts -> HTTP -> FastAPI -> PostgreSQL` path.

More detail:

- [`docs/testing.md`](docs/testing.md)

## Container Images

The backend and frontend each have a multi-stage Dockerfile.

The frontend image runs the Nitro `node-server` output.

Build the images locally:

```bash
docker build --platform linux/amd64 \
  -t taskflow-backend:local \
  module-3/backend

docker build --platform linux/amd64 \
  --build-arg VITE_API_BASE_URL=http://localhost:8000 \
  -t taskflow-frontend:local \
  module-3/frontend
```

The local Compose stack is the preferred reproducible way to exercise both containers together.

## CI

The Module 3 CI workflow runs:

- backend lint
- backend unit tests
- frontend lint
- frontend unit tests
- PostgreSQL-backed integration tests
- container builds

Pull requests and pushes to `main` run the CI workflow subject to its path filters.

### GitHub Actions Workflows

The Module 3 GitHub Actions workflows are stored at the repository root:

- [`ci.yml`](../.github/workflows/ci.yml) — CI checks, tests, integration tests, and container builds.
- [`deploy.yml`](../.github/workflows/deploy.yml) — gated production release and deployment to AWS.

## Production CI/CD

P9 adds the production release workflow after CI succeeds on `main`.

Deployment is triggered by completion of the exact upstream workflow:

```text
CI — Module 3
```

The deployment job proceeds only when the upstream run is:

```text
success + push + main
```

Pull-request CI runs do not deploy.

The production release identity is:

```text
github.event.workflow_run.head_sha
```

The same SHA is used for checkout, immutable image tags, release manifest, SSM deployment input, and release-state verification.

Production release flow:

```text
merge to main
-> CI
-> workflow_run deployment gate
-> exact release SHA checkout/verification
-> linux/amd64 image builds
-> immutable ECR push
-> image digest resolution
-> conditional CloudFormation for module-3/infra/** changes
-> S3 release manifest
-> SSM Run Command
-> EC2 /opt/taskflow/deploy.sh
-> release-state verification
-> public smoke tests
```

AWS authentication uses GitHub OIDC and the existing deployment role. The production workflow does not use long-lived AWS access keys.

The production frontend build uses:

```text
VITE_API_BASE_URL=https://api.zctaskflow.athing.cc
```

CloudFormation manages stable infrastructure only. Normal application releases use the existing EC2 deployment engine rather than treating CloudFormation as the application deployment mechanism.

P10 verified the application rollback and recovery path using existing immutable release artifacts.
The operational procedure, database compatibility rules, stop-the-line conditions, and rehearsal evidence are documented in [`docs/release-process.md`](docs/release-process.md).

## Deployment

The current public TaskFlow deployment uses AWS with:

- EC2
- Docker Compose
- ECR
- RDS PostgreSQL
- CloudFormation
- GitHub OIDC
- SSM
- S3
- Caddy/ACME

Public application:

```text
https://app.zctaskflow.athing.cc/
```

Public API:

```text
https://api.zctaskflow.athing.cc/
```

The current deployment has been verified with:

```text
Frontend -> HTTP 200
GET /api/tasks -> HTTP 200 + JSON array
```

Deployment details:

- [`docs/deployment.md`](docs/deployment.md)

Release/rollback process:

- [`docs/release-process.md`](docs/release-process.md)

Testing details:

- [`docs/testing.md`](docs/testing.md)

## Project Scope

TaskFlow Module 3 changes infrastructure and delivery around the existing application.

Authentication, authorization, task ownership, and staging/production environment separation are outside the current Module 3 implementation scope.
