# ============================================================
# engine/prospect_theory.py — DeciDr
# Implements Cumulative Prospect Theory (CPT)
#
# Primary references:
#   - Kahneman, D. & Tversky, A. (1979) — Prospect Theory:
#     An Analysis of Decision Under Risk. Econometrica, 47(2).
#   - Tversky, A. & Kahneman, D. (1992) — Advances in Prospect
#     Theory: Cumulative Representation of Uncertainty.
#     Journal of Risk and Uncertainty, 5(4), 297-323.
#   - Ruggeri et al. (2020) — Replicating patterns of prospect
#     theory. Nature Human Behaviour, 4, 622-633.
#
# Key empirically-derived parameters (Tversky & Kahneman 1992):
#   alpha  = 0.88  — diminishing sensitivity to gains
#   beta   = 0.88  — diminishing sensitivity to losses
#   lambda = 2.25  — loss aversion coefficient
#   gamma  = 0.61  — probability weighting curvature
# ============================================================

from loguru import logger

ALPHA  = 0.88
BETA   = 0.88
LAMBDA = 2.25
GAMMA  = 0.61

EMOTION_LAMBDA_ADJUSTMENTS = {
    "calm":    0.00,
    "neutral": 0.00,
    "anxious": 0.50,
    "fearful": 0.75,
    "sad":     0.25,
    "angry":  -0.50,
    "excited":-0.25,
}

RISK_GAMMA_ADJUSTMENTS = {
    "low":    -0.08,
    "medium":  0.00,
    "high":    0.08,
}


class ProspectTheoryEngine:
    def __init__(self, emotional_state="neutral", emotional_intensity=5, risk_tolerance="medium"):
        self.emotional_state = emotional_state.lower()
        self.emotional_intensity = emotional_intensity
        self.risk_tolerance = risk_tolerance.lower()

        intensity_scalar = emotional_intensity / 10.0
        base_lambda_adj = EMOTION_LAMBDA_ADJUSTMENTS.get(self.emotional_state, 0.0)
        self.lambda_effective = max(1.0, LAMBDA + (base_lambda_adj * intensity_scalar))

        gamma_adj = RISK_GAMMA_ADJUSTMENTS.get(self.risk_tolerance, 0.0)
        self.gamma_effective = max(0.3, min(1.0, GAMMA + gamma_adj))

        logger.info(
            f"ProspectTheoryEngine initialized | emotion={emotional_state} "
            f"intensity={emotional_intensity} | "
            f"lambda={self.lambda_effective:.3f} gamma={self.gamma_effective:.3f}"
        )

    def value_function(self, delta: float) -> float:
        if delta >= 0:
            pv = delta ** ALPHA
            logger.debug(f"Gain: {delta}^{ALPHA} = {pv:.4f}")
        else:
            pv = -self.lambda_effective * ((-delta) ** BETA)
            logger.debug(f"Loss: -{self.lambda_effective:.2f} * {(-delta):.4f}^{BETA} = {pv:.4f}")
        return pv

    def probability_weighting(self, p: float) -> float:
        p = max(0.001, min(0.999, p))
        g = self.gamma_effective
        numerator = p ** g
        denominator = (p ** g + (1 - p) ** g) ** (1 / g)
        weighted = numerator / denominator
        logger.debug(f"Probability weighting: p={p}, gamma={g:.4f}, w(p)={weighted:.4f}")
        return weighted

    def calculate_cpt(self, option_name, outcome, reference_point, probability=0.70):
        delta = outcome - reference_point
        framing = "GAIN" if delta >= 0 else "LOSS"

        logger.info(
            f"CPT for '{option_name}': outcome={outcome}, "
            f"ref={reference_point}, delta={delta:.4f}, framed_as={framing}"
        )

        psych_value = self.value_function(delta)
        weighted_prob = self.probability_weighting(probability)
        final_cpt = psych_value * weighted_prob

        if framing == "GAIN":
            framing_text = (
                f"'{option_name}' is psychologically framed as a GAIN "
                f"(delta=+{delta:.2f} from your current situation)."
            )
        else:
            framing_text = (
                f"'{option_name}' is psychologically framed as a LOSS "
                f"(delta={delta:.2f} from your current situation). "
                f"Loss aversion (lambda={self.lambda_effective:.2f}) amplifies "
                f"the psychological impact by {self.lambda_effective:.1f}x."
            )

        prob_text = (
            f"The {probability*100:.0f}% probability is perceived as "
            f"{weighted_prob*100:.1f}% by your brain's probability weighting."
        )

        explanation = (
            f"{framing_text} {prob_text} "
            f"Final psychological value: {psych_value:.3f} x "
            f"{weighted_prob:.3f} = {final_cpt:.3f}"
        )

        logger.info(
            f"CPT result for '{option_name}': "
            f"psych_value={psych_value:.4f} "
            f"weighted_prob={weighted_prob:.4f} "
            f"final={final_cpt:.4f}"
        )

        return {
            "option_name": option_name,
            "outcome": outcome,
            "reference_point": reference_point,
            "delta": round(delta, 4),
            "outcome_framing": framing,
            "psychological_value": round(psych_value, 4),
            "objective_probability": probability,
            "weighted_probability": round(weighted_prob, 4),
            "final_cpt_value": round(final_cpt, 4),
            "lambda_used": round(self.lambda_effective, 4),
            "gamma_used": round(self.gamma_effective, 4),
            "explanation": explanation,
            "research_basis": [
                "Kahneman & Tversky (1979) — Prospect Theory. Econometrica.",
                "Tversky & Kahneman (1992) — Advances in Prospect Theory.",
                "Lerner et al. (2015) — Emotion and Decision Making.",
                "Ruggeri et al. (2020) — Replicating patterns of prospect theory.",
            ]
        }


if __name__ == "__main__":
    engine = ProspectTheoryEngine(
        emotional_state="anxious",
        emotional_intensity=7,
        risk_tolerance="low"
    )
    result = engine.calculate_cpt(
        option_name="Quit and freelance",
        outcome=45000,
        reference_point=50000,
        probability=0.70
    )
    print(f"\nOption: {result['option_name']}")
    print(f"Framed as: {result['outcome_framing']}")
    print(f"Psychological value: {result['psychological_value']:.3f}")
    print(f"Weighted probability: {result['weighted_probability']:.3f}")
    print(f"Final CPT value: {result['final_cpt_value']:.3f}")
    print(f"Explanation: {result['explanation']}")