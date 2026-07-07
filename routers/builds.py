import json
import re
import threading
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy import update

from database import engine, get_session
from models import Build, Repository, RepoEnv
from services import docker_service, git_service
from services.docker_service import BuildCancelled

# build_id -> cancel Event for currently running builds
_cancel_events: dict[int, threading.Event] = {}
_cancel_events_lock = threading.Lock()

router = APIRouter(prefix="/api/builds", tags=["builds"])


class BuildCreate(BaseModel):
    repo_id: int
    commit_sha: str
    commit_message: Optional[str] = ""


def _image_name(repo_name: str, commit_sha: str) -> str:
    name = re.sub(r"[^a-z0-9._-]+", "-", repo_name.lower()).strip("-._")
    return f"{name or 'repo'}:{commit_sha[:8].lower()}"


def _validated_build_dir(build_root: Path, build_context: str | None) -> Path:
    root = build_root.resolve()
    build_dir = (root / build_context).resolve() if build_context else root
    if build_dir != root and root not in build_dir.parents:
        raise ValueError("build_context must stay inside the repository")
    if not build_dir.is_dir():
        raise ValueError(f"Build context does not exist: {build_context}")
    return build_dir


def _sse(data: str) -> str:
    # Escape newlines so each SSE message is on one line
    return f"data: {json.dumps(data)}\n\n"


@router.get("")
def list_builds(session: Session = Depends(get_session)):
    builds = session.exec(select(Build).order_by(Build.created_at.desc())).all()
    return builds


@router.post("")
def create_build(data: BuildCreate, session: Session = Depends(get_session)):
    repo = session.get(Repository, data.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    data.commit_sha = data.commit_sha.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", data.commit_sha):
        raise HTTPException(status_code=400, detail="Invalid Git commit SHA")
    image_name = _image_name(repo.name, data.commit_sha)
    build = Build(
        repo_id=data.repo_id,
        commit_sha=data.commit_sha,
        commit_message=data.commit_message,
        image_name=image_name,
        status="pending",
    )
    session.add(build)
    session.commit()
    session.refresh(build)
    return build


@router.get("/{build_id}")
def get_build(build_id: int, session: Session = Depends(get_session)):
    build = session.get(Build, build_id)
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    return build


@router.get("/{build_id}/stream")
def stream_build(build_id: int):
    """SSE endpoint — streams live docker build output."""

    def generate():
        cancel_event = threading.Event()

        with Session(engine) as session:
            build = session.get(Build, build_id)
            if not build:
                yield _sse("[ERROR] Build not found")
                return

            repo = session.get(Repository, build.repo_id)
            if not repo:
                yield _sse("[ERROR] Repo not found")
                return

            claim = session.exec(
                update(Build)
                .where(Build.id == build_id, Build.status == "pending")
                .values(status="running")
            )
            session.commit()
            if claim.rowcount != 1:
                yield _sse(f"[ERROR] Build is already {build.status}")
                return

            session.refresh(build)
            with _cancel_events_lock:
                _cancel_events[build_id] = cancel_event

            logs: list[str] = []

            def persist(status: str):
                build.status = status
                build.log = "\n".join(logs)
                session.add(build)
                session.commit()

            try:
                # Step 1 — create an isolated worktree for this build.
                yield _sse("[INFO] Resolving repository...")
                yield _sse(f"[INFO] Checking out commit {build.commit_sha[:8]}...")
                build_root = git_service.prepare_build_path(repo, build.id, build.commit_sha)

                build_dir = _validated_build_dir(build_root, repo.build_context)

                # Step 3 — auto-detect build mode
                has_compose = (
                    (build_dir / "docker-compose.yml").exists()
                    or (build_dir / "docker-compose.yaml").exists()
                )
                has_dockerfile = (build_dir / "Dockerfile").exists()

                if not has_compose and not has_dockerfile:
                    raise RuntimeError(
                        f"No Dockerfile or docker-compose.yml found in: {build_dir}"
                    )

                # Step 4 — load env vars
                envs = session.exec(
                    select(RepoEnv).where(RepoEnv.repo_id == repo.id)
                ).all()
                env_vars = {e.key: e.value for e in envs}
                if env_vars:
                    yield _sse(f"[INFO] Injecting {len(env_vars)} env var(s)")

                # Step 5 — build
                if has_compose:
                    yield _sse("[INFO] Found docker-compose.yml → docker compose build")
                    for line in docker_service.compose_build(build_dir, env_vars, cancel_event):
                        logs.append(line)
                        yield _sse(line)
                else:
                    yield _sse(f"[INFO] Starting docker build → {build.image_name}")
                    for line in docker_service.build_image(build_dir, build.image_name, env_vars, cancel_event):
                        logs.append(line)
                        yield _sse(line)

                persist("success")
                yield _sse("[DONE] Build succeeded")

                # Auto-run
                try:
                    container_name = repo.name.lower().replace(" ", "-").replace("_", "-")
                    if has_compose:
                        yield _sse("[INFO] Running: docker compose up -d ...")
                        docker_service.compose_up(build_dir, env_vars)
                        yield _sse("[INFO] Containers started")
                    else:
                        yield _sse(f"[INFO] Running container '{container_name}' ...")
                        cid = docker_service.run_image(build.image_name, container_name)
                        yield _sse(f"[INFO] Container started: {container_name} ({cid})")
                except Exception as run_err:
                    yield _sse(f"[WARN] Build succeeded but failed to start container: {run_err}")

                yield _sse("[DONE] All done")

            except BuildCancelled:
                logs.append("Cancelled by user")
                persist("cancelled")
                yield _sse("[CANCELLED] Build cancelled")

            except Exception as e:
                logs.append(str(e))
                persist("failed")
                yield _sse(f"[ERROR] {e}")

            finally:
                with _cancel_events_lock:
                    _cancel_events.pop(build_id, None)

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/{build_id}/cancel")
def cancel_build(build_id: int):
    """Signal a running build to stop."""
    with _cancel_events_lock:
        event = _cancel_events.get(build_id)
    if not event:
        raise HTTPException(status_code=404, detail="Build not running")
    event.set()
    return {"ok": True}


@router.post("/{build_id}/run")
def run_build(build_id: int, session: Session = Depends(get_session)):
    """Manually start a container from a successful build."""
    build = session.get(Build, build_id)
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    if build.status != "success":
        raise HTTPException(status_code=400, detail="Can only run successful builds")

    repo = session.get(Repository, build.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    build_root = git_service.get_build_path(build.id)
    if not build_root.exists():
        try:
            build_root = git_service.prepare_build_path(repo, build.id, build.commit_sha)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    try:
        build_dir = _validated_build_dir(build_root, repo.build_context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    has_compose = (
        (build_dir / "docker-compose.yml").exists()
        or (build_dir / "docker-compose.yaml").exists()
    )

    envs = session.exec(select(RepoEnv).where(RepoEnv.repo_id == repo.id)).all()
    env_vars = {e.key: e.value for e in envs}

    try:
        container_name = repo.name.lower().replace(" ", "-").replace("_", "-")
        if has_compose:
            docker_service.compose_up(build_dir, env_vars)
            return {"ok": True, "message": "Containers started via docker compose up"}
        else:
            cid = docker_service.run_image(build.image_name, container_name)
            return {"ok": True, "container_id": cid, "container_name": container_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
