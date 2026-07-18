# ============================================================
# engine/values_mapper.py — DeciDr
# Implements Schwartz's Theory of Basic Human Values (1992)
# Reference: Schwartz, S.H. (1992) — "Universals in the Content
# and Structure of Values" — Advances in Experimental Social
# Psychology, 25, 1-65. Validated across 60+ countries.
#
# Purpose: Re-weights decision options based on what THIS
# specific person actually cares about — not generic metrics.
# This is what makes DeciDr personal and human.
# ============================================================

from loguru import logger
from models.decision import DecisionOption, ValuesWeights


# ─── Emotional Impact Modifiers ───────────────────────────────────────────────
# Based on Lerner et al. (2015) — specific emotions distort
# how people perceive value alignment, not just risk.
# These modifiers adjust how strongly values are weighted
# when a person is in a particular emotional state.

EMOTION_VALUE_MODIFIERS = {
    # Calm/neutral — full values clarity, no distortion
    "calm":    {"growth_boost": 0.0, "security_boost": 0.0, "distortion": "none"},
    "neutral": {"growth_boost": 0.0, "security_boost": 0.0, "distortion": "none"},

    # Anxious — overweights security, underweights growth
    # Lerner et al. (2015): anxiety triggers risk-aversion and security-seeking
    "anxious": {"growth_boost": -0.15, "security_boost": 0.20, "distortion": "security_bias"},

    # Fearful — similar to anxious but stronger security pull
    "fearful": {"growth_boost": -0.20, "security_boost": 0.25, "distortion": "security_bias"},

    # Angry — underweights long-term values, overweights autonomy
    # Lerner et al. (2015): anger increases risk-taking and independence-seeking
    "angry":   {"growth_boost": 0.0, "security_boost": -0.15, "distortion": "autonomy_bias"},

    # Sad — underweights future-oriented values (growth, achievement)
    # Lerner et al. (2015): sadness increases present bias and impatience
    "sad":     {"growth_boost": -0.20, "security_boost": 0.10, "distortion": "present_bias"},

    # Excited — overweights growth and achievement, underweights security
    # Creates overconfidence in positive outcomes
    "excited": {"growth_boost": 0.20, "security_boost": -0.15, "distortion": "optimism_bias"},
}


