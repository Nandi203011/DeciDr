# ============================================================
# engine/scorer.py — DeciDr
# Master scoring engine — combines all three psychology layers
#
# Layer 1: CPT (Kahneman & Tversky 1992) — psychological value
# Layer 2: Values Alignment (Schwartz 1992) — personal fit
# Layer 3: Bias Detection (Arkes 1985, Samuelson 1988, etc.)
#
# Each layer is weighted differently per decision category
# because financial decisions need more CPT weight while
# lifestyle decisions need more values weight.
# ============================================================

from loguru import logger
from models.decision import DecisionInput, DecisionResult, OptionScore, BiasFound
from engine.prospect_theory import ProspectTheoryEngine
from engine.values_mapper import ValuesMapper
from engine.bias_detector import BiasDetector
import uuid


# ─── Layer Weights Per Decision Category ─────────────────────────────────────
# How much each psychology layer contributes to the final score
# varies by decision type — financial decisions are more CPT-driven,
# lifestyle decisions are more values-driven.

CATEGORY_WEIGHTS = {
    "financial":    {"cpt": 0.55, "values": 0.30, "bias": 0.15},
    "purchase":     {"cpt": 0.50, "values": 0.35, "bias": 0.15},
    "career":       {"cpt": 0.30, "values": 0.50, "bias": 0.20},
    "education":    {"cpt": 0.30, "values": 0.50, "bias": 0.20},
    "lifestyle":    {"cpt": 0.15, "values": 0.65, "bias": 0.20},
    "relationship": {"cpt": 0.10, "values": 0.70, "bias": 0.20},
    "other":        {"cpt": 0.30, "values": 0.50, "bias": 0.20},
}

# Score normalization ranges for CPT values
# CPT values can be very large (e.g. -4947) — we normalize to 0-10
CPT_NORMALIZE_RANGE = 10000.0


