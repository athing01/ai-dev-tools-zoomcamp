from fastapi import FastAPI
from .api.tasks import router as tasks_router, get_repo
from .api.errors import register_error_handlers
from .repositories.memory import InMemoryTaskRepository

def create_app() -> FastAPI:
    app = FastAPI(
        title="TaskFlow API",
        description="REST API for the TaskFlow personal Kanban board.",
        version="1.0.0",
    )

    # Singleton repository for in-memory stage
    repo = InMemoryTaskRepository()
    app.dependency_overrides[get_repo] = lambda: repo

    app.include_router(tasks_router)
    register_error_handlers(app)

    return app

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
