# TaskFlow Backend Implementation Plan

This plan intentionally makes no backend implementation changes. It preserves the required progression: a tested in-memory repository first, followed by SQLAlchemy and SQLite behind the same application-level interface.

## 1. Confirmed Contract Summary

`product-spec.md` and `openapi.yaml` confirm these endpoints and no others:

| Method | Path | Success | Defined error responses |
| --- | --- | --- | --- |
| GET | `/api/tasks` | 200 with `Task[]` | none |
| POST | `/api/tasks` | 201 with `Task` | 422 `ErrorResponse` |
| PATCH | `/api/tasks/{task_id}` | 200 with `Task` | 404 or 422 `ErrorResponse` |
| DELETE | `/api/tasks/{task_id}` | 204 with no response body | 404 `ErrorResponse` |

`GET /api/tasks/{task_id}` is explicitly out of scope.

A task has integer `id` (minimum 1), `title`, `description`, `status`, `created_at`, and `updated_at`. Status is exactly `todo`, `in_progress`, or `done`. On POST, `status` defaults to `todo` when omitted. `title` is trimmed before storage and must contain a non-whitespace character. PATCH is partial for `title`, `description`, and/or `status`; its request needs at least one property. `description` is optional on create but is always a string in a response, normalized to `""` when absent. Timestamps are date-time strings.

The defined JSON error shape is `{ "message": string }`. Request schemas reject additional properties. POST and PATCH validation failures are 422; PATCH and DELETE return 404 for an absent task.

## 2. Repository Findings and Assumptions

### Verified findings

- `module-2/frontend/` is a TypeScript React application using TanStack Start/Router/React Query and a Vite configuration.
- `module-2/frontend/bun.lock` and `bunfig.toml` establish Bun as the frontend package-manager convention. Its scripts are `bun run dev`, `build`, `preview`, and `lint` (the script bodies invoke Vite/ESLint).
- No frontend test runner or test scripts are currently configured.
- No frontend API base URL, API environment variable, proxy, or backend CORS configuration is present. `vite.config.ts` relies on the Lovable TanStack configuration and does not set a port.
- The current `TaskService` abstraction provides `listTasks`, `createTask`, `updateTask`, and `deleteTask`, but uses `string` task IDs. `mockTaskService.ts` is its active in-memory implementation and `queries.ts` imports it directly. This must be aligned with OpenAPI's integer IDs during the later frontend integration task.
- The root has no Python configuration for Module 2. Module 1 uses `pyproject.toml` plus `uv.lock`, targets Python `>=3.12`, and therefore demonstrates an existing repository-wide Python packaging preference, but it is not a Module 2 backend configuration.
- No repository-local `AGENTS.md` existed before this task. The root `.gitignore` currently ignores `.venv/`, Python cache/bytecode, and `.env`; it does not ignore SQLite database files.

### Assumptions and human questions

- **Frontend port/CORS:** Vite commonly defaults to 5173, but this repository does not declare a port and the configured plugin may affect it. Confirm the actual `bun run dev` origin before allowing it in CORS. Do not hard-code an origin from convention alone.
- **API base URL:** Choose and document either a `VITE_*` API-base environment variable or a same-origin/proxy approach during frontend integration. No choice is currently present.
- **Python tooling:** Use `uv` for a new Module 2 `pyproject.toml` unless the maintainer directs otherwise; this is a recommendation inferred from Module 1, not an established Module 2 rule.

## 3. Recommended Backend Architecture

Keep one small domain-level repository protocol. Routes depend on that protocol via FastAPI dependency injection, never a list/dictionary or SQLAlchemy session. The in-memory and SQLite implementations return/accept the same domain `Task` data. An app factory can accept a repository (or repository factory) in tests and choose the persistent repository in the production entry point.

