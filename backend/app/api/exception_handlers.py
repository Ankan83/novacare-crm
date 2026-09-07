"""
Global exception handlers for the Nova API.
"""

from fastapi import FastAPI, Request # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from sqlalchemy.exc import SQLAlchemyError # type: ignore


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers.
    """

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request,
        exc: SQLAlchemyError,
    ):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "A database error occurred."
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred."
            },
        )