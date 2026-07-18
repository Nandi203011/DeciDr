# ============================================================
# utils/helpers.py — DeciDr
# Shared utility functions used across the backend
# ============================================================

import uuid
import re
from datetime import datetime
from loguru import logger


def generate_decision_id() -> str:
    """Generates a unique decision ID"""
    return str(uuid.uuid4())


def sanitize_text(text: str, max_length: int = 500) -> str:
    """
    Strips HTML tags, trims whitespace, enforces max length.
    Used as a last-resort sanitization layer.
    Primary sanitization happens in Pydantic models.
    """
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text).strip()
    return clean[:max_length]


def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """
    Normalizes a value to 0-10 scale.
    Used to make CPT values comparable to values alignment scores.
    """
    if max_val == min_val:
        return 5.0  # Midpoint if no range
    normalized = ((value - min_val) / (max_val - min_val)) * 10
    return round(max(0.0, min(10.0, normalized)), 4)


def confidence_label(score_gap: float) -> str:
    """
    Returns confidence label based on gap between top two scores.
    Reference: ABI paper used similar confidence thresholds.
    """
    if score_gap >= 2.0:
        return "high"
    elif score_gap >= 0.8:
        return "medium"
    return "low"


def format_timestamp() -> str:
    """Returns current UTC timestamp as ISO string"""
    return datetime.utcnow().isoformat() + "Z"


def safe_divide(numerator: float, denominator: float, fallback: float = 0.0) -> float:
    """Safe division — returns fallback if denominator is zero"""
    if denominator == 0:
        logger.warning(f"Division by zero prevented: {numerator}/{denominator}")
        return fallback
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamps a value between min and max"""
    return max(min_val, min(max_val, value))


def mask_sensitive_log(text: str) -> str:
    """
    Masks potentially sensitive decision content for logging.
    We log metadata only — never personal decision content.
    Security principle: no PII in logs.
    """
    if len(text) <= 10:
        return "***"
    return text[:5] + "***" + text[-3:]