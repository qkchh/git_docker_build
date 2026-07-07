import os
import logging

from sqlalchemy import event, text
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gitdockerbuild.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
logger = logging.getLogger(__name__)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Each entry: (table, column, column_def)
# Safe to run repeatedly — errors on "duplicate column" are silently ignored.
_MIGRATIONS = [
    ("repository", "build_context", "TEXT"),
]


def create_db():
    # Ensure all SQLModel tables are registered regardless of import order.
    import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _run_migrations()


def _run_migrations():
    with engine.connect() as conn:
        for table, column, col_def in _MIGRATIONS:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
                conn.commit()
            except Exception as exc:
                if "duplicate column" not in str(exc).lower():
                    logger.exception("Database migration failed: %s.%s", table, column)
                    raise
        # Older releases allowed duplicate keys. Keep the latest value, then enforce one key per repo.
        conn.execute(
            text(
                "DELETE FROM repoenv WHERE id NOT IN "
                "(SELECT MAX(id) FROM repoenv GROUP BY repo_id, key)"
            )
        )
        conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS uq_repo_env_key ON repoenv (repo_id, key)")
        )
        conn.commit()


def recover_interrupted_builds():
    """A process restart cannot resume a Docker subprocess; mark stale rows failed."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE build SET status = 'failed', "
                "log = COALESCE(log || char(10), '') || '[ERROR] Service restarted during build' "
                "WHERE status = 'running'"
            )
        )


def get_session():
    with Session(engine) as session:
        yield session
