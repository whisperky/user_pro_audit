from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from psycopg2 import Error as PostgresError
from typing import Any, Dict, Optional

class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None,
        error_code: str = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code

class DatabaseException(AppException):
    def __init__(self, detail: str = "Database error occurred", original_error: Exception = None):
        super().__init__(
            status_code=500,
            detail=detail,
            error_code="DATABASE_ERROR"
        )
        self.original_error = original_error

class ValidationException(AppException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )

class AuthenticationException(AppException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=401,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
            error_code="AUTHENTICATION_ERROR"
        )

class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=404,
            detail=detail,
            error_code="NOT_FOUND"
        )

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "status": exc.status_code
            }
        }
    )

async def database_exception_handler(request: Request, exc: PostgresError):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "An error occurred while processing your request",
                "status": 500
            }
        }
    )

async def validation_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc),
                "status": 400
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "status": 500
            }
        }
    )
