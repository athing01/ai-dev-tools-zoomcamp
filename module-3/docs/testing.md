# Module 3 Testing

This document describes the testing strategy and local verification procedures for TaskFlow Module 3.

## Overview

Module 3 includes integration tests that use a real PostgreSQL database instead of SQLite.

There are two integration-test layers:

1. **Backend PostgreSQL integration tests**

   - Test file: `module-3/tests/integration/test_crud.py`
   - Runs the backend integration tests against PostgreSQL.
   - The test fixtures prepare the schema with Alembic.

2. **Frontend-to-backend (F2B) integration tests**

   - Test file: `module-3/tests/integration/f2b/test_f2b.test.ts`
   - Uses the production frontend API client (`module-3/frontend/src/lib/tasks/taskService.ts`).
   - Sends real HTTP requests to a running FastAPI backend.
   - The backend uses the PostgreSQL test database.
   - Uses Vitest with the **Node** test environment; no frontend build is required.

The intended F2B path is:

`taskService.ts -> HTTP -> FastAPI -> PostgreSQL`

The F2B tests do not mock the API client, backend, or database.

The test implementation is located under `module-3/tests/integration/`.

## Test Layers

### Unit tests

Unit tests exercise application behavior through the in-memory repository.

They do not require a PostgreSQL database.

The frontend unit tests remain separate from the F2B integration tests.

### Integration tests

Integration tests verify behavior against the real PostgreSQL database.

The backend integration tests use PostgreSQL with Alembic-managed schema setup.

The F2B integration tests additionally verify the frontend API client to backend API path, including the configured CORS path:

`frontend API client -> HTTP -> FastAPI -> PostgreSQL`

## Setup

### 1. Start the PostgreSQL test database

From any directory:

```bash
docker run -d --name tf-test-pg \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=taskflow_test \
  -p 127.0.0.1:55002:5432 \
  postgres:16
```

The test database URL used by the project is:

```text
postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test
```

You can export it once for the current shell:

```bash
export TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test"
```

The test commands below also set the URL explicitly so that they can be copied and run independently.

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

## Running the Tests

### Backend PostgreSQL integration tests

Run from the **project root**:

```bash
cd module-3/backend

TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
uv run pytest ../tests/integration/ -v
```

This is the canonical local command for the backend PostgreSQL integration tests.

The test fixture:

1. Reads `TEST_DATABASE_URL`.
2. Verifies that PostgreSQL is reachable.
3. Runs `alembic upgrade head` to prepare the schema.
4. Clears task rows for backend-test isolation.
5. Creates the SQLAlchemy repository and FastAPI application.
6. Runs the integration tests.

No manual `alembic upgrade head` command is required before running the test suite.

### Frontend-to-backend (F2B) integration tests

With PostgreSQL running and the backend already running on `http://localhost:8000`, run from the **project root**:

```bash
cd module-3/frontend

TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
VITE_API_BASE_URL="http://localhost:8000" \
bun run test:f2b
```

`test:f2b` is the project's configured Vitest command:

```json
"test:f2b": "vitest run --config vitest.f2b.config.ts"
```

Use this command instead of calling Vitest directly so the dedicated F2B configuration is always used.

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

F2B tests use a different isolation strategy:

- Each test creates the task data it needs.
- Each test records the IDs of tasks it created.
- `afterEach()` deletes only those recorded task IDs.
- Assertions identify tasks by the IDs returned by the API.
- Tests do not assume that the database contains only their own tasks.
- Unrelated stale task data therefore does not affect the correctness of the F2B assertions.

The F2B suite assumes an isolated test environment for a test run. Concurrent F2B runs against the same database are not a supported isolation model.

## Authentication Applicability

Authentication is not implemented and is out of scope for the current TaskFlow MVP.

The application has no user identity, session, task ownership, or authorization model. Therefore, authentication-specific integration tests are not applicable to the current testing scope.

This is a project scope decision, not a missing authentication test requirement.

## Negative Testing

The integration test fixture is intended to fail clearly when PostgreSQL cannot be reached.

To exercise the PostgreSQL-unreachable path, keep `TEST_DATABASE_URL` set but point it at an unavailable PostgreSQL endpoint. For example, from the **project root**:

```bash
cd module-3/backend

TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:59999/taskflow_test" \
uv run pytest ../tests/integration/test_crud.py -v
```

The expected result is a test failure with a diagnostic indicating that PostgreSQL is unreachable.

This is different from omitting `TEST_DATABASE_URL`: the fixture requires that environment variable and will fail earlier if it is not provided.

## Configuration

### Environment variables

| Variable               | Required                                 | Used by                                   | Description                                                 |
| ---------------------- | ---------------------------------------- | ----------------------------------------- | ----------------------------------------------------------- |
| `TEST_DATABASE_URL`    | Yes                                      | Backend integration tests and F2B fixture | PostgreSQL connection URL for the integration-test database |
| `DATABASE_URL`         | For the standalone backend run           | Backend                                   | Database URL used when starting the FastAPI application     |
| `VITE_API_BASE_URL`    | Yes for F2B                              | Frontend API client                       | Base URL of the running FastAPI backend                     |
| `CORS_ALLOWED_ORIGINS` | Yes for the documented local backend run | Backend                                   | Allows the local frontend origin                            |

### Test database URL

Use:

```text
postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test
```

### F2B API URL

The documented local F2B setup uses:

```text
http://localhost:8000
```

## Verification

A complete local Module 3 testing verification is:

1. Start the PostgreSQL test container.
2. Start the FastAPI backend on port `8000`.
3. Run the backend PostgreSQL integration tests.
4. Run the F2B integration tests.

The two test layers can be run independently after their respective prerequisites are available.

## Best Practices

1. Always run PostgreSQL integration tests against a real PostgreSQL database.
2. Do not silently skip integration tests when PostgreSQL is unavailable.
3. Use Alembic for integration-test schema setup.
4. Keep backend-test and F2B-test isolation mechanisms explicit.
5. Keep F2B tests on the real `taskService.ts -> HTTP -> FastAPI -> PostgreSQL` path.
6. Do not use direct PostgreSQL access from the F2B TypeScript tests.
7. Keep unit-test and integration-test responsibilities separate.

## CI Testing

CI testing documentation will be updated when the CI/CD phase is implemented.

The current testing documentation does not assume a CI PostgreSQL service or CI test commands that have not yet been implemented.

## References

- Module 3 Product Specification (v1.3)
- Module 3 Implementation Plan
- `AGENTS.md`
- `module-3/backend/tests/test_sqlalchemy_repository.py` - original SQLite repository tests
