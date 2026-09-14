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