class ValuesMapper:
    """
    Maps a DecisionOption against a user's personal value weights
    using Schwartz's Theory of Basic Human Values (1992).

    The key insight: a 'good' option isn't universally good —
    it's good relative to what THIS person values most.

    A ₹5000 pay cut means nothing to someone who values
    autonomy at 40/100 and financial security at 5/100.
    But it means everything to someone with the opposite weights.
    """

    def __init__(
        self,
        emotional_state: str = "neutral",
        emotional_intensity: int = 5
    ):
        """
        Args:
            emotional_state: Current emotion — affects value perception
            emotional_intensity: 1-10 — how strongly the emotion is felt
        """
        self.emotional_state = emotional_state.lower()
        self.emotional_intensity = emotional_intensity

        # Intensity scalar — maps 1-10 intensity to 0.1-1.0 effect multiplier
        # At intensity=5 (moderate), emotion affects values by 50% of max modifier
        self.intensity_scalar = emotional_intensity / 10.0

        logger.info(
            f"ValuesMapper initialized | emotion={emotional_state} "
            f"intensity={emotional_intensity} | scalar={self.intensity_scalar}"
        )

    def compute_values_alignment(
        self,
        option: DecisionOption,
        weights: ValuesWeights
    ) -> dict:
        """
        Computes how well an option aligns with the user's personal values.
        Returns a detailed breakdown of alignment per value dimension.

        Formula per dimension:
            raw_alignment = option_score × (weight / 100)
            This gives a weighted contribution of each value dimension.

        Total alignment = sum of all weighted contributions
        Normalized to 0-10 scale for readability.

        Args:
            option: The decision option being evaluated
            weights: User's personal value priority weights (sum to 100)

        Returns:
            dict with per-dimension scores and total alignment score
        """
        logger.info(f"Computing values alignment for option: '{option.name}'")

        # Step 1 — Get emotion modifiers for this emotional state
        emotion_mod = EMOTION_VALUE_MODIFIERS.get(
            self.emotional_state,
            EMOTION_VALUE_MODIFIERS["neutral"]
        )
        distortion_type = emotion_mod["distortion"]

        logger.debug(
            f"Emotion modifiers applied | state={self.emotional_state} "
            f"distortion={distortion_type}"
        )

        # Step 2 — Calculate raw weighted score per Schwartz value dimension
        # Each dimension: option's score on that value × user's weight for it
        # Divided by 100 to normalize weights (they sum to 100)

        dimensions = {}

        # --- Financial Security ---
        # Emotion adjustment: anxiety/fear boost security weight
        security_adj = emotion_mod["security_boost"] * self.intensity_scalar
        effective_security_weight = max(0, weights.financial_security + (security_adj * 100))
        dimensions["financial_security"] = {
            "option_score": option.financial_security,
            "user_weight": weights.financial_security,
            "effective_weight": round(effective_security_weight, 2),
            "emotion_adjustment": round(security_adj * 100, 2),
            "weighted_score": round(
                option.financial_security * (effective_security_weight / 100), 4
            ),
            "schwartz_category": "Security",  # Schwartz (1992) value category
        }

        # --- Personal Growth ---
        # Emotion adjustment: anxiety/sadness reduce growth weight,
        # excitement boosts it
        growth_adj = emotion_mod["growth_boost"] * self.intensity_scalar
        effective_growth_weight = max(0, weights.personal_growth + (growth_adj * 100))
        dimensions["personal_growth"] = {
            "option_score": option.personal_growth,
            "user_weight": weights.personal_growth,
            "effective_weight": round(effective_growth_weight, 2),
            "emotion_adjustment": round(growth_adj * 100, 2),
            "weighted_score": round(
                option.personal_growth * (effective_growth_weight / 100), 4
            ),
            "schwartz_category": "Self-Direction / Stimulation",
        }

        # --- Relationships ---
        # No direct emotion modifier — relationships value is relatively stable
        dimensions["relationships"] = {
            "option_score": option.relationships,
            "user_weight": weights.relationships,
            "effective_weight": weights.relationships,
            "emotion_adjustment": 0.0,
            "weighted_score": round(
                option.relationships * (weights.relationships / 100), 4
            ),
            "schwartz_category": "Benevolence / Conformity",
        }

        # --- Autonomy ---
        # Anger boosts autonomy weight — angry people value independence more
        autonomy_adj = (
            0.15 * self.intensity_scalar
            if self.emotional_state == "angry"
            else 0.0
        )
        effective_autonomy_weight = max(0, weights.autonomy + (autonomy_adj * 100))
        dimensions["autonomy"] = {
            "option_score": option.autonomy,
            "user_weight": weights.autonomy,
            "effective_weight": round(effective_autonomy_weight, 2),
            "emotion_adjustment": round(autonomy_adj * 100, 2),
            "weighted_score": round(
                option.autonomy * (effective_autonomy_weight / 100), 4
            ),
            "schwartz_category": "Self-Direction",
        }

        # --- Stability ---
        dimensions["stability"] = {
            "option_score": option.stability,
            "user_weight": weights.stability,
            "effective_weight": weights.stability,
            "emotion_adjustment": 0.0,
            "weighted_score": round(
                option.stability * (weights.stability / 100), 4
            ),
            "schwartz_category": "Security / Conformity",
        }

        # --- Achievement ---
        # Excitement boosts achievement weight slightly
        achievement_adj = (
            0.10 * self.intensity_scalar
            if self.emotional_state == "excited"
            else 0.0
        )
        effective_achievement_weight = max(0, weights.achievement + (achievement_adj * 100))
        dimensions["achievement"] = {
            "option_score": option.achievement,
            "user_weight": weights.achievement,
            "effective_weight": round(effective_achievement_weight, 2),
            "emotion_adjustment": round(achievement_adj * 100, 2),
            "weighted_score": round(
                option.achievement * (effective_achievement_weight / 100), 4
            ),
            "schwartz_category": "Achievement",
        }

        # --- Wellbeing ---
        dimensions["wellbeing"] = {
            "option_score": option.wellbeing,
            "user_weight": weights.wellbeing,
            "effective_weight": weights.wellbeing,
            "emotion_adjustment": 0.0,
            "weighted_score": round(
                option.wellbeing * (weights.wellbeing / 100), 4
            ),
            "schwartz_category": "Hedonism / Universalism",
        }

        # Step 3 — Sum all weighted scores
        # Max possible score = 10 (if all option scores are 10 and weights sum to 100)
        # So raw total is already on 0-10 scale
        raw_total = sum(d["weighted_score"] for d in dimensions.values())

        # Step 4 — Stress penalty
        # High stress options are penalized regardless of other scores
        # A great option that causes extreme stress isn't truly aligned
        # with wellbeing — Schwartz (1992) includes wellbeing as a core value
        stress_penalty = 0.0
        if option.stress_level >= 8:
            stress_penalty = 0.5   # High stress — significant penalty
            logger.debug(f"High stress penalty applied: -{stress_penalty}")
        elif option.stress_level >= 6:
            stress_penalty = 0.25  # Moderate stress — small penalty

        final_alignment = max(0.0, round(raw_total - stress_penalty, 4))

        # Step 5 — Find strongest and weakest value dimensions for this option
        sorted_dims = sorted(
            dimensions.items(),
            key=lambda x: x[1]["weighted_score"],
            reverse=True
        )
        strongest_value = sorted_dims[0][0]
        weakest_value = sorted_dims[-1][0]

        logger.info(
            f"Values alignment for '{option.name}': "
            f"raw={raw_total:.4f} stress_penalty={stress_penalty} "
            f"final={final_alignment:.4f} | "
            f"strongest={strongest_value} weakest={weakest_value}"
        )

        return {
            "option_name": option.name,
            "dimensions": dimensions,
            "raw_total": round(raw_total, 4),
            "stress_penalty": stress_penalty,
            "final_alignment_score": final_alignment,
            "strongest_value_dimension": strongest_value,
            "weakest_value_dimension": weakest_value,
            "emotion_distortion_type": distortion_type,
            "emotion_distortion_warning": (
                _get_distortion_warning(distortion_type, self.emotional_state)
                if distortion_type != "none"
                else None
            ),
            "research_basis": [
                "Schwartz, S.H. (1992) — Universals in the Content and Structure of Values",
                "Lerner, J.S. et al. (2015) — Emotion and Decision Making, Annual Review of Psychology",
            ]
        }


