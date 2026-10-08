"""
TrendPulse - FastAPI Application Entry Point
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("trendpulse.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TrendPulse API starting up...")
    from backend.database.connection import engine, Base, check_connection
    from backend.models import db_models  # noqa: F401 - registers models
    try:
        if check_connection():
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified/created.")
        else:
            logger.warning("PostgreSQL not reachable. Skipping table creation.")
    except Exception as e:
        logger.error(f"Startup DB error: {e}")
    yield
    logger.info("TrendPulse API shutting down.")


app = FastAPI(
    title="TrendPulse Analytics API",
    description="Real-Time YouTube Trending Intelligence & Video Lifecycle Analytics Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.routes import router
app.include_router(router)


@app.get("/", tags=["Health"])
def root():
    return {
        "name": "TrendPulse Analytics API",
        "version": "1.0.0",
        "description": "Real-Time YouTube Trending Intelligence Platform",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health():
    from backend.database.connection import check_connection
    db_ok = check_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=True,
        log_level="info",
    )