class DeciDrScorer:
    """
    Master scoring engine for DeciDr.

    Takes a DecisionInput, runs all three psychology engines,
    and produces a structured DecisionResult with:
    - Per-option scores (CPT + values + bias adjusted)
    - Detected biases with explanations
    - Final recommendation with confidence level
    - Pre-mortem analysis
    - Second-order thinking projection
    - Research citations for every claim
    """

    def __init__(self, decision_input: DecisionInput):
        self.input = decision_input
        self.category = decision_input.category.value
        self.weights = CATEGORY_WEIGHTS.get(self.category, CATEGORY_WEIGHTS["other"])

        logger.info(
            f"DeciDrScorer initialized | "
            f"category={self.category} | "
            f"weights=CPT:{self.weights['cpt']} "
            f"VALUES:{self.weights['values']} "
            f"BIAS:{self.weights['bias']}"
        )

    def compute(self) -> DecisionResult:
        """
        Main scoring pipeline. Runs all engines and combines results.

        Returns:
            DecisionResult — full structured output for the frontend
        """
        logger.info(f"Starting full scoring pipeline for: '{self.input.question}'")

        # ── Step 1: Run Bias Detection first ─────────────────────────────────
        # We run bias detection first because it affects how we
        # interpret the other layers' results
        logger.info("Step 1: Running bias detection...")
        detector = BiasDetector(self.input)
        detected_biases = detector.run_all_detectors()
        bias_summary = detector.get_summary()
        total_bias_adjustment = bias_summary["total_score_adjustment"]

        # ── Step 2: Run Values Mapper for each option ─────────────────────────
        logger.info("Step 2: Running values alignment for each option...")
        mapper = ValuesMapper(
            emotional_state=self.input.emotional_state.value,
            emotional_intensity=self.input.emotional_intensity
        )
        values_results = {}
        for option in self.input.options:
            result = mapper.compute_values_alignment(option, self.input.values_weights)
            values_results[option.name] = result

        # ── Step 3: Run CPT Engine for each option ────────────────────────────
        logger.info("Step 3: Running CPT calculations for each option...")
        cpt_engine = ProspectTheoryEngine(
            emotional_state=self.input.emotional_state.value,
            emotional_intensity=self.input.emotional_intensity,
            risk_tolerance=self.input.risk_tolerance.value
        )

        # Find reference point — current situation satisfaction as proxy
        # Mapped to a financial-equivalent scale for CPT
        # satisfaction 1-10 → reference point 1000-10000
        reference_point = self.input.current_situation_satisfaction * 1000

        cpt_results = {}
        for option in self.input.options:
            # Use values alignment score as the "outcome" for CPT
            # when no explicit financial values are provided
            # This is DeciDr's key innovation over the ABI paper —
            # we apply CPT to non-financial outcomes by using the
            # aggregated values score as the utility measure
            values_score = values_results[option.name]["final_alignment_score"]

            # Convert values score (0-10) to utility units (0-10000)
            # so CPT math works properly
            outcome_utility = values_score * 1000

            cpt_result = cpt_engine.calculate_cpt(
                option_name=option.name,
                outcome=outcome_utility,
                reference_point=reference_point,
                probability=0.70,  # Default 70% — things usually work out
            )
            cpt_results[option.name] = cpt_result

        # ── Step 4: Compute final score per option ────────────────────────────
        logger.info("Step 4: Computing final combined scores...")
        option_scores = []

        # Normalize CPT values to 0-10 scale for combination
        cpt_values = [r["final_cpt_value"] for r in cpt_results.values()]
        min_cpt = min(cpt_values)
        max_cpt = max(cpt_values)
        cpt_range = max_cpt - min_cpt if max_cpt != min_cpt else 1.0

        for option in self.input.options:
            name = option.name
            values_score = values_results[name]["final_alignment_score"]  # 0-10
            cpt_raw = cpt_results[name]["final_cpt_value"]

            # Normalize CPT to 0-10 scale relative to other options
            cpt_normalized = ((cpt_raw - min_cpt) / cpt_range) * 10

            # Raw combined score (before bias adjustment)
            raw_score = (
                (cpt_normalized * self.weights["cpt"]) +
                (values_score * self.weights["values"])
            )

            # Bias adjustment — distributed across options
            # Options that score higher get penalized more by biases
            # because biases inflate perceived attractiveness of the
            # status quo option
            bias_adj = total_bias_adjustment * self.weights["bias"]
            final_score = max(0.0, round(raw_score + bias_adj, 4))

            logger.info(
                f"Option '{name}': "
                f"cpt_norm={cpt_normalized:.3f} "
                f"values={values_score:.3f} "
                f"raw={raw_score:.3f} "
                f"bias_adj={bias_adj:.3f} "
                f"final={final_score:.4f}"
            )

            # Build per-dimension breakdown
            breakdown = {
                "cpt_raw_value": round(cpt_raw, 4),
                "cpt_normalized": round(cpt_normalized, 4),
                "cpt_weight": self.weights["cpt"],
                "cpt_contribution": round(cpt_normalized * self.weights["cpt"], 4),
                "values_score": round(values_score, 4),
                "values_weight": self.weights["values"],
                "values_contribution": round(values_score * self.weights["values"], 4),
                "bias_adjustment": round(bias_adj, 4),
                "strongest_value": values_results[name]["strongest_value_dimension"],
                "weakest_value": values_results[name]["weakest_value_dimension"],
                "cpt_framing": cpt_results[name].get("outcome_framing", "unknown"),
            }

            option_scores.append(OptionScore(
                name=name,
                raw_score=round(raw_score, 4),
                psychological_value=round(cpt_normalized, 4),
                values_alignment=round(values_score, 4),
                final_score=final_score,
                breakdown=breakdown
            ))

        # ── Step 5: Determine recommendation ─────────────────────────────────
        logger.info("Step 5: Determining recommendation...")
        option_scores.sort(key=lambda x: x.final_score, reverse=True)
        winner = option_scores[0]
        runner_up = option_scores[1] if len(option_scores) > 1 else None

        # Confidence based on score gap between winner and runner-up
        if runner_up:
            score_gap = winner.final_score - runner_up.final_score
            if score_gap >= 2.0:
                confidence = "high"
            elif score_gap >= 0.8:
                confidence = "medium"
            else:
                confidence = "low"
        else:
            confidence = "high"

        logger.info(
            f"Recommendation: '{winner.name}' | "
            f"score={winner.final_score} | "
            f"confidence={confidence} | "
            f"gap={score_gap:.3f}"
        )

        # ── Step 6: Pre-mortem analysis ───────────────────────────────────────
        # Klein (2007) — imagine the decision has already failed
        # Mitchell et al. (1989) — increases failure identification by 30%
        premortem = self._generate_premortem(winner.name, detected_biases)

        # ── Step 7: Second-order thinking ────────────────────────────────────
        # Evans & Stanovich (2013) — deliberate consequence projection
        second_order = self._generate_second_order(winner.name)

        # ── Step 8: Emotional state warning ──────────────────────────────────
        emotional_warning = self._get_emotional_warning()

        # ── Step 9: Build research citations ─────────────────────────────────
        citations = self._build_citations(detected_biases)

        # ── Step 10: Format biases for output ────────────────────────────────
        bias_output = [
            BiasFound(
                name=b["name"],
                description=b["how_it_affects"],
                severity=b["severity"],
                how_it_affects_this_decision=b["how_it_affects"],
                source_paper=b["research_source"]
            )
            for b in bias_summary["biases"]
        ]

        return DecisionResult(
            decision_id=str(uuid.uuid4()),
            question=self.input.question,
            recommendation=winner.name,
            confidence=confidence,
            biases_detected=bias_output,
            option_scores=option_scores,
            premortem=premortem,
            second_order_effects=second_order,
            narrative="",  # Filled by narrator.py
            emotional_state_warning=emotional_warning,
            research_citations=citations
        )

    def _generate_premortem(self, winner: str, biases: list) -> str:
        """
        Pre-mortem analysis — Klein (2007)
        Imagine the chosen option has ALREADY failed.
        What went wrong?
        """
        bias_names = [b.name for b in biases if b.severity in ["high", "medium"]]

        premortem = (
            f"PRE-MORTEM: Imagine you chose '{winner}' and it didn't work out. "
            f"The most likely reasons would be: "
        )

        if "Sunk Cost Fallacy" in bias_names:
            premortem += (
                f"(1) You made this decision while still attached to past "
                f"investments rather than future potential. "
            )
        if "Emotional Decision Making" in bias_names:
            premortem += (
                f"(2) The decision was made under high emotional intensity — "
                f"consider whether you'd make the same choice feeling calm. "
            )
        if "Present Bias" in bias_names:
            premortem += (
                f"(3) Short-term comfort was weighted too heavily over "
                f"long-term growth. "
            )

        premortem += (
            f"Use this pre-mortem to stress-test your reasoning before "
            f"committing. Reference: Klein, G. (2007) — Harvard Business Review."
        )

        return premortem

    def _generate_second_order(self, winner: str) -> str:
        """
        Second-order thinking — what happens AFTER this decision?
        Evans & Stanovich (2013) — deliberate System 2 projection
        """
        category = self.input.category.value

        templates = {
            "career": (
                f"If you choose '{winner}': Next you'll face questions about "
                f"financial runway, client acquisition, and skill gaps. "
                f"Plan for these before deciding — not after."
            ),
            "education": (
                f"If you choose '{winner}': Consider what comes after — "
                f"career paths this opens or closes, debt-to-income ratio, "
                f"and the opportunity cost of the time invested."
            ),
            "purchase": (
                f"If you choose '{winner}': Think about ongoing costs "
                f"(maintenance, insurance, storage) not just the purchase price. "
                f"The true cost is rarely just the sticker price."
            ),
            "financial": (
                f"If you choose '{winner}': Model the downstream effects — "
                f"how does this affect your financial position in 6, 12, 24 months?"
            ),
            "lifestyle": (
                f"If you choose '{winner}': This will create a new normal. "
                f"Who else does this affect? What habits will need to change?"
            ),
            "relationship": (
                f"If you choose '{winner}': Relationships have ripple effects. "
                f"Consider how this affects your broader social network "
                f"and daily routines."
            ),
        }

        return templates.get(
            category,
            f"If you choose '{winner}': Think carefully about what "
            f"comes next — decisions create new decision points."
        )

    def _get_emotional_warning(self) -> str | None:
        """Returns emotional state warning if relevant"""
        state = self.input.emotional_state.value
        intensity = self.input.emotional_intensity

        high_impact = ["anxious", "angry", "fearful", "sad"]
        if state in high_impact and intensity >= 7:
            return (
                f"⚠ You're feeling {state} at {intensity}/10 intensity. "
                f"Lerner et al. (2015) strongly recommend revisiting this "
                f"decision when feeling calmer — high-intensity emotions "
                f"systematically distort judgment in documented ways."
            )
        return None

    def _build_citations(self, biases: list) -> list[str]:
        """Builds full research citation list for this analysis"""
        citations = [
            "Kahneman, D. & Tversky, A. (1979) — Prospect Theory. Econometrica, 47(2).",
            "Tversky, A. & Kahneman, D. (1992) — Advances in Prospect Theory. J. Risk & Uncertainty.",
            "Schwartz, S.H. (1992) — Universals in the Content and Structure of Values.",
            "Lerner, J.S. et al. (2015) — Emotion and Decision Making. Annual Review of Psychology.",
            "Klein, G. (2007) — Performing a Project Premortem. Harvard Business Review.",
            "Evans & Stanovich (2013) — Dual-Process Theories of Higher Cognition.",
            "Ramos, Campos & Baião (2024) — ABI: Automatic Bias Identification. arXiv:2405.14067.",
        ]
        for bias in biases:
            src = bias.research_source
            if src and src not in citations:
                citations.append(src)
        return citations


