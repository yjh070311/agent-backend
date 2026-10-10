"""SQLAlchemy engine, session factory, model base, and FastAPI dependency."""

from collections.abc import Generator
from pathlib import Path
from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'agent_backend.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(
    dbapi_connection: SQLiteConnection,
    connection_record: object,
) -> None:
    """Enable SQLite foreign-key enforcement for ON DELETE CASCADE."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Base class that registers ORM models in Base.metadata."""


def get_db() -> Generator[Session, None, None]:
    """Yield one database session per request and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
