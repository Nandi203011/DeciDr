# ============================================================
# engine/narrator.py — DeciDr
# Generates human-readable narrative explanation using Groq API
#
# The narrator is the LAST step in the pipeline — it takes
# the structured output from scorer.py and turns it into
# a warm, clear, psychologically-grounded explanation.
#
# Key design principle: The LLM does NOT make the decision.
# The math/psychology engines make the decision.
# The LLM only EXPLAINS the decision in plain English.
#
# Model: Llama 3 via Groq API (free tier)
# Reference: Ramos et al. (2024) — ABI paper noted that
# explaining bias to decision-makers significantly improves
# awareness (85.2% agreed explanation helped them)
# ============================================================

from groq import Groq
from loguru import logger
from config import get_settings
from models.decision import DecisionResult


# ─── System Prompt ────────────────────────────────────────────────────────────
# This is the "personality" of DeciDr's narrator
# Carefully engineered to be warm, honest, and research-grounded

SYSTEM_PROMPT = """You are DeciDr's decision analyst — a warm, honest, and 
psychologically-informed advisor who explains decision analysis results to people.

Your role is ONLY to explain the analysis that has already been computed by 
DeciDr's psychology engines. You do NOT re-analyze or override the scores.

Your explanation style:
- Warm and human — like a trusted mentor, not a robot
- Honest — acknowledge uncertainty and limitations
- Grounded — reference the psychological research when relevant
- Concise — 3-4 paragraphs maximum
- Actionable — end with one clear next step

IMPORTANT RULES:
- Never say "As an AI" or "I am a language model"
- Never use bullet points — write in flowing paragraphs
- Never override the recommendation from the scores
- Always acknowledge the emotional state if it's high intensity
- Always mention at least one detected bias by name if any were found
- Keep response under 250 words
- End with one concrete, specific next step the person can take TODAY
"""


class DecisionNarrator:
    """
    Generates a human-readable narrative for a DeciDr analysis result.

    Takes the structured DecisionResult (scores, biases, recommendation)
    and produces a warm, clear explanation that a person can actually
    understand and act on.

    Uses Groq's free API with Llama 3 — completely free, fast,
    and runs in the cloud (no local hardware needed).
    """

    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile" # Free Groq model — Llama 3 8B
        logger.info(f"DecisionNarrator initialized | model={self.model}")

    def generate(self, result: DecisionResult, question: str) -> str:
        """
        Generates narrative explanation for a decision result.

        Args:
            result: Full DecisionResult from scorer.py
            question: Original decision question from user

        Returns:
            Human-readable narrative string
        """
        logger.info(f"Generating narrative for: '{question}'")

        # Build a structured summary to send to the LLM
        # We send ONLY the key facts — not raw numbers
        # This keeps the prompt focused and the response relevant

        bias_names = [b.name for b in result.biases_detected]
        high_biases = [b for b in result.biases_detected if b.severity == "high"]
        medium_biases = [b for b in result.biases_detected if b.severity == "medium"]

        # Build option scores summary
        scores_text = "\n".join([
            f"- {opt.name}: {opt.final_score:.2f}/10 "
            f"(values alignment: {opt.values_alignment:.2f}/10)"
            for opt in result.option_scores
        ])

        # Build bias summary
        bias_text = "\n".join([
            f"- {b.name} [{b.severity}]: {b.how_it_affects_this_decision[:100]}..."
            for b in result.biases_detected
        ]) if result.biases_detected else "No significant biases detected."

        # Build the user prompt with all relevant facts
        user_prompt = f"""
Please explain this DeciDr decision analysis to the person in a warm, 
clear, and helpful way.

DECISION QUESTION: {question}

RECOMMENDATION: {result.recommendation}
CONFIDENCE: {result.confidence}

OPTION SCORES:
{scores_text}

BIASES DETECTED:
{bias_text}

PRE-MORTEM (if this fails, why):
{result.premortem}

SECOND ORDER EFFECTS:
{result.second_order_effects}

EMOTIONAL WARNING:
{result.emotional_state_warning or "No significant emotional distortion detected."}

Write a warm, honest 3-4 paragraph explanation of what this analysis 
means for this person. Acknowledge their situation with empathy. 
Explain the key bias(es) affecting their thinking. Validate the 
recommendation with the psychological reasoning. End with one 
specific next step they can take TODAY.
"""

        try:
            logger.info("Calling Groq API for narrative generation...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=400,       # Keep response concise
                temperature=0.7,      # Balanced creativity vs consistency
                top_p=0.9,
            )

            narrative = response.choices[0].message.content.strip()

            logger.info(
                f"Narrative generated successfully | "
                f"length={len(narrative)} chars"
            )

            return narrative

        except Exception as e:
            # Security: never expose raw API errors to frontend
            # Log the real error server-side, return safe fallback
            logger.error(f"Groq API error: {type(e).__name__}: {str(e)[:100]}")
            return self._fallback_narrative(result, question)

    def _fallback_narrative(self, result: DecisionResult, question: str) -> str:
        """
        Fallback narrative if Groq API is unavailable.
        Generated purely from the structured data — no LLM needed.
        This ensures DeciDr works even without internet connection.
        """
        logger.info("Using fallback narrative (no LLM)")

        bias_mentions = ""
        if result.biases_detected:
            top_bias = result.biases_detected[0]
            bias_mentions = (
                f"One key pattern we noticed: {top_bias.name} may be "
                f"influencing your thinking here. {top_bias.how_it_affects_this_decision} "
            )

        emotional_mention = ""
        if result.emotional_state_warning:
            emotional_mention = f"{result.emotional_state_warning} "

        top_option = result.option_scores[0]
        bottom_option = result.option_scores[-1]
        score_gap = top_option.final_score - bottom_option.final_score

        confidence_text = {
            "high": "The analysis is quite clear",
            "medium": "The analysis leans toward",
            "low": "The analysis slightly favors"
        }.get(result.confidence, "The analysis suggests")

        return (
            f"Based on DeciDr's psychology-backed analysis of your question "
            f"'{question}', the recommendation is '{result.recommendation}'. "
            f"{confidence_text} this direction, with a score gap of "
            f"{score_gap:.1f} points between your options. "
            f"\n\n"
            f"{bias_mentions}"
            f"{emotional_mention}"
            f"\n\n"
            f"{result.premortem} "
            f"\n\n"
            f"{result.second_order_effects} "
            f"Take time to reflect on this analysis before making your final decision."
        )


