from fastapi import FastAPI
from justfastapi.core.config import settings
from justfastapi.core.database import create_database_pool, create_session_factory
from justfastapi.core.logging import configure_logging
from justfastapi.modules.health.router import router as health_router
from justfastapi.modules.iam.router import router as iam_router
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("SETTINGS:", repr(settings.database_url))
    print("ENV:", repr(__import__("os").environ.get("DATABASE_URL")))
    print("settings.database_url", settings.database_url)
    configure_logging(settings.debug)

    db_pool = create_database_pool(
        database_url=settings.database_url,
        max_size=settings.db_pool_max_size,
        min_size=settings.db_pool_min_size,
    )
    app.state.db_pool = db_pool
    app.state.session_factory = create_session_factory(db_pool)

    try:
        yield
    finally:
        db_pool.dispose()


app = FastAPI(
    title="SkillBridge AI",
    description="AI Education and Employment Workforce Platform",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(iam_router)
