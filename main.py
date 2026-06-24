import os
import secrets
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from database import create_db
from routers import builds, images, repos

app = FastAPI(title="Git Docker Build")

ACCESS_TOKEN: str = ""


def _load_or_create_token() -> str:
    if env_token := os.getenv("ACCESS_TOKEN"):
        return env_token
    token_file = Path("data/access_token.txt")
    token_file.parent.mkdir(parents=True, exist_ok=True)
    if token_file.exists():
        return token_file.read_text().strip()
    token = secrets.token_hex(16)
    token_file.write_text(token)
    return token


@app.on_event("startup")
def on_startup():
    global ACCESS_TOKEN
    create_db()
    ACCESS_TOKEN = _load_or_create_token()
    print("\n" + "=" * 52, flush=True)
    print(f"  Access Token: {ACCESS_TOKEN}", flush=True)
    print("=" * 52 + "\n", flush=True)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path == "/" or path.startswith("/static/") or path == "/api/auth/verify":
        return await call_next(request)
    token = request.headers.get("X-Access-Token") or request.query_params.get("token")
    if token != ACCESS_TOKEN:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


# ── Auth ──────────────────────────────────────────────
auth_router = APIRouter(prefix="/api/auth")


@auth_router.post("/verify")
async def verify_token(request: Request):
    data = await request.json()
    if data.get("token") == ACCESS_TOKEN:
        return {"ok": True}
    return JSONResponse(status_code=401, content={"detail": "Invalid token"})


app.include_router(auth_router)
app.include_router(repos.router)
app.include_router(builds.router)
app.include_router(images.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")