def _get_distortion_warning(distortion_type: str, emotion: str) -> str:
    """
    Returns a human-readable warning about how the current emotional
    state may be distorting value perception.
    Based on Lerner et al. (2015).
    """
    warnings = {
        "security_bias": (
            f"⚠ Your current {emotion} state may be causing you to "
            f"overweight financial security and underweight personal growth. "
            f"Lerner et al. (2015) found that {emotion} emotions increase "
            f"security-seeking behavior — consider how you'd weigh these "
            f"values on a calm day."
        ),
        "autonomy_bias": (
            f"⚠ Feeling {emotion} may be inflating how much you value "
            f"independence and autonomy right now. "
            f"This could be making options that offer more freedom "
            f"seem more attractive than they would otherwise."
        ),
        "present_bias": (
            f"⚠ Feeling {emotion} can cause present bias — "
            f"underweighting future benefits like growth and achievement "
            f"in favor of immediate comfort. "
            f"Lerner et al. (2015) documented this effect in sad emotional states."
        ),
        "optimism_bias": (
            f"⚠ Feeling {emotion} may be causing you to overweight "
            f"growth and achievement potential while underweighting "
            f"financial security risks. "
            f"Consider whether you'd rate these options the same "
            f"when feeling more neutral."
        ),
    }
    return warnings.get(distortion_type, "")


# ─── Quick Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from models.decision import DecisionOption, ValuesWeights

    # Test scenario: Passion-driven person considering freelancing
    # They love autonomy and growth, don't care much about financial security

    freelance_option = DecisionOption(
        name="Quit and freelance",
        financial_security=4,   # Low — income uncertainty
        personal_growth=9,      # High — massive learning opportunity
        relationships=6,        # Medium — less office politics
        autonomy=10,            # Maximum — full freedom
        stability=3,            # Low — very uncertain
        achievement=8,          # High — building something of your own
        wellbeing=7,            # Good — doing what you love
        stress_level=6,         # Moderate stress
    )

    stay_option = DecisionOption(
        name="Stay at current job",
        financial_security=8,   # High — stable salary
        personal_growth=3,      # Low — stagnating
        relationships=5,        # Medium
        autonomy=3,             # Low — boss, rules, meetings
        stability=9,            # High — very predictable
        achievement=3,          # Low — same work every day
        wellbeing=4,            # Poor — unhappy doing it
        stress_level=4,         # Lower stress
    )

    # Passion-driven person's weights — they care about growth and autonomy
    passion_weights = ValuesWeights(
        financial_security=5,   # Barely cares about money
        personal_growth=30,     # Top priority
        relationships=10,
        autonomy=30,            # Top priority
        stability=5,            # Doesn't need stability
        achievement=15,
        wellbeing=5,
    )

    # Test with neutral emotion first
    mapper_neutral = ValuesMapper(emotional_state="neutral", emotional_intensity=5)

    print("\n" + "="*60)
    print("PASSION-DRIVEN PERSON — VALUES ALIGNMENT TEST")
    print("="*60)

    for option in [freelance_option, stay_option]:
        result = mapper_neutral.compute_values_alignment(option, passion_weights)
        print(f"\nOption: {option.name}")
        print(f"Values Alignment Score: {result['final_alignment_score']}/10")
        print(f"Strongest dimension: {result['strongest_value_dimension']}")
        print(f"Weakest dimension: {result['weakest_value_dimension']}")
        print("Breakdown:")
        for dim, data in result["dimensions"].items():
            print(f"  {dim:25s}: score={data['option_score']}/10 × weight={data['user_weight']}% = {data['weighted_score']:.3f}")

    # Now test with anxious emotion — shows how anxiety distorts values
    print("\n" + "="*60)
    print("SAME PERSON — BUT FEELING ANXIOUS")
    print("="*60)
    mapper_anxious = ValuesMapper(emotional_state="anxious", emotional_intensity=8)
    result_anxious = mapper_anxious.compute_values_alignment(freelance_option, passion_weights)
    print(f"\nFreelance alignment (anxious): {result_anxious['final_alignment_score']}/10")
    print(f"Emotion warning: {result_anxious['emotion_distortion_warning']}")
    print("\n→ Notice how anxiety REDUCES the alignment score for freelancing")
    print("→ This is the emotion distortion DeciDr warns the user about")