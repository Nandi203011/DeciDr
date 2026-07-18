# ============================================================
# api/routes.py — DeciDr
# FastAPI route definitions — all API endpoints
# Security: rate limiting, input validation, error handling
# ============================================================

import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, Field

from models.decision import DecisionInput, DecisionResult
from engine.scorer import DeciDrScorer
from engine.narrator import DecisionNarrator
from engine.parser import DecisionParser
from engine.web_search import WebSearchEngine
from database import get_db, DecisionRecord, BiasRecord
from utils.helpers import format_timestamp, mask_sensitive_log

router  = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class ChatInput(BaseModel):
    text: str = Field(min_length=10, max_length=2000)


# ─── Health Check ─────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": "DeciDr",
        "version": "0.1.0",
        "timestamp": format_timestamp()
    }


# ─── Natural Language Chat Endpoint ──────────────────────────────────────────

@router.post("/chat")
@limiter.limit("10/minute")
async def chat_analyze(
    request: Request,
    chat_input: ChatInput,
    db: Session = Depends(get_db)
):
    logger.info(
        f"New chat request | length={len(chat_input.text)} | "
        f"preview={mask_sensitive_log(chat_input.text)}"
    )

    try:
        # Step 1 — Parse natural language
        logger.info("Step 1: Parsing natural language...")
        parser = DecisionParser()
        extracted = parser.parse(chat_input.text)

        # Step 2 — Convert to DecisionInput
        logger.info("Step 2: Converting to DecisionInput...")
        decision_input = DecisionInput(**extracted)

        # Step 2.5 — Web search for named entities
        decision_input, web_data = _apply_web_search(decision_input)

        # Step 3 — Run scoring engine
        logger.info("Step 3: Running scoring pipeline...")
        scorer = DeciDrScorer(decision_input)
        result = scorer.compute()

        # Step 4 — Generate narrative
        logger.info("Step 4: Generating narrative...")
        narrator = DecisionNarrator()
        narrative = narrator.generate(result, decision_input.question)
        result.narrative = narrative

        # Step 5 — Store metadata
        _store_decision(db, decision_input, result)

        logger.info(
            f"Chat complete | recommendation={result.recommendation} | "
            f"confidence={result.confidence} | web_search={web_data is not None}"
        )

        return {
            "result": result,
            "extracted_input": extracted,
            "web_data": web_data,
        }

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)[:100]}")
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.error(f"Chat error: {type(e).__name__}: {str(e)[:100]}")
        raise HTTPException(
            status_code=500,
            detail="Analysis failed. Please try again or use the guided form."
        )


# ─── Structured Form Endpoint ─────────────────────────────────────────────────

@router.post("/analyze")
@limiter.limit("10/minute")
async def analyze_decision(
    request: Request,
    decision_input: DecisionInput,
    db: Session = Depends(get_db)
):
    logger.info(
        f"New analyze request | category={decision_input.category} | "
        f"options={len(decision_input.options)} | "
        f"preview={mask_sensitive_log(decision_input.question)}"
    )

    try:
        # Auto-populate with web data if named entities detected
        decision_input, web_data = _apply_web_search(decision_input)

        scorer = DeciDrScorer(decision_input)
        result = scorer.compute()

        narrator = DecisionNarrator()
        narrative = narrator.generate(result, decision_input.question)
        result.narrative = narrative

        _store_decision(db, decision_input, result)

        logger.info(
            f"Analyze complete | recommendation={result.recommendation} | "
            f"web_search={web_data is not None}"
        )

        # Return result + web_data for frontend transparency
        return {
            "result": result,
            "web_data": web_data,
        }

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)[:100]}")
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.error(f"Analyze error: {type(e).__name__}: {str(e)[:100]}")
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")


# ─── History ──────────────────────────────────────────────────────────────────

