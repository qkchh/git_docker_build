from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import create_db
from routers import builds, images, repos

app = FastAPI(title="Git Docker Build")


@app.on_event("startup")
def on_startup():
    create_db()


app.include_router(repos.router)
app.include_router(builds.router)
app.include_router(images.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")
