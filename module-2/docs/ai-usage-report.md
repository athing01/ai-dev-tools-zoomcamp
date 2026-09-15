# AI Usage Report — TaskFlow

## 1. Product Specification

### AI Tool
ChatGPT

### Purpose
Turn the initial idea for a small personal Kanban board into a
structured product specification before implementation.

### Input
Initial product idea and discussion of the desired TaskFlow behavior,
including user stories, acceptance criteria, technical constraints,
and non-goals.

### Output
`module-2/product-spec.md` containing:
- product overview and target user
- goals
- user stories and acceptance criteria
- functional requirements
- non-goals
- future enhancements

### Human Review / Decisions
- Reviewed the specification and refined the MVP scope.
- Chose a single-user Kanban board with three statuses.
- Decided that task creation should allow selecting the initial status.
- Defined the REST API behavior and persistence requirements.
- Explicitly excluded authentication, multiple boards, collaboration,
  drag-and-drop, and other future enhancements.

## 2. Frontend Prototype

### AI Tool
Lovable

### Purpose
Create an interactive frontend prototype for TaskFlow using a mocked
backend service.

### Input
Product requirements for the personal Kanban board.

### Output
- Interactive three-column Kanban board.
- Create, edit, move, and delete task flows.
- Mock `TaskService` and `mockTaskService`.
- React Query integration.
- Loading, validation, and error states.

### Human Review / Decisions
- Reviewed the prototype against `product-spec.md`.
- Confirmed the main user flows and service-layer architecture.
- Found that the prototype uses string task IDs while the product
  specification requires integer IDs.
- Found that the mock service does not perform runtime validation of
  invalid status values.
- Kept the generated prototype as the frontend baseline and deferred
  contract-level alignment to the OpenAPI stage.
- Imported the frontend into `module-2/frontend/` and excluded
  Lovable-specific project metadata from the coursework repository.

## 3. OpenAPI Contract

### AI Tool
ChatGPT

### Purpose
Define the API contract between the TaskFlow frontend and backend
based on the frontend service layer and product requirements.

### Input
The TaskFlow product specification and the frontend service layer
created by Lovable, including `TaskService`, `CreateTaskInput`,
and `UpdateTaskInput`.

### Output
`module-2/openapi.yaml` defining:
- REST endpoints for listing, creating, updating, and deleting tasks.
- Request and response schemas.
- Task status values: `todo`, `in_progress`, and `done`.
- Validation and not-found responses.
- No authentication for the MVP.

### Human Review / Decisions
- Reviewed the frontend service layer before defining the API contract.
- Chose four MVP endpoints:
  `GET /api/tasks`,
  `POST /api/tasks`,
  `PATCH /api/tasks/{task_id}`,
  and `DELETE /api/tasks/{task_id}`.
- Omitted `GET /api/tasks/{task_id}` because the current frontend
  does not require fetching an individual task.
- Chose integer task IDs to match the product specification, even though
  the Lovable prototype uses string IDs.
- Kept task status updates within the general `PATCH` endpoint instead
  of introducing a separate status endpoint.
- Defined the OpenAPI contract as the source of truth for the backend
  implementation.

## 4. Backend

### AI Tool
- ChatGPT / GPT-5.6 Terra — planning and review
- Codex CLI / Gemma 4 31B — implementation

### Purpose
Implement a FastAPI backend against the OpenAPI contract, starting with
an in-memory repository and tests for the key endpoints.

### Input
The TaskFlow product specification, `module-2/openapi.yaml`,
`module-2/AGENTS.md`, and the backend implementation plan.

### Output
`module-2/backend/` containing:
- FastAPI application and API routes for the four MVP endpoints.
- Task domain model, status values, and Pydantic request/response schemas.
- Repository protocol used by the API layer.
- In-memory repository for the initial backend stage.
- Contract-shaped validation and not-found error responses.
- API and repository tests for the in-memory implementation.

### Human Review / Decisions
- Reviewed the backend structure and kept the API layer independent
  of the repository implementation.
- Confirmed that only the four endpoints defined in `openapi.yaml`
  are implemented.
- Confirmed positive integer task IDs, allowed status values,
  default `todo` status, title trimming, and rejection of blank titles.
