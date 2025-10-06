from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .settings import settings
from .routers import flywheel, jobs
# ...

app = FastAPI(title="Imagulator API")

# Allow your Vite dev server to call the API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # UI dev origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1) Health check (simple GET)
@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "api"}

# 2) Example with path & query params
#    GET /echo/42?msg=hi  -> {"id":42,"msg":"hi"}
@app.get("/echo/{item_id}")
def echo(item_id: int, msg: str = "hello"):
    return {"id": item_id, "msg": msg}

# 3) Example POST with validation (Pydantic model)
from pydantic import BaseModel

class SumReq(BaseModel):
    a: float
    b: float

class SumResp(BaseModel):
    result: float

@app.post("/sum", response_model=SumResp)
def sum_numbers(body: SumReq):
    return {"result": body.a + body.b}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(flywheel.router, prefix="/flywheel", tags=["flywheel"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
