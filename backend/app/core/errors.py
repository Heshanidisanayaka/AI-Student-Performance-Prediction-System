import traceback
from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings
from app.core.logging import logger


class AppException(Exception):
    """Base application exception for domain-specific errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def setup_error_handlers(app: FastAPI) -> None:
    """Registers centralized exception handlers to the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            f"AppException: status={exc.status_code} path={request.url.path} msg={exc.message}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "type": "AppException",
                    "code": exc.status_code,
                    "message": exc.message,
                    "details": jsonable_encoder(exc.details) if exc.details else None,
                },
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        logger.warning(
            f"HTTPException: status={exc.status_code} path={request.url.path} detail={exc.detail}"
        )
        headers = getattr(exc, "headers", None)
        return JSONResponse(
            status_code=exc.status_code,
            headers=headers,
            content={
                "success": False,
                "error": {
                    "type": "HTTPException",
                    "code": exc.status_code,
                    "message": exc.detail,
                    "details": None,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            f"ValidationError: path={request.url.path} errors={exc.errors()}"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "type": "ValidationError",
                    "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "message": "Input validation failed.",
                    "details": jsonable_encoder(exc.errors()),
                },
            },
        )

    @app.exception_handler(OperationalError)
    async def db_operational_exception_handler(
        request: Request, exc: OperationalError
    ) -> JSONResponse:
        logger.error(
            f"Database Connection Error: {exc} | Path: {request.url.path}\n"
            f"{traceback.format_exc()}"
        )
        details = str(exc.orig) if settings.DEBUG and hasattr(exc, "orig") else None
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "type": "DatabaseOperationalError",
                    "code": status.HTTP_503_SERVICE_UNAVAILABLE,
                    "message": "Database connection error. Service is temporarily unavailable.",
                    "details": details,
                },
            },
        )

    @app.exception_handler(IntegrityError)
    async def db_integrity_exception_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        logger.warning(
            f"Database Integrity Violation: {exc} | Path: {request.url.path}"
        )
        details = str(exc.orig) if settings.DEBUG and hasattr(exc, "orig") else None
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "type": "DatabaseIntegrityError",
                    "code": status.HTTP_409_CONFLICT,
                    "message": "Database constraint violation occurred.",
                    "details": details,
                },
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.error(
            f"SQLAlchemy Database Error: {exc} | Path: {request.url.path}\n"
            f"{traceback.format_exc()}"
        )
        details = str(exc) if settings.DEBUG else None
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "type": "DatabaseError",
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An internal database error occurred.",
                    "details": details,
                },
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            f"Unhandled Server Error: {exc} | Path: {request.url.path}\n"
            f"{traceback.format_exc()}"
        )
        details = str(exc) if settings.DEBUG else None
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "type": "InternalServerError",
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An unexpected internal server error occurred.",
                    "details": details,
                },
            },
        )
