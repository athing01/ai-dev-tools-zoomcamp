# Module 3 Testing

This document describes the testing strategy and local verification procedures for TaskFlow Module 3.

## Overview

Module 3 uses PostgreSQL for integration testing and for the deployed application. Unit tests continue to exercise application behavior through the in-memory repository.

There are two integration-test layers:

1. **Backend PostgreSQL integration tests**
   - Test file: `module-3/tests/integration/test_crud.py`
   - Runs against a real PostgreSQL database.
   - The test fixtures prepare the schema through the Alembic migration chain.

2. **Frontend-to-backend (F2B) integration tests**
   - Test file: `module-3/tests/integration/f2b/test_f2b.test.ts`
   - Uses the production frontend API client: `module-3/frontend/src/lib/tasks/taskService.ts`.
   - Sends real HTTP requests to a running FastAPI backend.
   - The backend uses the PostgreSQL test database.
   - Uses Vitest with the **Node** test environment; no frontend build or frontend server is required.

The F2B path is:

`taskService.ts -> HTTP -> FastAPI -> PostgreSQL`

The F2B tests do not mock the API client, backend, or database.

All integration-test code is under `module-3/tests/integration/`.

## Test Layers

### Unit tests

Unit tests exercise application behavior through the in-memory repository.

They do not require PostgreSQL.

Backend unit tests:

```bash
cd module-3/backend
uv run pytest
```

Frontend unit tests:

```bash
cd module-3/frontend
bun run test
```

### Integration tests

Integration tests verify behavior against a real PostgreSQL instance.

The backend integration tests use PostgreSQL with Alembic-managed schema setup.

The F2B integration tests additionally verify the frontend API client to backend API path, including the configured CORS path:

`frontend API client -> HTTP -> FastAPI -> PostgreSQL`

## Local Integration-Test Setup

### 1. Start the PostgreSQL test database

A dedicated PostgreSQL container can be used for the local integration-test database:

```bash
docker run -d --name tf-test-pg \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=taskflow_test \
  -p 127.0.0.1:55002:5432 \
  postgres:16
```

The test database URL is:

```text
postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test
```

You can export it once for the current shell:

```bash
export TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test"
```

The commands below also set the URL explicitly where that makes the command independently copyable.

### 2. Start the backend for F2B tests

The backend must be running before the F2B tests are started.

From the **project root**:

```bash
cd module-3/backend

TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
CORS_ALLOWED_ORIGINS="http://localhost:3000" \
uv run uvicorn taskflow_backend.app:create_app --factory --host 0.0.0.0 --port 8000
```

Keep this process running while the F2B tests are executed.

## Running Integration Tests

### Backend PostgreSQL integration tests

Run from the project root:

```bash
cd module-3/backend

TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
uv run pytest ../tests/integration/ -v
```

The integration fixture:

1. Reads `TEST_DATABASE_URL`.
2. Verifies that PostgreSQL is reachable.
3. Runs `alembic upgrade head` to prepare the schema.
4. Clears task rows for backend-test isolation.
5. Creates the SQLAlchemy repository and FastAPI application.
6. Runs the integration tests.

No manual `alembic upgrade head` is required before the test suite.

### Frontend-to-backend (F2B) integration tests

With PostgreSQL running and the backend already running on `http://localhost:8000`:

```bash
cd module-3/frontend

TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
VITE_API_BASE_URL="http://localhost:8000" \
bun run test:f2b
```

The configured script is:

```json
"test:f2b": "vitest run --config vitest.f2b.config.ts"
```

Use `bun run test:f2b` so the dedicated F2B Vitest configuration is used.

The F2B tests do not start Nitro, Vite, or a frontend container.

## Test Coverage

### Backend PostgreSQL integration tests

The backend integration tests cover:

- list tasks, including the empty result case
- create task
- partial update
- status change
- delete
- missing-resource behavior
- timezone-aware UTC timestamps
- `updated_at` advancing on update

### Frontend-to-backend (F2B) integration tests

The F2B suite contains 9 tests covering:

- finding a created task through the frontend API client
- creating a task through the frontend API client
- listing multiple created tasks
- partial task update
- task status change
- task deletion
- 404 handling for missing resources
- timezone-aware UTC timestamps
- `updated_at` advancing on update

## Test Isolation

### Backend integration tests

Backend integration tests clear task rows as part of the fixture lifecycle so one backend test does not depend on task data left by another backend test.

### F2B integration tests

F2B tests use a separate cleanup strategy:

- each test creates the task data it needs
- each test records the IDs of tasks it created
- `afterEach()` deletes only those recorded task IDs
- assertions identify tasks by IDs returned by the API
- tests do not assume the database contains only their own tasks

The F2B suite assumes an isolated test environment for a test run. Concurrent F2B runs against the same database are not a supported isolation model.

## CI Testing

The Module 3 CI workflow runs the following jobs for the Module 3 test/build path:

- `backend-lint`
- `backend-unit`
- `frontend-lint`
- `frontend-unit`
- `integration`
- `container-build`

The `integration` job uses a PostgreSQL 16 service and exercises the real PostgreSQL integration path, including the Alembic-managed schema setup and the F2B tests.

The `container-build` job verifies that the backend and frontend Docker images build successfully. It does not push images or deploy to AWS.

