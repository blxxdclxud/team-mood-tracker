"""FastAPI application entry point for Team Mood Tracker."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.database import init_db
from src.routes import moods, stats


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown events."""
    init_db()
    yield


app = FastAPI(
    title="Team Mood Tracker",
    description=(
        "A lightweight internal tool for agile teams to monitor collective well-being. "
        "Submit mood entries (emoji/rating + comment) and explore historical trends."
    ),
    version="0.1.0",
    contact={"name": "Team"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

app.include_router(moods.router)
app.include_router(stats.router)


@app.get(
    "/health",
    summary="Health check",
    description="Returns a simple OK response to confirm the service is running.",
    tags=["meta"],
    responses={
        200: {
            "description": "Service is healthy",
            "content": {"application/json": {"example": {"status": "ok"}}},
        }
    },
)
def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}
