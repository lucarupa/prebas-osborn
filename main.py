from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables and seed initial data on startup
    yield


app = FastAPI(
    title="Creative Assets Management API",
    description="Sistema de gestión de activos creativos",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

def _error_response(status_code: int, code: str, message: str, details: list[Any] = []) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [
        {
            "field": " -> ".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    return _error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        details=details,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        return _error_response(
            status_code=exc.status_code,
            code=detail.get("code", "ERROR"),
            message=detail.get("message", str(exc.detail)),
            details=detail.get("details", []),
        )
    return _error_response(
        status_code=exc.status_code,
        code="HTTP_ERROR",
        message=str(detail),
        details=[],
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return _error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred.",
        details=[str(exc)],
    )

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}