@router.get("/history")
@limiter.limit("30/minute")
async def get_decision_history(
    request: Request,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    limit = max(1, min(limit, 50))
    try:
        records = (
            db.query(DecisionRecord)
            .order_by(DecisionRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return {
            "count": len(records),
            "decisions": [
                {
                    "id": r.id,
                    "category": r.category,
                    "recommendation": r.recommendation,
                    "confidence": r.confidence,
                    "biases_count": r.biases_count,
                    "emotional_state": r.emotional_state,
                    "created_at": r.created_at.isoformat(),
                }
                for r in records
            ]
        }
    except Exception as e:
        logger.error(f"History error: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Could not fetch history.")


# ─── Bias Stats ───────────────────────────────────────────────────────────────

@router.get("/stats/biases")
@limiter.limit("20/minute")
async def get_bias_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        records = db.query(BiasRecord).all()
        if not records:
            return {"message": "No data yet", "stats": {}}

        bias_counts = {}
        severity_counts = {"high": 0, "medium": 0, "low": 0}

        for r in records:
            bias_counts[r.bias_name] = bias_counts.get(r.bias_name, 0) + 1
            severity_counts[r.severity] = severity_counts.get(r.severity, 0) + 1

        sorted_biases = sorted(bias_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_biases_detected": len(records),
            "most_common_biases": [{"name": n, "count": c} for n, c in sorted_biases],
            "severity_breakdown": severity_counts,
        }
    except Exception as e:
        logger.error(f"Stats error: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Could not fetch stats.")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _apply_web_search(decision_input: DecisionInput) -> tuple:
    """
    Checks if decision involves named entities.
    If yes, fetches real web data and auto-populates option ratings.
    Returns (updated_decision_input, web_data or None)
    """
    try:
        web_engine = WebSearchEngine()
        option_names = [opt.name for opt in decision_input.options]

        if not web_engine.should_search(decision_input.question, option_names):
            return decision_input, None

        logger.info("Web search triggered — fetching real data...")
        web_data = web_engine.fetch_and_map(
            question=decision_input.question,
            option_names=option_names,
            category=decision_input.category.value
        )

        options_data = web_data.get("options", {})
        updated_options = []

        for opt in decision_input.options:
            if opt.name in options_data:
                real = options_data[opt.name]
                updated_opt = opt.model_copy(update={
                    "financial_security": real.get("financial_security", opt.financial_security),
                    "personal_growth":    real.get("personal_growth", opt.personal_growth),
                    "relationships":      real.get("relationships", opt.relationships),
                    "autonomy":           real.get("autonomy", opt.autonomy),
                    "stability":          real.get("stability", opt.stability),
                    "achievement":        real.get("achievement", opt.achievement),
                    "wellbeing":          real.get("wellbeing", opt.wellbeing),
                    "stress_level":       real.get("stress_level", opt.stress_level),
                })
                updated_options.append(updated_opt)
            else:
                updated_options.append(opt)

        return decision_input.model_copy(update={"options": updated_options}), web_data

    except Exception as e:
        logger.warning(f"Web search failed gracefully: {str(e)[:100]}")
        return decision_input, None


def _store_decision(db, inp: DecisionInput, result: DecisionResult):
    try:
        record = DecisionRecord(
            id=result.decision_id,
            question_preview=inp.question[:50],
            category=inp.category.value,
            recommendation=result.recommendation,
            confidence=result.confidence,
            final_score=result.option_scores[0].final_score if result.option_scores else 0.0,
            biases_count=len(result.biases_detected),
            bias_names=json.dumps([b.name for b in result.biases_detected]),
            emotional_state=inp.emotional_state.value,
            is_reversible=inp.is_reversible,
        )
        db.add(record)

        for bias in result.biases_detected:
            bias_record = BiasRecord(
                decision_id=result.decision_id,
                bias_name=bias.name,
                severity=bias.severity,
                confidence=0.75,
                category=inp.category.value,
            )
            db.add(bias_record)

        db.commit()
        logger.info(f"Decision {result.decision_id[:8]}... stored")

    except Exception as e:
        db.rollback()
        logger.error(f"Storage error: {type(e).__name__}: {str(e)[:100]}")