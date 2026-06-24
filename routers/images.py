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


@router.post("/containers/{container_id}/action")
def container_action(container_id: str, body: ContainerAction):
    try:
        docker_service.container_action(container_id, body.action)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
