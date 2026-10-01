import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .domain.repositories import TaskRepository
from .api.tasks import router as tasks_router, get_repo
from .api.errors import register_error_handlers
from .repositories.sqlalchemy import SqlAlchemyTaskRepository


def _build_repository() -> SqlAlchemyTaskRepository:
    """Construct the production SQLAlchemy repository from ``DATABASE_URL``.

    The repository is built from the ``DATABASE_URL`` environment variable.
    If the variable is missing or malformed, an explicit configuration
    failure is raised — there is no silent SQLite fallback.

    Database connectivity is **not** established by this factory; it is
    verified by Alembic, integration tests, and deployment readiness gates.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. The production repository requires a "
            "PostgreSQL connection URL (e.g. postgresql+psycopg://…). "
            "There is no SQLite runtime fallback."
        )
    return SqlAlchemyTaskRepository(database_url)


def _build_cors_origins() -> list[str]:
    """Build the CORS allowlist from ``CORS_ALLOWED_ORIGINS``.

    The variable is a comma-separated list of exact origins (e.g.
    ``http://localhost:3000``). An empty or unset value raises an explicit
    configuration failure — no wildcard origins are allowed.
    """
    raw = os.environ.get("CORS_ALLOWED_ORIGINS")
    if not raw:
        raise RuntimeError(
            "CORS_ALLOWED_ORIGINS is not set. It must be a comma-separated "
            "list of exact origins (e.g. http://localhost:3000). "
            "Wildcard origins are not allowed."
        )
    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app(repo: TaskRepository | None = None) -> FastAPI:
    app = FastAPI(
        title="TaskFlow API",
        description="REST API for the TaskFlow personal Kanban board.",
        version="1.0.0",
    )

    # If the caller supplies a repository, use it. Otherwise create the
    # production SQLAlchemy repository from ``DATABASE_URL``.
    if repo is None:
        repo = _build_repository()
    app.dependency_overrides[get_repo] = lambda: repo

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_build_cors_origins(),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tasks_router)
    register_error_handlers(app)

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
