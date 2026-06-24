import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from database import engine, get_session
from models import Build, Repository, RepoEnv
from services import docker_service, git_service

router = APIRouter(prefix="/api/builds", tags=["builds"])


class BuildCreate(BaseModel):
    repo_id: int
    commit_sha: str
    commit_message: Optional[str] = ""


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

    image_name = f"{repo.name.lower().replace(' ', '-')}:{data.commit_sha[:8]}"
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
        with Session(engine) as session:
            build = session.get(Build, build_id)
            if not build:
                yield _sse("[ERROR] Build not found")
                return

            repo = session.get(Repository, build.repo_id)
            if not repo:
                yield _sse("[ERROR] Repo not found")
                return

            logs: list[str] = []

            def persist(status: str):
                build.status = status
                build.log = "\n".join(logs)
                session.add(build)
                session.commit()

            try:
                build.status = "running"
                session.add(build)
                session.commit()

                # Step 1 — resolve workspace path (clone/fetch if remote)
                yield _sse(f"[INFO] Resolving repository...")
                repo_path = git_service.get_repo_path(repo)

                # Step 2 — checkout commit (remote only)
                #   Local  → build directly from the working directory as-is
                #   Remote → checkout the specific commit in the cloned workspace,
                #            then build from there (all committed files available)
                if repo.source_type == "remote":
                    yield _sse(f"[INFO] Checking out commit {build.commit_sha[:8]}...")
                    git_service.checkout_commit(repo_path, build.commit_sha)
                else:
                    yield _sse(f"[INFO] Building from local path: {repo_path}")

                build_dir = repo_path / repo.build_context if repo.build_context else repo_path

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
                    yield _sse(f"[INFO] Found docker-compose.yml → docker compose build")
                    for line in docker_service.compose_build(build_dir, env_vars):
                        logs.append(line)
                        yield _sse(line)
                else:
                    yield _sse(f"[INFO] Starting docker build → {build.image_name}")
                    for line in docker_service.build_image(build_dir, build.image_name, env_vars):
                        logs.append(line)
                        yield _sse(line)

                persist("success")
                yield _sse("[DONE] Build succeeded")

            except Exception as e:
                logs.append(str(e))
                persist("failed")
                yield _sse(f"[ERROR] {e}")

    return StreamingResponse(generate(), media_type="text/event-stream")
