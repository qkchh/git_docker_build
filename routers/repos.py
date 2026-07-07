from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import Build, Repository, RepoEnv
from services import git_service

router = APIRouter(prefix="/api/repos", tags=["repos"])


def _valid_env_key(key: str) -> bool:
    return bool(key) and key.replace("_", "a").isascii() and key.replace("_", "a").isalnum() and not key[0].isdigit()


class RepoCreate(BaseModel):
    name: str
    source_type: Literal["remote", "local"]
    git_url: Optional[str] = None
    local_path: Optional[str] = None
    build_context: Optional[str] = None  # e.g. "backend" or "frontend"


@router.get("")
def list_repos(session: Session = Depends(get_session)):
    return session.exec(select(Repository)).all()


@router.post("")
def create_repo(data: RepoCreate, session: Session = Depends(get_session)):
    data.name = data.name.strip()
    if not data.name:
        raise HTTPException(status_code=400, detail="name cannot be empty")
    if data.source_type == "remote" and not data.git_url:
        raise HTTPException(status_code=400, detail="git_url is required for remote repos")
    if data.source_type == "local":
        if not data.local_path:
            raise HTTPException(status_code=400, detail="local_path is required for local repos")
        local_path = Path(data.local_path).expanduser().resolve()
        if not local_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path does not exist: {data.local_path}")
        if not (local_path / ".git").exists():
            raise HTTPException(status_code=400, detail=f"Not a Git repository: {data.local_path}")
        data.local_path = str(local_path)

    if data.build_context:
        context = Path(data.build_context)
        if context.is_absolute() or ".." in context.parts:
            raise HTTPException(status_code=400, detail="build_context must stay inside the repository")
        data.build_context = context.as_posix().strip("./") or None

    repo = Repository(**data.model_dump())
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return repo


@router.delete("/{repo_id}")
def delete_repo(repo_id: int, session: Session = Depends(get_session)):
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    builds = session.exec(select(Build).where(Build.repo_id == repo_id)).all()
    envs = session.exec(select(RepoEnv).where(RepoEnv.repo_id == repo_id)).all()
    for build in builds:
        git_service.delete_build_workspace(build.id)
        session.delete(build)
    for env in envs:
        session.delete(env)
    git_service.delete_repo_workspace(repo)
    session.delete(repo)
    session.commit()
    return {"ok": True}


@router.get("/{repo_id}/commits")
def get_commits(repo_id: int, session: Session = Depends(get_session)):
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    try:
        repo_path = git_service.get_repo_path(repo, fetch=True)
        return git_service.get_commits(repo_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repo_id}/envs")
def list_envs(repo_id: int, session: Session = Depends(get_session)):
    return session.exec(select(RepoEnv).where(RepoEnv.repo_id == repo_id)).all()


class EnvCreate(BaseModel):
    key: str
    value: str


@router.post("/{repo_id}/envs")
def add_env(repo_id: int, data: EnvCreate, session: Session = Depends(get_session)):
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    key = data.key.strip()
    if not _valid_env_key(key):
        raise HTTPException(status_code=400, detail="Invalid environment variable name")
    env = session.exec(
        select(RepoEnv).where(RepoEnv.repo_id == repo_id, RepoEnv.key == key)
    ).first()
    if env:
        env.value = data.value
    else:
        env = RepoEnv(repo_id=repo_id, key=key, value=data.value)
    session.add(env)
    session.commit()
    session.refresh(env)
    return env


class EnvBulkImport(BaseModel):
    content: str  # raw .env file text


@router.post("/{repo_id}/envs/bulk")
def bulk_import_envs(repo_id: int, data: EnvBulkImport, session: Session = Depends(get_session)):
    """Parse raw .env content and append to repo's env vars (skips comments/blanks)."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    imported = 0
    for line in data.content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        if not _valid_env_key(key):
            continue
        existing = session.exec(
            select(RepoEnv).where(RepoEnv.repo_id == repo_id, RepoEnv.key == key)
        ).first()
        if existing:
            existing.value = value
            session.add(existing)
        else:
            session.add(RepoEnv(repo_id=repo_id, key=key, value=value))
        imported += 1

    session.commit()
    return {"imported": imported}


class EnvUpdate(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None


@router.patch("/{repo_id}/envs/{env_id}")
def update_env(repo_id: int, env_id: int, data: EnvUpdate, session: Session = Depends(get_session)):
    env = session.get(RepoEnv, env_id)
    if not env or env.repo_id != repo_id:
        raise HTTPException(status_code=404, detail="Env var not found")
    if data.key is not None:
        key = data.key.strip()
        if not _valid_env_key(key):
            raise HTTPException(status_code=400, detail="Invalid environment variable name")
        duplicate = session.exec(
            select(RepoEnv).where(
                RepoEnv.repo_id == repo_id,
                RepoEnv.key == key,
                RepoEnv.id != env_id,
            )
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Environment variable already exists")
        env.key = key
    if data.value is not None:
        env.value = data.value
    session.add(env)
    session.commit()
    session.refresh(env)
    return env


@router.delete("/{repo_id}/envs/{env_id}")
def delete_env(repo_id: int, env_id: int, session: Session = Depends(get_session)):
    env = session.get(RepoEnv, env_id)
    if not env or env.repo_id != repo_id:
        raise HTTPException(status_code=404, detail="Env var not found")
    session.delete(env)
    session.commit()
    return {"ok": True}


@router.get("/{repo_id}/branches")
def get_branches(repo_id: int, session: Session = Depends(get_session)):
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    try:
        repo_path = git_service.get_repo_path(repo)
        return git_service.get_branches(repo_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
