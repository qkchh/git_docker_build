import os

from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gitdockerbuild.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Each entry: (table, column, column_def)
# Safe to run repeatedly — errors on "duplicate column" are silently ignored.
_MIGRATIONS = [
    ("repository", "build_context", "TEXT"),
]


def create_db():
    SQLModel.metadata.create_all(engine)
    _run_migrations()


def _run_migrations():
    with engine.connect() as conn:
        for table, column, col_def in _MIGRATIONS:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
                conn.commit()
            except Exception:
                pass  # column already exists


def get_session():
    with Session(engine) as session:
        yield session
