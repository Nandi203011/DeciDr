# ============================================================
# engine/web_search.py — DeciDr
# Fetches real-world data for named entities in decisions
# using Tavily API + Groq/Llama for detection and mapping
#
# Detection: LLM-based (works for ANY company/product/place)
# Search: Tavily API (free tier: 1000 searches/month)
# Mapping: Groq/Llama maps fetched data to Schwartz dimensions
# ============================================================

import json
import re
from tavily import TavilyClient
from groq import Groq
from loguru import logger
from config import get_settings


class WebSearchEngine:
    """
    Fetches real-world data for named entities in decisions.

    Works for ANY named entity:
    - Job offers (TCS vs Honeywell, Zoho vs Freshworks)
    - Products (Speed 400 vs Himalayan, iPhone vs Samsung)
    - Colleges (IIT vs NIT, BITS vs VIT)
    - Cities (Bangalore vs Mumbai)
    - Anything with data on the internet
    """

    def __init__(self):
        settings = get_settings()
        self.tavily = TavilyClient(api_key=settings.tavily_api_key)
        self.groq = Groq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile"
        logger.info("WebSearchEngine initialized")

    def should_search(self, question: str, options: list) -> bool:
        """
        Uses LLM to detect if this decision involves named entities
        that have real-world data available online.

        Works for ANY entity — not limited to a hardcoded list.
        """
        prompt = f"""Does this decision involve specific named entities 
(companies, products, colleges, cities, brands, or services) 
that have real-world factual data available online?

Decision: {question}
Options: {options}

Examples that SHOULD search:
- "TCS vs Honeywell" → YES (real companies with salary data)
- "iPhone vs Samsung" → YES (real products with specs)
- "IIT vs NIT" → YES (real colleges with placement data)
- "Bangalore vs Mumbai" → YES (real cities with cost of living data)
- "Speed 400 vs Himalayan" → YES (real bikes with specs)
- "Zoho vs Freshworks" → YES (real companies)

Examples that should NOT search:
- "Should I stay or leave my relationship" → NO (no named entities)
- "Should I wake up early or sleep late" → NO (lifestyle, no entities)
- "Should I be more social or focus on work" → NO (personal choice)

Reply with ONLY one word: YES or NO"""

        try:
            response = self.groq.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.0,
            )
            answer = response.choices[0].message.content.strip().upper()
            result = "YES" in answer
            logger.info(f"Entity detection: {result} | question='{question[:50]}'")
            return result

        except Exception as e:
            logger.warning(f"Entity detection failed: {str(e)[:50]} — defaulting to False")
            return False

    def fetch_and_map(
        self,
        question: str,
        option_names: list,
        category: str
    ) -> dict:
        """
        Main method — fetches real data and maps to value dimensions.

        Returns:
            dict with pre-populated ratings for each option
        """
        logger.info(f"Fetching web data for: {option_names}")

        all_data = {}
        for option in option_names:
            search_results = self._search_option(option, question, category)
            all_data[option] = search_results

        mapped = self._map_to_dimensions(question, option_names, all_data, category)
        return mapped

    def _search_option(self, option: str, context: str, category: str) -> str:
        """Searches web for data about a specific option"""
        queries = self._build_queries(option, context, category)
        all_results = []

        for query in queries[:2]:
            try:
                result = self.tavily.search(
                    query=query,
                    search_depth="basic",
                    max_results=3,
                    include_answer=True,
                )
                if result.get("answer"):
                    all_results.append(result["answer"])
                for r in result.get("results", [])[:2]:
                    if r.get("content"):
                        all_results.append(r["content"][:300])
            except Exception as e:
                logger.warning(f"Search failed for '{query}': {str(e)[:50]}")

        return "\n".join(all_results)

    def _build_queries(self, option: str, context: str, category: str) -> list:
        """
        Builds targeted search queries based on category.
        Works for any option name the user provides.
        """
        queries = {
            "career": [
                f"{option} salary India 2025 Glassdoor review",
                f"{option} work life balance employee review India",
            ],
            "purchase": [
                f"{option} specifications price review 2025 India",
                f"{option} pros cons owner review mileage performance",
            ],
            "education": [
                f"{option} placement stats fees ranking 2025",
                f"{option} student review campus life experience",
            ],
            "financial": [
                f"{option} returns performance review 2025",
                f"{option} pros cons risk analysis",
            ],
            "lifestyle": [
                f"{option} cost of living quality of life 2025",
                f"{option} pros cons living experience",
            ],
            "relationship": [
                f"{option} review experience",
                f"{option} pros cons",
            ],
        }
        return queries.get(
            category,
            [f"{option} review pros cons 2025", f"{option} specifications comparison"]
        )

    def _map_to_dimensions(
        self,
        question: str,
        options: list,
        data: dict,
        category: str
    ) -> dict:
        """
        Uses Groq/Llama to map fetched web data to our
        Schwartz value dimensions (1-10 scale).
        """
        data_summary = ""
        for option, content in data.items():
            data_summary += f"\n\n=== {option} ===\n{content[:600]}"

        # Build dynamic JSON template for any number of options
        options_template = {}
        for opt in options:
            options_template[opt] = {
                "financial_security": 5,
                "personal_growth": 5,
                "relationships": 5,
                "autonomy": 5,
                "stability": 5,
                "achievement": 5,
                "wellbeing": 5,
                "stress_level": 5,
                "data_summary": "summary here"
            }

        prompt = f"""You are a data analyst for DeciDr, a psychology-backed decision tool.

Decision: {question}
Category: {category}
Options being compared: {', '.join(options)}

Real-world data fetched from the web:
{data_summary}

Based on this real data, rate each option on these dimensions (1-10 scale):
- financial_security: Financial stability, salary, cost, value for money
- personal_growth: Learning, skill development, career growth potential
- relationships: Team culture, social impact, community
- autonomy: Freedom, independence, control
- stability: Security, reliability, consistency
- achievement: Performance, prestige, accomplishment potential
- wellbeing: Work-life balance, comfort, happiness, health
- stress_level: How much stress this option causes (higher = more stress)

Rules:
- Base ratings ONLY on the fetched data, not assumptions
- If data is missing for a dimension, use 5 as neutral
- data_summary should mention 2-3 specific facts from the search results
- Return ONLY valid JSON, no explanation, no markdown backticks

Return this exact JSON structure:
{{
  "options": {{
    {json.dumps(options_template, indent=4)[1:-1]}
  }},
  "search_confidence": "medium",
  "data_sources_used": ["Glassdoor", "web reviews"]
}}"""

        try:
            response = self.groq.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.1,
            )

            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"```json\s*", "", raw)
            raw = re.sub(r"```\s*", "", raw)

            mapped = json.loads(raw)
            logger.info(
                f"Web data mapped | "
                f"confidence={mapped.get('search_confidence')} | "
                f"options={list(mapped.get('options', {}).keys())}"
            )
            return mapped

        except Exception as e:
            logger.error(f"Mapping failed: {type(e).__name__}: {str(e)[:100]}")
            return self._neutral_ratings(options)

    def _neutral_ratings(self, options: list) -> dict:
        """Returns neutral 5/10 ratings as fallback"""
        neutral = {
            "financial_security": 5, "personal_growth": 5,
            "relationships": 5, "autonomy": 5, "stability": 5,
            "achievement": 5, "wellbeing": 5, "stress_level": 5,
            "data_summary": "Could not fetch real data — using neutral ratings."
        }
        return {
            "options": {opt: neutral.copy() for opt in options},
            "search_confidence": "low",
            "data_sources_used": []
        }


