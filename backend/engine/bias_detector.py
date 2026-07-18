# ============================================================
# engine/bias_detector.py — DeciDr
# Rule-based cognitive bias detection engine
#
# Research basis:
#   - Arkes & Blumer (1985) — Sunk Cost Fallacy
#   - Samuelson & Zeckhauser (1988) — Status Quo Bias
#   - Kahneman & Tversky (1979, 1992) — Loss Aversion, CPT
#   - Lerner et al. (2015) — Emotion-induced bias
#   - Tversky & Kahneman (1974) — Heuristics and Biases
#   - Evans & Stanovich (2013) — Dual Process Theory
#   - Ramos, Campos & Baião (2024) — ABI approach (automated
#     bias identification — the paper you uploaded)
#
# Key insight from ABI paper: bias detection should be
# automatic, rule-based, and explained to the user in
# context — not just flagged generically.
# ============================================================

from dataclasses import dataclass
from loguru import logger
from models.decision import DecisionInput


# ─── Bias Data Structure ──────────────────────────────────────────────────────

@dataclass
class DetectedBias:
    """
    A single detected cognitive bias with full context.
    Every bias must cite its research source — core DeciDr principle.
    """
    name: str                        # Bias name
    severity: str                    # "low" | "medium" | "high"
    confidence: float                # 0.0 - 1.0 how confident we are
    how_it_affects: str              # Specific to THIS decision
    what_to_do: str                  # Actionable debiasing suggestion
    score_adjustment: float          # How much to adjust final score (-1.0 to 0.0)
    research_source: str             # Always cite the paper


# ─── Bias Detector ────────────────────────────────────────────────────────────

