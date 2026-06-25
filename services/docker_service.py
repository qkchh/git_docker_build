import subprocess
import threading
from pathlib import Path
from typing import Generator

from python_on_whales import DockerClient, docker


class BuildCancelled(Exception):
    """Raised when a build is cancelled by the user."""


def _kill_on_cancel(cancel_event: threading.Event, proc: subprocess.Popen) -> None:
    """Background daemon thread: terminates proc as soon as cancel_event is set."""
    cancel_event.wait()
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def build_image(
    build_dir: Path,
    image_name: str,
    env_vars: dict[str, str] | None = None,
    cancel_event: threading.Event | None = None,
) -> Generator[str, None, None]:
    """Stream docker build output line by line.

    env_vars are injected two ways:
    - Written to build_dir/.env  (for COPY .env or docker-compose)
    - Passed as --build-arg      (for ARG instructions in Dockerfile)
    """
    if env_vars:
        with open(build_dir / ".env", "w") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")

    cmd = ["docker", "build", "--progress=plain", "-t", image_name]
    for k, v in (env_vars or {}).items():
        cmd += ["--build-arg", f"{k}={v}"]
    cmd.append(str(build_dir.resolve()))

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if cancel_event:
        threading.Thread(target=_kill_on_cancel, args=(cancel_event, proc), daemon=True).start()

    try:
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                yield line
        proc.wait()
        if cancel_event and cancel_event.is_set():
            raise BuildCancelled()
        if proc.returncode != 0:
            raise RuntimeError(f"docker build exited with code {proc.returncode}")
    except BuildCancelled:
        raise
    except Exception:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        raise


def compose_build(
    build_dir: Path,
    env_vars: dict[str, str] | None = None,
    cancel_event: threading.Event | None = None,
) -> Generator[str, None, None]:
    """Stream docker compose build output line by line."""
    if env_vars:
        with open(build_dir / ".env", "w") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")

    # --progress is a global docker compose flag; cwd lets compose find the file automatically
    cmd = ["docker", "compose", "--progress", "plain", "build"]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=str(build_dir.resolve()),
    )

    if cancel_event:
        threading.Thread(target=_kill_on_cancel, args=(cancel_event, proc), daemon=True).start()

    try:
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                yield line
        proc.wait()
        if cancel_event and cancel_event.is_set():
            raise BuildCancelled()
        if proc.returncode != 0:
            raise RuntimeError(f"docker compose build exited with code {proc.returncode}")
    except BuildCancelled:
        raise
    except Exception:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        raise


def run_image(image_name: str, container_name: str) -> str:
    """Remove any existing container with the same name, then start a new one."""
    try:
        existing = docker.container.inspect(container_name)
        docker.container.remove(existing, force=True)
    except Exception:
        pass
    # Use create+start to avoid python-on-whales streaming bugs with detach=True
    container = docker.container.create(
        image_name,
        name=container_name,
        publish_all=True,
        restart="unless-stopped",
    )
    docker.container.start(container)
    return container.id[:12]


def compose_up(build_dir: Path, env_vars: dict | None = None) -> None:
    """docker compose up -d"""
    compose_file = (
        build_dir / "docker-compose.yml"
        if (build_dir / "docker-compose.yml").exists()
        else build_dir / "docker-compose.yaml"
    )
    if env_vars:
        with open(build_dir / ".env", "w") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")
    client = DockerClient(compose_files=[str(compose_file)])
    client.compose.up(detach=True, stream_logs=False)


def run_image_by_tag(image_tag: str) -> str:
    """Run an image by tag; derive container name from the tag."""
    container_name = image_tag.split(":")[0].split("/")[-1].replace("_", "-")
    return run_image(image_tag, container_name)


def get_container_logs(container_id: str, lines: int = 200) -> str:
    c = docker.container.inspect(container_id)
    raw = docker.container.logs(c, tail=lines)
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return str(raw)


def get_images() -> list[dict]:
    images = []
    for img in docker.image.list():
        images.append(
            {
                "id": img.id[:12],
                "tags": img.repo_tags or ["<none>"],
                "size_mb": round(img.size / 1024 / 1024, 1),
                "created": img.created.isoformat() if img.created else None,
            }
        )
    return sorted(images, key=lambda x: x["created"] or "", reverse=True)


def remove_image(image_id: str) -> None:
    docker.image.remove(image_id, force=True)


def get_containers() -> list[dict]:
    containers = []
    for c in docker.container.list(all=True):
        containers.append(
            {
                "id": c.id[:12],
                "name": c.name,
                "image": c.image,
                "status": c.state.status,
                "created": c.created.isoformat() if c.created else None,
            }
        )
    return containers


def container_action(container_id: str, action: str) -> None:
    """start | stop | restart | remove"""
    c = docker.container.inspect(container_id)
    if action == "start":
        docker.container.start(c)
    elif action == "stop":
        docker.container.stop(c)
    elif action == "restart":
        docker.container.restart(c)
    elif action == "remove":
        docker.container.remove(c, force=True)
    else:
        raise ValueError(f"Unknown action: {action}")
