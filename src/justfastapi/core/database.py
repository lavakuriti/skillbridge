from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def create_database_pool(database_url: str, min_size: int, max_size: int) -> Engine:
    return create_engine(
        database_url,
        pool_size=min_size,
        max_overflow=max(0, max_size - min_size),
        pool_pre_ping=True,
        pool_recycle=1000,
    )


def create_session_factory(
    engine: Engine,
) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
