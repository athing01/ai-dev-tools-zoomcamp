# Module 2 Agent Guide

TaskFlow is a single-user personal Mini Kanban Board. The MVP supports creating, listing, partially updating, moving by status, and deleting tasks only.

## Sources of truth

- Read `product-spec.md` for product behavior and `openapi.yaml` for the API contract before changing code. OpenAPI controls API behavior.
- Inspect relevant existing files before each change. Work on one small task at a time and run the relevant tests after it.

## Contract and stack

- Only these endpoints are permitted: `GET /api/tasks`, `POST /api/tasks`, `PATCH /api/tasks/{task_id}`, and `DELETE /api/tasks/{task_id}`. Do not add `GET /api/tasks/{task_id}`.
- Task IDs are positive integers. Status is exactly `todo`, `in_progress`, or `done`. Omitted create status defaults to `todo`; PATCH is partial for title, description, and/or status; trim titles and reject empty or whitespace-only titles.
- Backend stack: FastAPI, SQLAlchemy, and SQLite. First implement and test against a small in-memory repository behind a repository/protocol abstraction; then add the SQLAlchemy/SQLite implementation without coupling routes to it.

## Boundaries

- Do not modify `module-1/`, `product-spec.md`, `openapi.yaml`, or frontend code unless a separately scoped task explicitly requires it. Do not reopen product/API decisions without documenting a concrete contradiction.
- No authentication, users, boards, labels, due dates, priority, drag-and-drop, realtime features, deployment work, or unnecessary layers.

## Completion discipline

- After each task, report changed files, commands run, test results, and known limitations to the human reviewer.
- `docs/ai-usage-report.md` is maintained by the human owner. Do not create, modify, or update it unless the human explicitly asks you to do so.
- When asked to update the AI usage report, record only work that actually happened; never invent prompts, tool output, review actions, or decisions.