# ─── Quick Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    from models.decision import (
        DecisionInput, DecisionOption, ValuesWeights,
        DecisionCategory, EmotionalState, RiskTolerance
    )
    from engine.scorer import DeciDrScorer

    # Run full pipeline including narrator
    test_input = DecisionInput(
        question="Should I quit my job and start freelancing?",
        category=DecisionCategory.CAREER,
        options=[
            DecisionOption(
                name="Stay at job",
                financial_security=8, personal_growth=3,
                relationships=5, autonomy=3, stability=9,
                achievement=3, wellbeing=4, stress_level=4
            ),
            DecisionOption(
                name="Quit and freelance",
                financial_security=4, personal_growth=9,
                relationships=6, autonomy=10, stability=3,
                achievement=8, wellbeing=7, stress_level=6
            ),
        ],
        values_weights=ValuesWeights(
            financial_security=5, personal_growth=30,
            relationships=10, autonomy=30, stability=5,
            achievement=15, wellbeing=5
        ),
        emotional_state=EmotionalState.ANXIOUS,
        emotional_intensity=8,
        risk_tolerance=RiskTolerance.LOW,
        time_already_invested_months=48,
        money_already_invested=0,
        current_situation_satisfaction=3,
        is_reversible=True,
        time_pressure=False,
    )

    # Step 1 — Get scores
    scorer = DeciDrScorer(test_input)
    result = scorer.compute()

    # Step 2 — Generate narrative
    narrator = DecisionNarrator()
    narrative = narrator.generate(result, test_input.question)

    # Step 3 — Attach narrative to result
    result.narrative = narrative

    print("\n" + "="*60)
    print("DECIDR — COMPLETE ANALYSIS WITH NARRATIVE")
    print("="*60)
    print(f"\n🏆 RECOMMENDATION: {result.recommendation}")
    print(f"📊 Confidence: {result.confidence.upper()}")
    print(f"\n--- NARRATIVE ---\n")
    print(narrative)
    print(f"\n--- CITATIONS ---")
    for i, cite in enumerate(result.research_citations[:5], 1):
        print(f"  {i}. {cite}")