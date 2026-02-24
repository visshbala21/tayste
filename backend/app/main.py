import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.services.pipeline_queue import pipeline_queue

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Tayste - AI A&R Intelligence",
    description="AI-powered artist discovery and scouting platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.on_event("startup")
async def _start_pipeline_queue():
    pipeline_queue.start()


@app.get("/health")
async def health():
    return {"status": "ok"}