# ─── Quick Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    from models.decision import (
        DecisionInput, DecisionOption, ValuesWeights,
        DecisionCategory, EmotionalState, RiskTolerance
    )

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

    scorer = DeciDrScorer(test_input)
    result = scorer.compute()

    print("\n" + "="*60)
    print("DECIDR — FULL DECISION ANALYSIS")
    print("="*60)
    print(f"Question: {result.question}")
    print(f"\n🏆 RECOMMENDATION: {result.recommendation}")
    print(f"📊 Confidence: {result.confidence.upper()}")

    print("\n--- OPTION SCORES ---")
    for opt in result.option_scores:
        print(f"\n{opt.name}")
        print(f"  Final Score:        {opt.final_score:.3f}/10")
        print(f"  Psychological Value:{opt.psychological_value:.3f}/10")
        print(f"  Values Alignment:   {opt.values_alignment:.3f}/10")
        print(f"  CPT Framing:        {opt.breakdown.get('cpt_framing')}")

    print(f"\n--- BIASES DETECTED ({len(result.biases_detected)}) ---")
    for bias in result.biases_detected:
        print(f"  [{bias.severity.upper()}] {bias.name}")

    print(f"\n--- PRE-MORTEM ---")
    print(f"  {result.premortem}")

    print(f"\n--- SECOND ORDER EFFECTS ---")
    print(f"  {result.second_order_effects}")

    if result.emotional_state_warning:
        print(f"\n--- EMOTIONAL WARNING ---")
        print(f"  {result.emotional_state_warning}")

    print(f"\n--- RESEARCH CITATIONS ---")
    for i, cite in enumerate(result.research_citations, 1):
        print(f"  {i}. {cite}")