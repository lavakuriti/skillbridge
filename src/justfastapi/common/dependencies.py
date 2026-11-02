from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session


def get_database_session(
    request: Request,
) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()

    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