- Reviewed the partial `PATCH` behavior and the `404` / `422` response
  behavior against the contract.
- Kept the in-memory repository as the first implementation and deferred
  SQLAlchemy/SQLite persistence to the database stage.
- Reviewed the added API coverage and kept the test suite at 62 passing
  tests before moving to the SQLite stage.

## 5. Database and SQLite Persistence

### AI Tool
- ChatGPT / GPT-5.6 Terra — planning and review
- Codex CLI / gpt-oss-20b — implementation

### Purpose
Add SQLAlchemy/SQLite persistence and wire it into the production FastAPI
application while preserving the in-memory repository for isolated API tests.
Then verify persistence across application lifecycles at the API level.

### Input
The TaskFlow product specification, `module-2/openapi.yaml`,
`module-2/AGENTS.md`, the backend implementation plan, and the existing
FastAPI/in-memory repository implementation.

### Output
- SQLAlchemy repository implementation backed by SQLite.
- SQLAlchemy ORM mapping and database/session setup.
- Production app wiring to `module-2/backend/data/taskflow.db`.
- Repository injection in `create_app()` so tests can continue to use
  a fresh in-memory repository.
- API-level SQLite persistence test using a temporary database.
- `.gitignore` rule for the local SQLite database file.

### Human Review / Decisions
- Reviewed the SQLAlchemy repository implementation and kept the API layer
  dependent on the repository protocol rather than the concrete database implementation.
- Confirmed SQLite status values are stored as the contract values
  `todo`, `in_progress`, and `done`.
- Confirmed UTC timestamp handling, including normalization when SQLite
  returns naive datetimes.
- Chose `module-2/backend/data/taskflow.db` as the local development database
  path and kept it out of version control.
- Kept `create_app()` on SQLite by default, while allowing an explicit
  repository to be injected for tests.
- Updated API tests to use a fresh `InMemoryTaskRepository` per test so
  test state does not leak into the persistent development database.
- Added an API-level persistence test that creates and updates a task with
  one app instance, verifies the data through a newly created app instance
  using the same temporary SQLite file, deletes the task, and verifies the
  deletion through a third app instance.
- Ran the test suite in the WSL development environment rather than relying
  on the coding-agent sandbox for test execution.

## 6. Frontend Integration and Behavior Tests

### AI Tool
- ChatGPT / GPT-5.6 Terra — planning and review
- Codex CLI / Gemma 4 31B — frontend integration implementation
- Codex / GPT-5.5 Medium — frontend behavior tests

### Purpose
Connect the TaskFlow frontend to the real backend API and add frontend
behavior tests covering the core flows defined by the product specification
and API contract.

### Input
The TaskFlow product specification, `module-2/openapi.yaml`,
`module-2/AGENTS.md`, the backend implementation plan, and the existing
frontend and backend implementation.

### Output
- Replaced the frontend mock task service with a REST API client.
- Aligned frontend task IDs from `string` to `number` to match the contract.
- Added narrowly scoped CORS configuration for the local frontend origin.
- Added Vitest and React Testing Library for frontend behavior tests.
- Added tests covering loading, listing, error handling, task creation,
  task editing, deletion, and status changes.
- Added frontend test configuration and setup.
- Updated the frontend package manifest and `bun.lock` with the test tooling.

### Human Review / Decisions
- Kept `openapi.yaml` and the backend contract as the source of truth
  when resolving the frontend string-ID mismatch.
- Removed the mock service from the active frontend path rather than
  changing the backend contract to match the prototype.
- Limited CORS to the local Vite development origin.
- Kept frontend tests focused on observable TaskFlow behavior rather than
  visual details or implementation-specific snapshots.
- Corrected test expectations where the existing form behavior sends both
  title and description during task updates.
- Mocked the Radix dropdown primitive in the status-change test to keep the
  behavior test deterministic in the jsdom environment.
- Kept unrelated formatting and pre-existing lint issues outside the scope
  of this task.

### Verification
- Backend test suite: 77 tests passed.
- Frontend behavior tests: 8 tests passed.
- Frontend production build: passed.
- `git diff --check`: passed.
