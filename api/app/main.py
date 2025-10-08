# api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .settings import settings
from .routers import flywheel

app = FastAPI(title="Imagulator API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(flywheel.router, prefix="/flywheel", tags=["flywheel"])

app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")
@app.get("/")
def root():
    return {"ok": True, "docs": "/docs"}

@app.get("/ping")
def ping():
    return {"status": "pong"}

# Debug: print routes on startup
@app.on_event("startup")
async def _print_routes():
    for r in app.router.routes:
        print("ROUTE:", r.path, getattr(r, "methods", None))

