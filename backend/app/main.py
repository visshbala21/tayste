import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.auth_routes import auth_router
from app.services.pipeline_queue import pipeline_queue
from app.config import get_settings

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title="Tayste - AI A&R Intelligence",
    description="AI-powered artist discovery and scouting platform",
    version="0.1.0",
)

_origins = [
    "http://localhost:3000",
    settings.frontend_url.rstrip("/"),
]
# Also allow the bare Vercel domain variant (with/without www)
for o in list(_origins):
    if "vercel.app" in o:
        _origins.append(o.replace("https://", "https://www."))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(router, prefix="/api")

@app.on_event("startup")
async def _start_pipeline_queue():
    await pipeline_queue.start()


@app.get("/health")
async def health():
    return {"status": "ok"}
