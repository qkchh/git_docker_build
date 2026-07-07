from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


class Repository(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    source_type: str  # "remote" | "local"
    git_url: Optional[str] = None
    local_path: Optional[str] = None
    build_context: Optional[str] = None  # subdirectory containing Dockerfile, e.g. "backend"
    created_at: datetime = Field(default_factory=utc_now)


class RepoEnv(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("repo_id", "key", name="uq_repo_env_key"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id")
    key: str
    value: str


class Build(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id")
    commit_sha: str
    commit_message: Optional[str] = None
    image_name: str
    status: str = "pending"  # pending | running | success | failed
    log: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
