"""Local API application factory. Domain calculations do not require this module."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.analytics import router as analytics_router
from app.api.routes import router
from app.database.session import Database
from app.domain.version import MODEL_VERSION
from app.services.scenarios import (
    InvalidStoredScenarioError,
    ScenarioNotFoundError,
    UnsupportedModelVersionError,
)


def create_app(database_url: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        database = Database(database_url or os.getenv("DATABASE_URL", "sqlite:///./yummy_flow.db"))
        application.state.database = database
        try:
            database.require_current_schema()
            yield
        finally:
            database.close()

    application = FastAPI(
        title="Yummy Flow Digital Twin",
        version="0.1.0",
        lifespan=lifespan,
        description=(
            "Quick-commerce decision support using illustrative synthetic assumptions. "
            "A new portfolio project; not historical Yummy Flow technology or operating data. "
            "Amounts are VAT-exclusive EUR. Decimal values are returned as strings."
        ),
    )
    application.include_router(router)
    application.include_router(analytics_router)

    @application.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok", "model_version": MODEL_VERSION}

    @application.exception_handler(ScenarioNotFoundError)
    async def not_found(request: Request, exc: ScenarioNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @application.exception_handler(UnsupportedModelVersionError)
    async def unsupported(request: Request, exc: UnsupportedModelVersionError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @application.exception_handler(InvalidStoredScenarioError)
    async def invalid_snapshot(request: Request, exc: InvalidStoredScenarioError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @application.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "Scenario storage is unavailable"})

    @application.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Echoing invalid input can leak user data or fail JSON serialization for NaN.
        errors = [
            {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": errors})

    return application


app = create_app()
