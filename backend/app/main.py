import os
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers import ingest, chat

app = FastAPI(title="MindMirror", version="0.1.0")

_cors_origins = [
    "http://localhost:3000",
]
_extra_origin = os.getenv("CORS_ORIGIN", "")
if _extra_origin:
    _cors_origins.append(_extra_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.on_event("startup")
def startup():
    init_db()
    # Pre-load embedding model
    print("Loading embedding model...")
    from app.embedding import get_model
    get_model()
    print("Embedding model loaded.")


@app.get("/api/health")
def health():
    return {"status": "ok"}
