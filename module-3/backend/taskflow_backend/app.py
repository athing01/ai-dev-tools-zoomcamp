from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from .domain.repositories import TaskRepository
from typing import Optional
from .api.tasks import router as tasks_router, get_repo
from .api.errors import register_error_handlers
from .repositories.sqlalchemy import SqlAlchemyTaskRepository

def create_app(repo: Optional[TaskRepository] = None) -> FastAPI:
    app = FastAPI(
        title="TaskFlow API",
        description="REST API for the TaskFlow personal Kanban board.",
        version="1.0.0",
    )

    # If the caller supplies a repository, use it. Otherwise create the
    # production SQLite repository.
    if repo is None:
        # Singleton repository for production: SQLite via SQLAlchemy.
        # The database file resides under ``../data/taskflow.db`` relative to this
        # package, matching the build‑plan. Ensure the directory exists.
        data_dir = Path(__file__).resolve().parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        db_path = data_dir / "taskflow.db"
        repo = SqlAlchemyTaskRepository(db_path=str(db_path))
    app.dependency_overrides[get_repo] = lambda: repo

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
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
