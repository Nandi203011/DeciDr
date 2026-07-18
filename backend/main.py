# ============================================================
# main.py — DeciDr
# FastAPI application entry point
# Run with: uvicorn main:app --reload
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
import sys

from config import get_settings
from database import init_db
from api.routes import router

# ─── Settings ─────────────────────────────────────────────────────────────────
settings = get_settings()

# ─── Logging Setup ────────────────────────────────────────────────────────────
# Remove default logger and configure safe logging
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    colorize=True,
)
logger.add(
    "logs/decidr.log",
    level="INFO",
    rotation="10 MB",    # New file when log hits 10MB
    retention="7 days",  # Keep logs for 7 days
    compression="zip",   # Compress old logs
)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="DeciDr API",
    description=(
        "Psychology-backed personal decision engine. "
        "Implements Cumulative Prospect Theory (Kahneman & Tversky, 1992), "
        "Schwartz Values Theory (1992), and automated bias detection "
        "based on Ramos, Campos & Baião (2024)."
    ),
    version="0.1.0",
    docs_url="/docs",      # Swagger UI — test your API here
    redoc_url="/redoc",    # ReDoc alternative docs
)

# ─── Rate Limiting ────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Only allow requests from your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],  # From .env — not wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST"],            # Only what we need
    allow_headers=["Content-Type", "Authorization"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api")

# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    """Runs when server starts — initializes database"""
    logger.info("DeciDr API starting up...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Allowed origin: {settings.allowed_origin}")
    init_db()
    logger.info("DeciDr API ready!")


@app.on_event("shutdown")
async def shutdown():
    logger.info("DeciDr API shutting down...")


# ─── Root ─────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "app": "DeciDr",
        "version": "0.1.0",
        "description": "Psychology-backed decision engine",
        "docs": "/docs",
        "health": "/api/health"
    }