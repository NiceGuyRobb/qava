from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from qava.api.routers import questionnaires, sessions


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from qava.api.dependencies import get_db_manager

    manager = get_db_manager()
    await manager.initialize()
    try:
        yield
    finally:
        await manager.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Qava MVP API",
        version="1.0.0",
        description=(
            "Contract-first authoring, interviewing, projection, health, and explicit publication."
        ),
        lifespan=lifespan,
    )
    app.include_router(questionnaires.router)
    app.include_router(sessions.router)
    return app


app = create_app()
