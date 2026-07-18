# ============================================================
# database.py — DeciDr
# SQLite database setup via SQLAlchemy ORM
# Security: we NEVER write raw SQL — ORM only
# ============================================================

from sqlalchemy import (
    create_engine, Column, String, Float,
    Integer, Boolean, Text, DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from loguru import logger
from config import get_settings

settings = get_settings()

# ─── Engine Setup ─────────────────────────────────────────────────────────────
engine = create_engine(
    "sqlite:///./decidr.db",
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Models ───────────────────────────────────────────────────────────────────

class DecisionRecord(Base):
    """
    Stores each decision analysis result.
    We store metadata and scores — NOT raw personal content.
    Security: question text is stored but no PII.
    """
    __tablename__ = "decisions"

    id               = Column(String, primary_key=True, index=True)
    question_preview = Column(String(50))     # First 50 chars only — not full question
    category         = Column(String(50))
    recommendation   = Column(String(100))
    confidence       = Column(String(10))
    final_score      = Column(Float)
    biases_count     = Column(Integer)
    bias_names       = Column(Text)           # JSON string of bias names
    emotional_state  = Column(String(20))
    is_reversible    = Column(Boolean)
    created_at       = Column(DateTime, default=datetime.utcnow)


class BiasRecord(Base):
    """Stores individual bias detection records for analytics"""
    __tablename__ = "biases"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(String, index=True)
    bias_name   = Column(String(100))
    severity    = Column(String(10))
    confidence  = Column(Float)
    category    = Column(String(50))
    created_at  = Column(DateTime, default=datetime.utcnow)


# ─── Database Initialization ──────────────────────────────────────────────────

def init_db():
    """Creates all tables if they don't exist"""
    logger.info("Initializing DeciDr database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def get_db():
    """
    Dependency injection for FastAPI routes.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()