```text
module-2/backend/
  pyproject.toml
  taskflow_backend/
    __init__.py
    app.py                       # create_app and production wiring
    api/
      tasks.py                   # four route handlers only
      errors.py                  # contract-shaped HTTP errors/handlers
    domain/
      task.py                    # Task and TaskStatus types
      repositories.py            # TaskRepository protocol
    schemas/
      tasks.py                   # request/response Pydantic models
    repositories/
      memory.py                  # InMemoryTaskRepository
      sqlalchemy.py              # SqlAlchemyTaskRepository and ORM mapping
    db/
      session.py                 # engine/session factory and table creation
  tests/
    conftest.py
    test_tasks_api.py
    test_memory_repository.py
    test_sqlite_repository.py
    test_sqlite_integration.py
```

This is a proposed tree only. Do not introduce services, CQRS, a generic repository, migrations, authentication, or async database complexity unless a later confirmed need requires it.

## 4. Dependencies and Tooling

- `fastapi`: routes, dependency injection, request/response handling, and Pydantic integration.
- `uvicorn[standard]` (or `uvicorn` if the extras are unnecessary): local ASGI development server.
- `sqlalchemy`: SQLite mapping, sessions, and persistence implementation.
- `pydantic`: already used through FastAPI; declare a compatible direct dependency only if imports/configuration require it.
- `pytest`: test runner.
- `httpx`: FastAPI/Starlette HTTP test client transport.

No additional runtime database driver is needed for SQLite because Python includes `sqlite3`. The standard synchronous SQLAlchemy engine is adequate for this small app. Add `pytest` test configuration to a Module 2 backend `pyproject.toml`; absent a Module 2 convention, recommend `uv` and commit its lock file to match Module 1. Do not add frontend testing dependencies until the frontend-test task.

## 5. Domain Model and Validation Design

- Domain `Task`: `id: int`, `title: str`, `description: str`, `status: TaskStatus`, and timezone-aware `created_at`/`updated_at` datetimes. Serialize timestamps as OpenAPI `date-time` values. Generate both at creation; only `updated_at` changes on a successful PATCH.
- `TaskStatus`: a string enum/literal restricted to `todo`, `in_progress`, and `done`.
- Create schema: required string `title`; optional string `description`; optional valid `status` defaulting to `todo`. A title validator strips surrounding whitespace and rejects an empty result.
- Update schema: optional `title`, `description`, and `status`; reject a payload with no recognized fields. Apply title normalization only when title is present.
- Response schema: all six `Task` fields required; normalize an omitted description to `""` before persistence/response.
- Error schema: exactly a `message` string for documented 404 and route-level validation errors.

OpenAPI declares `description` as `type: string`, not nullable. Therefore `null` on create or update should be rejected with 422, rather than silently converted to an empty string. This is a minimal contract-aligned decision, but should be confirmed if the product owner intended `null` to clear a description. An empty string is valid because no `minLength` is declared. Reject unknown request fields, including a PATCH body containing only unknown keys, with 422. A valid PATCH for a missing task returns 404; malformed paths and invalid request data use 422 as documented.

One implementation detail needs review: FastAPI's default validation payload is `detail`, while the contract's `ErrorResponse` requires `message`. The coding agent should add a focused validation-exception handler that produces `{ "message": "..." }` and cover it with tests, while retaining useful detail in the message. Do not claim OpenAPI's description specifies the exact text.

## 6. Mock Repository Stage

Define a focused `TaskRepository` protocol with `list()`, `create(...)`, `update(task_id, changes)`, and `delete(task_id)`. `update` and `delete` should make missingness explicit (for example, return `None`/`False`), leaving the route to turn it into the contract's 404. The in-memory implementation owns an ordered task collection, increments positive integer IDs, generates UTC timestamps, returns copies/value objects rather than mutable internals, and normalizes description through the domain/schema boundary.

Use `create_app(repository=...)` or an equivalent dependency override so each API test gets a fresh `InMemoryTaskRepository`. The production composition root may construct one in-memory repository during this stage. Route code must only request the protocol/dependency; it must never access test data structures directly.

## 7. FastAPI Routes and Error Handling

