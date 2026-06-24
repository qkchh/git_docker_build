from pathlib import Path
from typing import Generator

from python_on_whales import DockerClient, docker


def build_image(
    build_dir: Path,
    image_name: str,
    env_vars: dict[str, str] | None = None,
) -> Generator[str, None, None]:
    """Stream docker build output line by line.

    env_vars are injected two ways:
    - Written to build_dir/.env  (for COPY .env or docker-compose)
    - Passed as --build-arg      (for ARG instructions in Dockerfile)
    """
    if env_vars:
        env_file = build_dir / ".env"
        with open(env_file, "w") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")

    for line in docker.build(
        build_dir,
        tags=[image_name],
        build_args=env_vars or {},
        stream_logs=True,
    ):
        yield line


def compose_build(
    build_dir: Path,
    env_vars: dict[str, str] | None = None,
) -> Generator[str, None, None]:
    """Stream docker compose build output line by line."""
    if env_vars:
        with open(build_dir / ".env", "w") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")

    compose_file = (
        build_dir / "docker-compose.yml"
        if (build_dir / "docker-compose.yml").exists()
        else build_dir / "docker-compose.yaml"
    )
    client = DockerClient(compose_files=[str(compose_file)])
    for item in client.compose.build(stream_logs=True):
        # python-on-whales compose returns (stream_type, bytes) tuples
        if isinstance(item, tuple):
            content = item[1]
        else:
            content = item
        if isinstance(content, bytes):
            line = content.decode("utf-8", errors="replace").rstrip()
        else:
            line = str(content).rstrip()
        if line:
            yield line


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
