# Module 2 — Mini Kanban Board

# TaskFlow

TaskFlow is a small personal Kanban board built as part of DataTalksClub AI Dev Tools Zoomcamp Module 2.

## Project Structure

- `product-spec.md` — product requirements and MVP scope
- `AGENTS.md` — project instructions for AI-assisted development
- `openapi.yaml` — REST API contract
- `frontend/` — TaskFlow frontend
- `backend/` — FastAPI backend
- `docs/ai-usage-report.md` — record of AI-assisted development

## Stack

- Frontend: React, TypeScript, TanStack Start/Router, React Query
- Backend: FastAPI
- Database: SQLite with SQLAlchemy
- Frontend tests: Vitest + React Testing Library

## Run Locally

### Backend

```
cd module-2/backend
uv run uvicorn taskflow_backend.app:create_app --factory --reload --host 127.0.0.1 --port 8000
```

### Backend API:

`http://127.0.0.1:8000`

### Frontend

In another terminal:

```
cd module-2/frontend
bun install
bun run dev -- --port 5173
```

The frontend url:

`http://localhost:5173`

## Tests

### Backend

```
cd module-2/backend
uv run pytest -q tests
```

### Frontend

```
cd module-2/frontend
bun run test
```

## Production Build

```
cd module-2/frontend
bun run build
```

## Database

The local development database is stored at:

`backend/data/taskflow.db`

The SQLite database file is local-only and is not committed to Git.

## API

TaskFlow exposes four MVP endpoints:

- `GET /api/tasks`
- `POST /api/tasks`
- `PATCH /api/tasks/{task_id}`
- `DELETE /api/tasks/{task_id}`

The OpenAPI definition in `openapi.yaml` is the source of truth for the  
frontend/backend contract.

## MVP Scope

TaskFlow supports:

- creating tasks
- editing tasks
- changing task status
- deleting tasks
- persistent SQLite storage

Authentication, multiple users, multiple boards, collaboration,  
real-time features, and deployment are outside the Module 2 MVP.
