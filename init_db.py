"""Create the SQLite tables for the Day 10 learning project.

Run from the repository root:
    .venv\\Scripts\\python.exe init_db.py

For production schema changes, use Alembic migrations instead of create_all().
"""

from sqlalchemy import inspect

from app.database import Base, DATABASE_URL, engine
from app.models import Conversation, Message, User  # noqa: F401


def init_database() -> None:
    """Create missing tables and print the resulting table names."""
    Base.metadata.create_all(bind=engine)
    table_names = inspect(engine).get_table_names()
    print(f"Database: {DATABASE_URL}")
    print(f"Tables: {', '.join(table_names)}")


if __name__ == "__main__":
    init_database()
