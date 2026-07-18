# ============================================================
# engine/parser.py — DeciDr
# Extracts structured DecisionInput from free-form text
# using Groq/Llama as the extraction engine.
#
# Design principle: LLM is used ONLY for extraction here —
# not for making the decision. The psychology engine still
# makes the actual recommendation.
# ============================================================

import json
import re
from groq import Groq
from loguru import logger
from config import get_settings


# ─── Extraction Prompt ────────────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are a structured data extraction engine for DeciDr, 
a psychology-backed decision analysis tool.

Your ONLY job is to extract structured information from the user's free-form text 
and return it as a valid JSON object. You do NOT make recommendations or give advice.

Extract the following from the user's text:

1. question (string): The core decision question (rephrase as "Should I X or Y?")
2. category (string): One of: career, education, financial, purchase, relationship, lifestyle, other
3. options (array): 2-5 options being considered. For each option extract:
   - name (string): Short name for this option
   - financial_security (1-10): How financially secure is this option?
   - personal_growth (1-10): Growth potential
   - relationships (1-10): Impact on relationships
   - autonomy (1-10): Freedom and control
   - stability (1-10): Predictability
   - achievement (1-10): Achievement potential
   - wellbeing (1-10): Happiness impact
   - stress_level (1-10): Stress caused (higher = more stress)
4. values_weights (object): How much this person weights each value (must sum to 100):
   - financial_security, personal_growth, relationships, autonomy, stability, achievement, wellbeing
5. emotional_state (string): One of: calm, neutral, anxious, angry, sad, fearful, excited
6. emotional_intensity (1-10): How intense is the emotion?
7. risk_tolerance (string): One of: low, medium, high
8. time_already_invested_months (integer): Months invested in current path (0 if not mentioned)
9. money_already_invested (float): Money invested (0 if not mentioned)
10. current_situation_satisfaction (1-10): Satisfaction with current situation
11. is_reversible (boolean): Can the decision be undone?
12. time_pressure (boolean): Is there time pressure?

RULES:
- Always return ONLY valid JSON — no explanation, no markdown, no backticks
- If information is not mentioned, use sensible defaults
- Values weights MUST sum to exactly 100
- Infer emotional state from tone and words used
- Infer risk tolerance from how the person describes their fears
- If only one option is mentioned, infer a reasonable second option (e.g. "stay" vs "change")
- All numeric fields must be integers or floats within their specified ranges

Return ONLY the JSON object, nothing else."""


class DecisionParser:
    """
    Extracts structured DecisionInput from free-form natural language.
    
    Uses Groq/Llama to understand the user's situation and convert it
    into the structured format our psychology engine needs.
    """

    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile"
        logger.info(f"DecisionParser initialized | model={self.model}")

    def parse(self, user_text: str) -> dict:
        """
        Parses free-form text into structured DecisionInput dict.
        
        Args:
            user_text: Raw text from the user describing their decision
            
        Returns:
            dict matching DecisionInput schema
        """
        logger.info(f"Parsing decision text | length={len(user_text)} chars")

        # Security — limit input length
        user_text = user_text[:2000].strip()

        if len(user_text) < 10:
            raise ValueError("Please describe your decision in more detail.")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Extract the decision structure from this text:\n\n{user_text}"}
                ],
                max_tokens=1500,
                temperature=0.1,  # Low temperature — we want consistent extraction
                top_p=0.9,
            )

            raw = response.choices[0].message.content.strip()
            logger.debug(f"Raw extraction response: {raw[:200]}...")

            # Clean response — remove any markdown if model added it
            raw = re.sub(r"```json\s*", "", raw)
            raw = re.sub(r"```\s*", "", raw)
            raw = raw.strip()

            # Parse JSON
            extracted = json.loads(raw)

            # Validate and fix weights sum
            extracted = self._fix_weights(extracted)

            # Ensure all required fields exist with defaults
            extracted = self._apply_defaults(extracted)

            logger.info(
                f"Parsing successful | "
                f"category={extracted.get('category')} | "
                f"options={len(extracted.get('options', []))} | "
                f"emotion={extracted.get('emotional_state')}"
            )

            return extracted

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)[:100]}")
            raise ValueError("Could not extract decision structure. Please try being more specific.")

        except Exception as e:
            logger.error(f"Parser error: {type(e).__name__}: {str(e)[:100]}")
            raise ValueError("Something went wrong while parsing your decision. Please try again.")

    def _fix_weights(self, data: dict) -> dict:
        """Ensures values_weights sum to exactly 100"""
        weights = data.get("values_weights", {})
        keys = ["financial_security", "personal_growth", "relationships",
                "autonomy", "stability", "achievement", "wellbeing"]

        # Fill missing keys with equal distribution
        for key in keys:
            if key not in weights:
                weights[key] = 0

        total = sum(weights.values())

        if total == 0:
            # All zeros — distribute equally
            per = 100 // len(keys)
            remainder = 100 - (per * len(keys))
            for i, key in enumerate(keys):
                weights[key] = per + (1 if i < remainder else 0)
        elif total != 100:
            # Scale to 100
            factor = 100 / total
            scaled = {k: int(v * factor) for k, v in weights.items()}
            # Fix rounding to ensure sum is exactly 100
            diff = 100 - sum(scaled.values())
            scaled[keys[0]] += diff
            weights = scaled

        data["values_weights"] = weights
        return data

    def _apply_defaults(self, data: dict) -> dict:
        """Applies sensible defaults for any missing fields"""
        defaults = {
            "emotional_intensity": 5,
            "risk_tolerance": "medium",
            "time_already_invested_months": 0,
            "money_already_invested": 0.0,
            "current_situation_satisfaction": 5,
            "is_reversible": True,
            "time_pressure": False,
        }
        for key, val in defaults.items():
            if key not in data or data[key] is None:
                data[key] = val

        # Ensure options have all required fields
        option_defaults = {
            "financial_security": 5,
            "personal_growth": 5,
            "relationships": 5,
            "autonomy": 5,
            "stability": 5,
            "achievement": 5,
            "wellbeing": 5,
            "stress_level": 5,
        }
        for opt in data.get("options", []):
            for key, val in option_defaults.items():
                if key not in opt or opt[key] is None:
                    opt[key] = val
            # Clamp values to 1-10
            for key in option_defaults:
                opt[key] = max(1, min(10, int(opt.get(key, 5))))

        return data


# ─── Quick Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    parser = DecisionParser()

    test_text = """
    I've been working at this company for 4 years and I really hate it. 
    The pay is decent but I have no freedom and I'm not growing at all.
    I want to quit and start freelancing but I'm really scared and anxious 
    about the money. My friends think I should stay because the job market 
    is tough right now. I feel like I'm wasting my life but I also have 
    some savings. I don't know what to do — should I just stay or take 
    the risk and go freelance?
    """

    print("\n" + "="*60)
    print("DECIDR NATURAL LANGUAGE PARSER TEST")
    print("="*60)
    print(f"Input: {test_text[:100]}...")

    result = parser.parse(test_text)

    print(f"\nExtracted:")
    print(f"  Question: {result['question']}")
    print(f"  Category: {result['category']}")
    print(f"  Options: {[o['name'] for o in result['options']]}")
    print(f"  Emotion: {result['emotional_state']} ({result['emotional_intensity']}/10)")
    print(f"  Risk tolerance: {result['risk_tolerance']}")
    print(f"  Weights sum: {sum(result['values_weights'].values())}")
    print(f"\nFull extracted data:")
    print(json.dumps(result, indent=2))