# ─── Quick Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    engine = WebSearchEngine()

    tests = [
        {
            "question": "Should I join Zoho or Freshworks as SDE?",
            "options": ["Zoho", "Freshworks"],
            "category": "career"
        },
        {
            "question": "Should I buy Triumph Speed 400 or Royal Enfield Himalayan?",
            "options": ["Triumph Speed 400", "Royal Enfield Himalayan"],
            "category": "purchase"
        },
        {
            "question": "Should I wake up early or sleep late?",
            "options": ["Wake up early", "Sleep late"],
            "category": "lifestyle"
        },
    ]

    for test in tests:
        print("\n" + "="*60)
        print(f"TEST: {test['question']}")
        print("="*60)

        should = engine.should_search(test["question"], test["options"])
        print(f"Should search web: {should}")

        if should:
            result = engine.fetch_and_map(
                question=test["question"],
                option_names=test["options"],
                category=test["category"]
            )
            print(f"Search confidence: {result.get('search_confidence')}")
            for opt, data in result.get("options", {}).items():
                print(f"\n  {opt}:")
                print(f"    Financial Security: {data.get('financial_security')}/10")
                print(f"    Growth:             {data.get('personal_growth')}/10")
                print(f"    Wellbeing:          {data.get('wellbeing')}/10")
                print(f"    Summary: {data.get('data_summary', '')[:120]}")
        else:
            print("→ No web search needed — pure psychology analysis")