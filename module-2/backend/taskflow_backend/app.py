from fastapi import FastAPI

def create_app() -> FastAPI:
    """
    TaskFlow Backend App Factory.
    
    This function initializes the FastAPI application.
    Business routes will be included here in later tasks.
    """
    app = FastAPI(
        title="TaskFlow API",
        description="REST API for the TaskFlow personal Kanban board.",
        version="1.0.0",
    )
    
    # Routes will be added here (e.g., app.include_router(tasks_router))
    
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