class BiasDetector:
    """
    Automatically detects cognitive biases in a decision input.

    Inspired by the ABI (Automatic Bias Identification) approach
    from Ramos, Campos & Baião (2024) — which proved that automated
    bias detection significantly improves decision-maker awareness.

    Unlike ABI which focused only on financial GO/KILL decisions,
    DeciDr's bias detector works across ALL personal decision types.

    Detection is rule-based — each bias has specific trigger conditions
    derived directly from the psychology research that documented it.
    """

    def __init__(self, decision_input: DecisionInput):
        self.input = decision_input
        self.detected_biases: list[DetectedBias] = []
        logger.info(
            f"BiasDetector initialized | "
            f"category={decision_input.category} | "
            f"emotion={decision_input.emotional_state} | "
            f"options={len(decision_input.options)}"
        )

    def run_all_detectors(self) -> list[DetectedBias]:
        """
        Runs all bias detectors in sequence.
        Returns list of detected biases sorted by severity.
        """
        logger.info("Running full bias detection pipeline...")

        # Run each detector
        self._detect_sunk_cost_fallacy()
        self._detect_status_quo_bias()
        self._detect_loss_aversion_override()
        self._detect_emotional_decision_making()
        self._detect_time_pressure_bias()
        self._detect_reversibility_neglect()
        self._detect_present_bias()

        # Sort by severity (high → medium → low)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        self.detected_biases.sort(
            key=lambda b: severity_order.get(b.severity, 3)
        )

        logger.info(
            f"Bias detection complete | "
            f"total={len(self.detected_biases)} | "
            f"high={sum(1 for b in self.detected_biases if b.severity == 'high')} | "
            f"medium={sum(1 for b in self.detected_biases if b.severity == 'medium')} | "
            f"low={sum(1 for b in self.detected_biases if b.severity == 'low')}"
        )

        return self.detected_biases

    # ─── Individual Bias Detectors ────────────────────────────────────────────

    def _detect_sunk_cost_fallacy(self):
        """
        Sunk Cost Fallacy — Arkes & Blumer (1985)

        Trigger: User has invested significant time or money in the
        current path AND rates current situation satisfaction LOW.

        This pattern = they're staying because of past investment,
        not because the current situation is actually good.

        ABI paper reference: The sunk cost fallacy was the primary
        bias used in Ramos et al. (2024) experiments because it
        "triggers risk seeking preference when dealing with losses."
        """
        time_invested = self.input.time_already_invested_months or 0
        money_invested = self.input.money_already_invested or 0.0
        satisfaction = self.input.current_situation_satisfaction

        # Trigger conditions (from Arkes & Blumer 1985):
        # 1. Significant time investment (>12 months)
        # 2. OR significant money investment (>10,000)
        # 3. AND low satisfaction with current situation (≤5)
        # Pattern: invested a lot + unhappy = classic sunk cost trap

        time_trigger = time_invested >= 12
        money_trigger = money_invested >= 10_000
        unhappy = satisfaction <= 5

        if (time_trigger or money_trigger) and unhappy:
            # Calculate severity based on investment size and unhappiness
            if time_invested >= 36 or money_invested >= 50_000:
                severity = "high"
                confidence = 0.85
                score_adj = -0.8
            elif time_invested >= 24 or money_invested >= 25_000:
                severity = "high"
                confidence = 0.75
                score_adj = -0.6
            else:
                severity = "medium"
                confidence = 0.65
                score_adj = -0.4

            time_str = f"{time_invested} months" if time_invested > 0 else ""
            money_str = f"₹{money_invested:,.0f}" if money_invested > 0 else ""
            investment_str = " and ".join(filter(None, [time_str, money_str]))

            bias = DetectedBias(
                name="Sunk Cost Fallacy",
                severity=severity,
                confidence=confidence,
                how_it_affects=(
                    f"You've invested {investment_str} in your current path, "
                    f"yet rate your current satisfaction at only {satisfaction}/10. "
                    f"This pattern suggests you may be continuing because of what "
                    f"you've already put in — not because the current path is good. "
                    f"Past investments are gone regardless of what you decide now."
                ),
                what_to_do=(
                    "Ask yourself: 'If I was starting fresh today with zero "
                    "prior investment, would I still choose the current path?' "
                    "If no — the sunk cost fallacy may be trapping you. "
                    "Kahneman et al. (2021) recommend imagining a trusted friend "
                    "in your situation — what would you advise them to do?"
                ),
                score_adjustment=score_adj,
                research_source=(
                    "Arkes, H.R. & Blumer, C. (1985) — The Psychology of Sunk Cost. "
                    "Organizational Behavior and Human Decision Processes, 35(1), 124-140."
                )
            )
            self.detected_biases.append(bias)
            logger.warning(
                f"SUNK COST FALLACY detected | severity={severity} | "
                f"time={time_invested}mo money=₹{money_invested:,.0f} "
                f"satisfaction={satisfaction}/10"
            )

    def _detect_status_quo_bias(self):
        """
        Status Quo Bias — Samuelson & Zeckhauser (1988)

        Trigger: User rates current situation satisfaction HIGH
        AND the decision involves a reversible change.

        High satisfaction with status quo + reversible decision =
        they may be preferring the current state just because
        it's familiar, not because it's actually better.

        Samuelson & Zeckhauser proved people systematically prefer
        the existing state even when alternatives are objectively better.
        """
        satisfaction = self.input.current_situation_satisfaction
        is_reversible = self.input.is_reversible
        emotional_state = self.input.emotional_state.value

        # Trigger: high satisfaction + reversible (low actual risk)
        # The bias is strongest when the decision is reversible because
        # there's objectively less reason to fear change
        high_satisfaction = satisfaction >= 7
        anxious_or_fearful = emotional_state in ["anxious", "fearful"]

        if high_satisfaction and is_reversible:
            # Stronger if also feeling anxious/fearful
            if anxious_or_fearful:
                severity = "high"
                confidence = 0.80
                score_adj = -0.5
            else:
                severity = "medium"
                confidence = 0.65
                score_adj = -0.3

            bias = DetectedBias(
                name="Status Quo Bias",
                severity=severity,
                confidence=confidence,
                how_it_affects=(
                    f"You rate your current situation {satisfaction}/10 and "
                    f"this decision is reversible — meaning the actual risk "
                    f"of change is lower than it feels. "
                    f"Status quo bias makes the current state feel safer "
                    f"than it actually is, purely because it's familiar. "
                    f"This can prevent beneficial changes even when the "
                    f"alternative is objectively better."
                ),
                what_to_do=(
                    "Since this decision is reversible, the cost of trying "
                    "the alternative is lower than your brain is signaling. "
                    "Ask: 'Am I rating my current situation highly because "
                    "it's genuinely good, or because it's what I know?' "
                    "Samuelson & Zeckhauser (1988) found people systematically "
                    "prefer the status quo even when alternatives are better."
                ),
                score_adjustment=score_adj,
                research_source=(
                    "Samuelson, W. & Zeckhauser, R. (1988) — Status Quo Bias "
                    "in Decision Making. Journal of Risk and Uncertainty, 1(1), 7-59."
                )
            )
            self.detected_biases.append(bias)
            logger.warning(
                f"STATUS QUO BIAS detected | severity={severity} | "
                f"satisfaction={satisfaction}/10 reversible={is_reversible}"
            )

    def _detect_loss_aversion_override(self):
        """
        Loss Aversion Override — Kahneman & Tversky (1979, 1992)

        Trigger: Decision is NOT reversible AND user has LOW risk tolerance
        AND current situation satisfaction is LOW.

        Pattern: They know the current situation is bad, they know the
        decision can't be undone, and they're risk-averse —
        this combination causes people to stay in bad situations
        far longer than rational analysis would suggest.

        The λ=2.25 coefficient means losses feel 2.25x worse than
        equivalent gains feel good — making irreversible decisions
        feel disproportionately scary.
        """
        is_reversible = self.input.is_reversible
        risk_tolerance = self.input.risk_tolerance.value
        satisfaction = self.input.current_situation_satisfaction

        not_reversible = not is_reversible
        low_risk = risk_tolerance == "low"
        low_satisfaction = satisfaction <= 4

        if not_reversible and low_risk and low_satisfaction:
            bias = DetectedBias(
                name="Loss Aversion Override",
                severity="high",
                confidence=0.80,
                how_it_affects=(
                    f"You're in a situation you rate {satisfaction}/10, "
                    f"but because this decision feels irreversible and "
                    f"you have low risk tolerance, loss aversion (λ=2.25) "
                    f"is amplifying the perceived pain of change by 2.25x. "
                    f"Your brain treats 'what you might lose' as 2.25x more "
                    f"painful than 'what you might gain' — even when staying "
                    f"is clearly worse."
                ),
                what_to_do=(
                    "Separate the fear of loss from the actual probability "
                    "of loss. Ask: 'What is the realistic worst case if I "
                    "change? And what is the realistic worst case if I stay?' "
                    "Kahneman (2011) recommends pre-mortem thinking — imagine "
                    "both choices have already happened and work backwards "
                    "from the outcome."
                ),
                score_adjustment=-0.7,
                research_source=(
                    "Kahneman, D. & Tversky, A. (1979) — Prospect Theory: "
                    "An Analysis of Decision Under Risk. Econometrica, 47(2). "
                    "Tversky & Kahneman (1992) — λ=2.25 loss aversion coefficient."
                )
            )
            self.detected_biases.append(bias)
            logger.warning(
                f"LOSS AVERSION OVERRIDE detected | "
                f"reversible={is_reversible} risk={risk_tolerance} "
                f"satisfaction={satisfaction}/10"
            )

    def _detect_emotional_decision_making(self):
        """
        Emotional Decision Making — Lerner et al. (2015)

        Trigger: High emotional intensity (≥7) in a high-stakes emotion
        (angry, anxious, fearful, sad).

        These emotions have documented directional effects on
        decision quality — they systematically push decisions
        in specific directions regardless of the actual facts.

        Evans & Stanovich (2013): High emotion activates System 1
        (fast, intuitive) and suppresses System 2 (slow, deliberate).
        """
        intensity = self.input.emotional_intensity
        state = self.input.emotional_state.value

        high_impact_emotions = ["angry", "anxious", "fearful", "sad"]
        is_high_impact = state in high_impact_emotions
        is_intense = intensity >= 7

        if is_high_impact and is_intense:
            severity = "high" if intensity >= 9 else "medium"
            confidence = 0.75

            emotion_effects = {
                "angry": "increases risk-taking and impulsive decisions",
                "anxious": "increases risk-aversion and security-seeking",
                "fearful": "causes severe risk-aversion and avoidance",
                "sad": "increases present bias and impatience",
            }
            effect = emotion_effects.get(state, "distorts judgment")

            bias = DetectedBias(
                name="Emotional Decision Making",
                severity=severity,
                confidence=confidence,
                how_it_affects=(
                    f"You're feeling {state} at intensity {intensity}/10. "
                    f"Research shows {state} emotions specifically {effect}. "
                    f"At this intensity, System 1 (fast, emotional thinking) "
                    f"is dominating System 2 (slow, rational thinking). "
                    f"This decision may feel clearer than it actually is."
                ),
                what_to_do=(
                    f"Lerner et al. (2015) strongly recommend delaying "
                    f"important decisions when feeling {state} at high intensity. "
                    f"If delay isn't possible, explicitly ask: 'Would I make "
                    f"the same choice if I felt calm right now?' "
                    f"Evans & Stanovich (2013): force System 2 by writing "
                    f"out your reasoning before deciding."
                ),
                score_adjustment=-0.4,
                research_source=(
                    "Lerner, J.S. et al. (2015) — Emotion and Decision Making. "
                    "Annual Review of Psychology, 66, 799-823. "
                    "Evans & Stanovich (2013) — Dual-Process Theories of Higher Cognition."
                )
            )
            self.detected_biases.append(bias)
            logger.warning(
                f"EMOTIONAL DECISION MAKING detected | "
                f"emotion={state} intensity={intensity}/10"
            )

    def _detect_time_pressure_bias(self):
        """
        Time Pressure Bias — Evans & Stanovich (2013)

        Trigger: User is under time pressure.

        Time pressure forces System 1 thinking (fast, heuristic-based)
        and prevents the deliberate System 2 analysis that good
        decisions require. Kahneman (2011) documented that most
        cognitive biases are amplified under time pressure.
        """
        if self.input.time_pressure:
            bias = DetectedBias(
                name="Time Pressure Bias",
                severity="medium",
                confidence=0.70,
                how_it_affects=(
                    "You're under time pressure to decide. Time pressure "
                    "activates System 1 (fast, intuitive) thinking and "
                    "suppresses the deliberate System 2 analysis needed "
                    "for important decisions. This amplifies ALL other "
                    "cognitive biases present in this decision."
                ),
                what_to_do=(
                    "Question whether the deadline is real or perceived. "
                    "Most self-imposed time pressure isn't actually urgent. "
                    "If the deadline is real, at minimum write down your "
                    "top 3 reasons for each option before deciding — "
                    "this forces minimal System 2 engagement. "
                    "Kahneman (2011): 'Nothing in life is as important as "
                    "you think it is while you are thinking about it.'"
                ),
                score_adjustment=-0.2,
                research_source=(
                    "Evans, J.S.B.T. & Stanovich, K.E. (2013) — Dual-Process "
                    "Theories of Higher Cognition. Perspectives on Psychological "
                    "Science, 8(3), 223-241. Kahneman, D. (2011) — Thinking, "
                    "Fast and Slow."
                )
            )
            self.detected_biases.append(bias)
            logger.warning("TIME PRESSURE BIAS detected")

    def _detect_reversibility_neglect(self):
        """
        Reversibility Neglect — Kahneman (2011)

        Trigger: Decision IS reversible but user has HIGH emotional
        intensity or LOW risk tolerance.

        People treat reversible decisions as if they're permanent,
        causing unnecessary anxiety and risk-aversion.
        The psychological impact of a reversible decision should be
        much lower than an irreversible one — but often isn't.
        """
        is_reversible = self.input.is_reversible
        intensity = self.input.emotional_intensity
        risk_tolerance = self.input.risk_tolerance.value

        if is_reversible and (intensity >= 7 or risk_tolerance == "low"):
            bias = DetectedBias(
                name="Reversibility Neglect",
                severity="low",
                confidence=0.60,
                how_it_affects=(
                    "This decision is reversible — you can change course "
                    "if it doesn't work out. But your emotional intensity "
                    "or risk profile suggests you may be treating it as "
                    "permanent. Kahneman (2011) documented that people "
                    "systematically ignore reversibility, causing unnecessary "
                    "stress and over-caution."
                ),
                what_to_do=(
                    "Remind yourself explicitly: this is NOT permanent. "
                    "Define what 'reversing' would actually look like — "
                    "how long would it take, what would it cost? "
                    "Often the 'escape hatch' is much easier than feared. "
                    "This should meaningfully reduce your perceived risk."
                ),
                score_adjustment=-0.1,
                research_source=(
                    "Kahneman, D. (2011) — Thinking, Fast and Slow. "
                    "Farrar, Straus and Giroux. Chapter on reversibility "
                    "and the focusing illusion."
                )
            )
            self.detected_biases.append(bias)
            logger.info("REVERSIBILITY NEGLECT detected (low severity)")

    def _detect_present_bias(self):
        """
        Present Bias — Lerner et al. (2015), Kahneman (2011)

        Trigger: User is feeling sad OR has high emotional intensity
        AND the decision involves long-term outcomes (career, education).

        Present bias = overweighting immediate costs/benefits vs
        future costs/benefits. Sad people are especially prone to
        this — they want relief NOW, not future gain.
        """
        state = self.input.emotional_state.value
        intensity = self.input.emotional_intensity
        category = self.input.category.value

        long_term_categories = ["career", "education", "lifestyle"]
        is_long_term = category in long_term_categories
        sad_or_intense = state == "sad" or (intensity >= 8)

        if is_long_term and sad_or_intense:
            bias = DetectedBias(
                name="Present Bias",
                severity="medium",
                confidence=0.65,
                how_it_affects=(
                    f"This is a {category} decision with long-term consequences, "
                    f"but your current emotional state may be causing you to "
                    f"overweight immediate comfort over future benefit. "
                    f"Present bias makes short-term relief feel more valuable "
                    f"than it actually is relative to long-term outcomes."
                ),
                what_to_do=(
                    "Project yourself 5 years forward. Which option would "
                    "the future version of you be more grateful for? "
                    "Lerner et al. (2015) found that temporal distancing — "
                    "imagining your future self — effectively counteracts "
                    "present bias in long-term decisions."
                ),
                score_adjustment=-0.3,
                research_source=(
                    "Lerner, J.S. et al. (2015) — Emotion and Decision Making. "
                    "Annual Review of Psychology, 66, 799-823."
                )
            )
            self.detected_biases.append(bias)
            logger.warning(
                f"PRESENT BIAS detected | category={category} "
                f"emotion={state} intensity={intensity}/10"
            )

    def get_total_score_adjustment(self) -> float:
        """
        Returns total score adjustment from all detected biases.
        Capped at -2.0 to prevent extreme penalization.
        """
        total = sum(b.score_adjustment for b in self.detected_biases)
        return max(-2.0, round(total, 4))

    def get_summary(self) -> dict:
        """Returns a clean summary of all detected biases"""
        return {
            "total_biases_detected": len(self.detected_biases),
            "high_severity": [b.name for b in self.detected_biases if b.severity == "high"],
            "medium_severity": [b.name for b in self.detected_biases if b.severity == "medium"],
            "low_severity": [b.name for b in self.detected_biases if b.severity == "low"],
            "total_score_adjustment": self.get_total_score_adjustment(),
            "biases": [
                {
                    "name": b.name,
                    "severity": b.severity,
                    "confidence": b.confidence,
                    "how_it_affects": b.how_it_affects,
                    "what_to_do": b.what_to_do,
                    "score_adjustment": b.score_adjustment,
                    "research_source": b.research_source,
                }
                for b in self.detected_biases
            ]
        }


