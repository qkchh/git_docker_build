from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import docker_service

router = APIRouter(prefix="/api", tags=["docker"])


@router.get("/images")
def list_images():
    try:
        return docker_service.get_images()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/images/{image_id}")
def delete_image(image_id: str):
    try:
        docker_service.remove_image(image_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/containers")
def list_containers():
    try:
        return docker_service.get_containers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ContainerAction(BaseModel):
    action: str  # start | stop | restart | remove


@router.post("/images/{image_id}/run")
def run_image(image_id: str):
    try:
        images = docker_service.get_images()
        image = next((img for img in images if img["id"] == image_id), None)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        tag = next((t for t in image["tags"] if "<none>" not in t), image_id)
        cid = docker_service.run_image_by_tag(tag)
        return {"ok": True, "container_id": cid}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/containers/{container_id}/logs")
def container_logs(container_id: str, lines: int = 200):
    try:
        lines = max(1, min(lines, 5000))
        logs = docker_service.get_container_logs(container_id, lines)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/containers/{container_id}/action")
def container_action(container_id: str, body: ContainerAction):
    try:
        docker_service.container_action(container_id, body.action)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
