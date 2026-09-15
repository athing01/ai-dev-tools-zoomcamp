from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from starlette import status

def register_error_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Extract the human-readable message from the first error
        error_msg = exc.errors()[0]["msg"] if exc.errors() else "Validation failed"
        return JSONResponse(
            status_code=422,
            content={"message": error_msg},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # FastAPI HTTPException.detail can be a string or a dict
        message = exc.detail
        if isinstance(message, dict) and "message" in message:
            message = message["message"]

        return JSONResponse(
            status_code=exc.status_code,
            content={"message": message if isinstance(message, str) else str(message)},
        )