# ─── Quick Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    from models.decision import (
        DecisionInput, DecisionOption, ValuesWeights,
        DecisionCategory, EmotionalState, RiskTolerance
    )

    # Test: Person who's been at a job 4 years, unhappy, anxious, time pressure
    # Classic sunk cost + status quo + emotional bias scenario

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
        time_already_invested_months=48,   # 4 years at job
        money_already_invested=0,
        current_situation_satisfaction=3,  # Very unhappy
        is_reversible=True,
        time_pressure=True,
    )

    detector = BiasDetector(test_input)
    biases = detector.run_all_detectors()
    summary = detector.get_summary()

    print("\n" + "="*60)
    print("BIAS DETECTION REPORT — DeciDr")
    print("="*60)
    print(f"Total biases detected: {summary['total_biases_detected']}")
    print(f"High severity: {summary['high_severity']}")
    print(f"Medium severity: {summary['medium_severity']}")
    print(f"Low severity: {summary['low_severity']}")
    print(f"Total score adjustment: {summary['total_score_adjustment']}")

    print("\n--- DETAILED BREAKDOWN ---")
    for bias in summary["biases"]:
        print(f"\n🔴 {bias['name']} [{bias['severity'].upper()}] "
              f"(confidence: {bias['confidence']*100:.0f}%)")
        print(f"   How it affects you: {bias['how_it_affects'][:120]}...")
        print(f"   What to do: {bias['what_to_do'][:100]}...")
        print(f"   Score adjustment: {bias['score_adjustment']}")
        print(f"   Source: {bias['research_source'][:80]}...")