Pull requests and pushes to `main` run the same CI workflow, subject to the workflow path filters.

## P9 CI/CD Release Verification

P9 adds a production deployment workflow that runs after the exact upstream workflow `CI — Module 3` completes.

Deployment proceeds only when the upstream run has:

```text
conclusion == success
event == push
head_branch == main
```

Pull-request CI runs do not deploy.

The authoritative release identity is:

```text
github.event.workflow_run.head_sha
```

The same SHA is preserved across checkout, infrastructure-change detection, immutable ECR tags, release manifests, SSM deployment, release-state verification, and public smoke tests.

The production release path is:

```text
successful CI on main
-> workflow_run deployment gate
-> checkout and verify exact release SHA
-> detect module-3/infra/** changes
-> configure AWS credentials through GitHub OIDC
-> build linux/amd64 backend/frontend images
-> push immutable ECR SHA tags
-> resolve final image digests
-> update CloudFormation only when infrastructure changed
-> create/upload S3 release manifest
-> invoke SSM Run Command
-> existing /opt/taskflow/deploy.sh performs the EC2 deployment
-> verify P8 release-state content
-> public frontend smoke test
-> public tasks API smoke test
```

The production frontend build uses the exact public API base URL:

```text
VITE_API_BASE_URL=https://api.zctaskflow.athing.cc
```

AWS authentication uses GitHub OIDC and the existing deployment role. No long-lived AWS access keys are part of the release path.

## P9 Deployment-Level Verification

The deployment workflow verifies:

- the release SHA is a valid 40-character commit SHA
- the checked-out commit exactly matches `workflow_run.head_sha`
- infrastructure changes are detected only under `module-3/infra/`
- final ECR image digests resolve to valid `sha256:` digests
- the release manifest contains the release SHA and both image digests
- SSM Run Command completes with `Success`
- the P8 release-state content matches the requested SHA and exact deployed ECR image digests
- the public frontend returns HTTP 200
- `/api/tasks` returns HTTP 200 and a JSON array

The P9 merge-to-main release path was exercised successfully through SSM deployment, release-state verification, and the public smoke tests.

## P10 Rollback and Recovery Verification

P10 rehearsed application rollback and recovery using existing immutable release artifacts documented in `docs/release-process.md`.

The rehearsal:

- rolled back from `c04f832...` to `38ca2e4...`
- verified SSM completion and release-state
- verified the public frontend and `/api/tasks`
- recovered to `c04f832...`
- re-verified the public frontend and `/api/tasks`

Both rollback and recovery completed successfully.

## Authentication Applicability

TaskFlow currently has no user identity model, session/token model, task ownership model, or authorization model.

For the current TaskFlow application scope, authentication-specific integration/E2E tests are **N/A**.

This is a project-specific scope determination, not a statement that the official Module 3 source omits authentication from its general wording. If an authoritative later rubric requires authentication for this project, this section must be revised through the normal change process.

## Negative Testing

The integration fixture is intended to fail clearly when PostgreSQL cannot be reached.

For example:

```bash
cd module-3/backend

TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:59999/taskflow_test" \
uv run pytest ../tests/integration/test_crud.py -v
```

The expected result is a test failure with a diagnostic indicating that PostgreSQL is unreachable.

This is different from omitting `TEST_DATABASE_URL`: the fixture requires that environment variable and fails earlier when it is missing.

## Configuration

| Variable | Required | Used by | Description |
|---|---|---|---|
| `TEST_DATABASE_URL` | Yes for integration/F2B tests | Integration tests and F2B fixture | PostgreSQL connection URL for the integration-test database |
| `DATABASE_URL` | Required for a standalone backend run and application runtime | Backend | PostgreSQL connection URL used by the FastAPI application |
| `VITE_API_BASE_URL` | Yes for F2B; required at frontend build time | Frontend API client | Base URL of the FastAPI backend |
| `CORS_ALLOWED_ORIGINS` | Required for the documented local backend run | Backend | Exact-origin allowlist for allowed browser origins |

## Local Full-Stack Verification

For the reproducible application stack, use the root Compose setup documented in `README.md`:

```bash
cd module-3
docker compose up -d --build
docker compose ps
curl -fsS http://localhost:3000/
curl -fsS http://localhost:8000/api/tasks
```

The expected local topology is:

`postgres -> migrate -> backend -> frontend`

The PostgreSQL data is stored in the named `taskflow_postgres_data` volume.

## Best Practices

1. Run integration tests against real PostgreSQL rather than SQLite or mocks.
2. Do not silently skip integration tests when PostgreSQL is unavailable.
3. Use Alembic for integration-test schema setup.
4. Keep backend-test and F2B isolation mechanisms explicit.
5. Keep F2B tests on the real `taskService.ts -> HTTP -> FastAPI -> PostgreSQL` path.
6. Do not use direct PostgreSQL access from the F2B TypeScript tests.
7. Keep unit-test and integration-test responsibilities separate.

## References

- Module 3 Product Specification
- Module 3 Implementation Plan
- `AGENTS.md`
- `module-3/tests/integration/test_crud.py`
- `module-3/tests/integration/f2b/test_f2b.test.ts`
- `module-3/backend/tests/test_sqlalchemy_repository.py`
- `module-3/docs/release-process.md`
