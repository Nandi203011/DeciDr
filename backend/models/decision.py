# ============================================================
# models/decision.py — DeciDr
# Pydantic models — every input validated BEFORE touching logic
# Psychology frameworks used:
#   - Schwartz Values Theory (1992) — value weights
#   - CPT inputs (Kahneman & Tversky 1992) — option scoring
#   - Lerner et al. (2015) — emotional state impact
#   - Arkes & Blumer (1985) — sunk cost inputs
#   - Samuelson & Zeckhauser (1988) — status quo inputs
# ============================================================

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from enum import Enum
import re
import uuid


# ─── Enums (whitelisted values — prevents arbitrary string injection) ─────────

class DecisionCategory(str, Enum):
    CAREER       = "career"
    EDUCATION    = "education"
    FINANCIAL    = "financial"
    PURCHASE     = "purchase"
    RELATIONSHIP = "relationship"
    LIFESTYLE    = "lifestyle"
    OTHER        = "other"


class EmotionalState(str, Enum):
    """
    Specific emotions — not just positive/negative.
    Based on Lerner et al. (2015): each emotion has a specific
    directional effect on risk tolerance and decision quality.
    - Angry   → increases risk-taking (hot cognition)
    - Fearful → increases risk-aversion
    - Sad     → increases impatience (present bias)
    - Anxious → overestimates negative outcomes
    - Excited → overestimates positive outcomes
    """
    CALM     = "calm"
    ANXIOUS  = "anxious"
    ANGRY    = "angry"
    SAD      = "sad"
    EXCITED  = "excited"
    FEARFUL  = "fearful"
    NEUTRAL  = "neutral"


class RiskTolerance(str, Enum):
    """Feeds into CPT lambda (loss aversion) coefficient adjustment"""
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


# ─── Sub-models ──────────────────────────────────────────────────────────────

class DecisionOption(BaseModel):
    """
    A single option the user is considering.
    Rated across Schwartz's 7 core personal values (1992).
    """
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

    # Schwartz Values ratings for THIS specific option (1-10)
    financial_security: int = Field(ge=1, le=10)
    personal_growth:    int = Field(ge=1, le=10)
    relationships:      int = Field(ge=1, le=10)
    autonomy:           int = Field(ge=1, le=10)
    stability:          int = Field(ge=1, le=10)
    achievement:        int = Field(ge=1, le=10)
    wellbeing:          int = Field(ge=1, le=10)
    stress_level:       int = Field(ge=1, le=10)

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_html(cls, v: Optional[str]) -> Optional[str]:
        """Strip HTML/script tags — prevent XSS"""
        if v is None:
            return None
        return re.sub(r"<[^>]+>", "", str(v)).strip() or None


class ValuesWeights(BaseModel):
    """
    How much THIS user personally weights each Schwartz value.
    Reference: Schwartz, S.H. (1992) — validated across 60+ countries.
    All weights must sum to 100 — normalized personal priorities.
    """
    financial_security: int = Field(ge=0, le=100)
    personal_growth:    int = Field(ge=0, le=100)
    relationships:      int = Field(ge=0, le=100)
    autonomy:           int = Field(ge=0, le=100)
    stability:          int = Field(ge=0, le=100)
    achievement:        int = Field(ge=0, le=100)
    wellbeing:          int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def must_sum_to_100(self) -> "ValuesWeights":
        total = (
            self.financial_security + self.personal_growth +
            self.relationships + self.autonomy + self.stability +
            self.achievement + self.wellbeing
        )
        if total != 100:
            raise ValueError(
                f"Value weights must sum to exactly 100, got {total}. "
                f"Adjust your weights."
            )
        return self


# ─── Main Input Model ─────────────────────────────────────────────────────────

class DecisionInput(BaseModel):
    """
    Full structured input for one DeciDr analysis session.
    Every field validated before the psychology engine runs.
    """

    # Core question
    question: str = Field(min_length=10, max_length=300)
    category: DecisionCategory

    # Options (2 minimum, 5 maximum)
    options: list[DecisionOption] = Field(min_length=2, max_length=5)

    # Personal value priorities
    values_weights: ValuesWeights

    # Emotional context — Lerner et al. (2015)
    emotional_state:     EmotionalState
    emotional_intensity: int = Field(ge=1, le=10)

    # Risk profile — CPT lambda adjustment
    risk_tolerance: RiskTolerance

    # Sunk cost triggers — Arkes & Blumer (1985)
    time_already_invested_months: Optional[int] = Field(
        default=None, ge=0, le=600
    )
    money_already_invested: Optional[float] = Field(
        default=None, ge=0.0, le=10_000_000.0
    )

    # Status quo bias trigger — Samuelson & Zeckhauser (1988)
    current_situation_satisfaction: int = Field(ge=1, le=10)

    # CPT reference point framing
    is_reversible: bool
    time_pressure: bool

    @field_validator("question", mode="before")
    @classmethod
    def sanitize_question(cls, v: str) -> str:
        """Strip HTML and enforce minimum length after sanitization"""
        clean = re.sub(r"<[^>]+>", "", str(v)).strip()
        if len(clean) < 10:
            raise ValueError("Question too short — minimum 10 characters")
        return clean

    @model_validator(mode="after")
    def options_must_be_unique(self) -> "DecisionInput":
        """Prevent duplicate option names"""
        names = [o.name.lower().strip() for o in self.options]
        if len(names) != len(set(names)):
            raise ValueError("All options must have unique names")
        return self


# ─── Output Models ────────────────────────────────────────────────────────────

class BiasFound(BaseModel):
    """A single detected cognitive bias with full research citation"""
    name: str
    description: str
    severity: Literal["low", "medium", "high"]
    how_it_affects_this_decision: str
    source_paper: str  # Always cite the research


class OptionScore(BaseModel):
    """Full scored breakdown for a single option"""
    name: str
    raw_score: float            # Before any bias adjustment
    psychological_value: float  # CPT-adjusted value
    values_alignment: float     # Schwartz alignment score
    final_score: float          # Combined final score
    breakdown: dict             # Detailed per-value breakdown


class DecisionResult(BaseModel):
    """
    Full structured output returned to the frontend.
    Every field has a clear psychological basis.
    """
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    recommendation: str                  # Winning option name
    confidence: Literal["low", "medium", "high"]
    biases_detected: list[BiasFound]
    option_scores: list[OptionScore]
    premortem: str                       # "If this fails, likely reason..."
    second_order_effects: str            # "If you choose X, next you'll face..."
    narrative: str                       # Human-readable full explanation
    emotional_state_warning: Optional[str] = None
    research_citations: list[str]        # Papers that backed this analysis