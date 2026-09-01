import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.config import STATIC_DIR
from app.routers import auth, billing, chat, memory, skills, notes, settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schemas & migrations on startup
    init_db()
    yield

app = FastAPI(
    title="Stumpy AI — Adaptive Learning Companion SaaS",
    description="Public Freemium AI application designed to learn, adapt, and evolve with you.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(chat.router)
app.include_router(memory.router)
app.include_router(skills.router)
app.include_router(notes.router)
app.include_router(settings.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Stumpy AI SaaS", "version": "2.0.0"}

# Mount Static Files for Single Page Application
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Fallback to index.html for SPA routing
        return FileResponse(str(STATIC_DIR / "index.html"))
