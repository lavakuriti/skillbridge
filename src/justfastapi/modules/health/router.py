from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text, Engine
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
def health_check():
    return {"status": "healthy"}


@router.get("/ready")
def ready_ness_check(request: Request):
    try:
        db_engine: Engine = request.app.state.db_pool
        with db_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {"status": "ready", "db": "connected"}
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Application is not ready") from exc