Put the four handlers in `api/tasks.py`, include the router under `/api`, and use response models/status declarations matching the contract. Each handler validates/parses its request and delegates once to the injected repository:

- GET lists repository tasks and returns 200.
- POST creates a normalized task and returns 201.
- PATCH applies only supplied fields, returns 200, and raises a JSON 404 when the repository reports no task.
- DELETE returns 204 with an empty body, or the same JSON 404 when absent.

Use one small error utility/exception handler to ensure 404 and validation errors follow `{ "message": string }`; do not leak HTML or an uncontracted default error body. Configure CORS only after confirming the frontend origin. While the frontend is served separately, allow the exact local origin(s), the four relevant methods, and required headers; avoid a blanket production-style `*` policy. CORS is not needed for in-process API tests.

## 8. Test Strategy

### Mock-stage API/contract tests (highest priority)

Run route tests with a fresh injected in-memory repository. Cover empty list; create with omitted status (`todo`), `todo`, `in_progress`, and `done`; title trimming; whitespace-only title rejection; invalid status rejection; list contents; title-only, description-only, and status-only PATCH; a PATCH with no fields or unknown fields; missing PATCH; successful DELETE (204); missing DELETE; and absence from a subsequent list.

Assert status codes, response schema/field types, integer IDs, normalized missing description, timestamps, and `{message: string}` error bodies. Add compact checks that unknown properties are rejected and that an individual GET endpoint is not accidentally introduced (for example, expected 405/404 as determined by framework routing, without adding a route).

### Repository tests

Unit-test in-memory ID allocation, copy/isolation behavior, partial changes, timestamp changes, and missing-record results where those behaviors are not already clear in route tests.

### SQLite and persistence tests

After the replacement exists, run the same key API suite against SQLite and direct repository tests using a temporary per-test database. Prove persistence by creating through one repository/app/session lifecycle, constructing a fresh repository/app/session over the same temporary database path, and listing the task. Keep test DB files out of the development database location and clean them via fixtures.

### Frontend tests (later)

Only after the API client replaces the mock, test service request formation, integer ID handling, JSON error mapping, and board create/edit/move/delete/error behavior. Choose a frontend test framework at that task; none is configured today.

## 9. Transition from Mock Store to SQLite

Replace `InMemoryTaskRepository` at application wiring with `SqlAlchemyTaskRepository`, leaving schemas, route signatures, dependency protocol, and route logic unchanged or nearly unchanged. The SQLAlchemy implementation uses a `tasks` table with integer primary-key `id`, non-null `title`, non-null `description` defaulting to `""`, constrained/validated status, and non-null timestamps. Map ORM rows to the domain `Task`, keeping ORM types out of routes.

Create a synchronous SQLite engine and session factory in `db/session.py`; use a per-request/per-operation session lifecycle appropriate to the final concrete implementation. Create tables with `metadata.create_all()` at local startup for this homework. Put the local persistent database at an explicit Module 2 backend data path such as `module-2/backend/data/taskflow.db`, create the directory if needed, and add the exact database file/path pattern to `.gitignore` only in the implementation/documentation task if it is not already ignored. Do not use migration tooling for this small exercise.

For tests, pass a temporary SQLite URL/path through the factory rather than touching the local development database. A later Postgres switch changes configuration/driver and the database/session implementation (plus migration strategy once schema evolution matters), but preserves `TaskRepository`, schemas, and route logic.

## 10. Task-by-Task Implementation Sequence

| # | Task | Purpose, boundaries, and expected files | Commands/tests | Completion criteria / not yet |
| --- | --- | --- | --- | --- |
| 1 | Confirm conventions | Re-read contract, frontend service types, and this plan; confirm Python tool and actual frontend origin. No implementation. | `git status --short`; inspect files; optionally `bun run dev` to observe origin. | Decisions recorded; do not create backend. |
| 2 | Backend skeleton/tooling | Add `backend/pyproject.toml`, package initializers, app factory entry point, and minimal test config. No task behavior. | `uv sync`; `uv run pytest` (collection). | Dependencies resolve and empty test suite collects; no routes yet. |
| 3 | Domain, schemas, protocol | Add domain task/status, Pydantic request/response/error schemas, title validation, repository protocol. No storage or routes. | `uv run pytest tests/...`; formatter/linter if configured. | Contract types validate in focused unit tests; no SQLite. |
| 4 | In-memory repository | Add only `InMemoryTaskRepository` and isolated unit tests. | `uv run pytest tests/test_memory_repository.py`. | Integer IDs/timestamps/partial operations work; no FastAPI routes. |
| 5 | Routes over mock | Add four FastAPI handlers, repository injection, and contract-shaped error handling. | `uv run pytest tests/test_tasks_api.py`. | Handlers use protocol only; do not add persistent store. |
| 6 | Key mock API tests | Complete prioritized endpoint/validation tests from section 8. | `uv run pytest`. | Mock implementation demonstrates core contract; do not integrate frontend. |
| 7 | SQLAlchemy/SQLite repository | Add ORM mapping, engine/session setup, concrete repository, and repository tests. | `uv run pytest tests/test_sqlite_repository.py`. | Temporary SQLite storage works; do not change route code or frontend. |
| 8 | Switch production wiring | Select SQLite repository in app composition and create local tables. | `uv run pytest`; local API smoke test. | App persists locally; mock remains usable for tests; no frontend change. |
| 9 | SQLite persistence/regression | Add API-level SQLite and cross-lifecycle persistence tests. | `uv run pytest`. | All mock and SQLite regressions pass; no CORS guesswork. |
| 10 | Frontend API/CORS integration | Confirm origin/base URL, replace active mock client, convert IDs to `number`, configure narrowly scoped CORS if needed. | `bun run lint`; `bun run build`; backend tests. | UI calls the four routes; do not add features. |
| 11 | Frontend behavior tests | Add the smallest suitable test tooling and behavior coverage. | Chosen frontend test command; `bun run lint`; `bun run build`. | Core UI flows/errors tested; no visual redesign. |
| 12 | Documentation/verification | Document exact run/test instructions; update AI report only with actual work; verify clean scope. | Backend suite, frontend suite/build, `git diff --check`, `git status --short`. | Deliverable is reproducible; do not alter product/contract. |

The exact test-file paths in the early tasks may be adjusted to the final small tree, but each task must remain one independently verifiable Codex turn.

## 11. Acceptance Checklist

- [ ] All behavior matches `product-spec.md`; all request/response behavior matches `openapi.yaml`.
- [ ] Exactly four permitted endpoints exist; individual-task GET does not.
- [ ] Integer IDs, status enum, default `todo`, title normalization, optional-description response normalization, and PATCH semantics are enforced server-side.
- [ ] A route-independent repository protocol is exercised first by a mock repository, then by SQLAlchemy/SQLite.
- [ ] SQLite persists tasks across backend restarts/lifecycles.
- [ ] Core API validation, not-found, delete, and persistence tests pass; frontend behavior tests pass after integration.
- [ ] The frontend service layer uses the real API with integer IDs and agreed base URL/CORS settings.
- [ ] Run instructions, known limitations, and truthful AI usage entries are documented.

## 12. Risks and Human Decisions Needed

1. Confirm the actual frontend dev-server origin before selecting CORS origins; no explicit port was found.
2. Confirm the frontend API base strategy: `VITE_*` variable versus development proxy/same-origin approach.
3. Confirm `uv` as Module 2's Python package manager; it is a strong repository precedent, not an existing Module 2 configuration.
4. OpenAPI's non-null string description implies rejecting explicit `null`; confirm if clearing with `null` was intended. Empty string remains a contract-valid way to clear it.
5. The frontend currently uses string IDs; integration must convert its types and service signatures to integer IDs without preserving incompatible mock IDs.
6. Decide the exact ignored local SQLite path and ensure test fixtures use temporary files so they never modify it.
