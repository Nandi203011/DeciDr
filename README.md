# DeciDr — Psychology-Backed Decision Engine

> Making better decisions through behavioral science, not gut feeling.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal.svg)](https://fastapi.tiangolo.com)

---

## What is DeciDr?

DeciDr is a personal decision analysis engine that combines **three layers of psychology** to help you make better decisions — career, purchases, education, relationships, and more.

Unlike a simple pros/cons list, DeciDr:
- Calculates the **psychological value** of each option using Nobel Prize-winning formulas
- Detects **cognitive biases** distorting your judgment (with research citations)
- Weights decisions against **your personal values** — not generic metrics
- Fetches **real-world data** (salaries, specs, reviews) for named entities
- Accepts **natural language input** — just describe your situation

---

## Psychology Framework

DeciDr implements three research-backed layers:

### Layer 1 — Cumulative Prospect Theory (CPT)
**Reference:** Kahneman, D. & Tversky, A. (1992) — *Advances in Prospect Theory*

Calculates the **psychological value** of each option using empirically-derived parameters:
```
v(x) = x^α              if x ≥ 0  (gains)
v(x) = -λ × (-x)^β     if x < 0  (losses)

α = β = 0.88  (diminishing sensitivity)
λ = 2.25      (loss aversion — losses feel 2.25x worse than equivalent gains)
γ = 0.61      (probability weighting)
```

### Layer 2 — Schwartz Values Theory
**Reference:** Schwartz, S.H. (1992) — *Universals in the Content and Structure of Values*

Weights each option against the user's personal value priorities across 7 dimensions: financial security, personal growth, relationships, autonomy, stability, achievement, and wellbeing.

### Layer 3 — Automated Bias Detection
**Reference:** Ramos, Campos & Baião (2024) — *ABI: Automatic Bias Identification* (arXiv:2405.14067)

Detects 7 cognitive biases with research citations:

| Bias | Research Source |
|------|----------------|
| Sunk Cost Fallacy | Arkes & Blumer (1985) |
| Status Quo Bias | Samuelson & Zeckhauser (1988) |
| Loss Aversion Override | Kahneman & Tversky (1979) |
| Emotional Decision Making | Lerner et al. (2015) |
| Time Pressure Bias | Evans & Stanovich (2013) |
| Present Bias | Lerner et al. (2015) |
| Reversibility Neglect | Kahneman (2011) |

---

## Features

- **⚡ Quick Mode** — Describe your decision in plain text, DeciDr extracts structure automatically using LLM
- **🎯 Guided Form** — 4-step structured input for precise control
- **🌐 Web Search Layer** — Auto-detects named entities (companies, products, colleges) and fetches real-world data
- **🔍 Bias Detection** — 7 cognitive biases detected with severity ratings and research citations
- **📊 Transparency** — Full breakdown of how scores are calculated
- **🔮 Pre-Mortem Analysis** — Klein (2007) technique to stress-test decisions
- **⚡ Second-Order Thinking** — What happens AFTER you decide?
- **📚 Research Citations** — Every recommendation cites the paper it came from

---

## Tech Stack

### Backend
```
Python 3.11+
FastAPI          — REST API framework
SQLAlchemy       — ORM (SQLite database)
Groq API         — LLM inference (Llama 3.3 70B) — free tier
Tavily API       — Web search for real-world data — free tier
Pydantic         — Input validation and data modeling
SlowAPI          — Rate limiting
Loguru           — Structured logging
```

### Frontend
```
Next.js 16       — React framework
shadcn/ui        — UI components (MIT License)
Tailwind CSS     — Styling
Axios            — HTTP client
```

---

## Project Structure

```
decidr/
├── backend/
│   ├── engine/
│   │   ├── prospect_theory.py   ← CPT formulas (Kahneman & Tversky 1992)
│   │   ├── values_mapper.py     ← Schwartz values alignment
│   │   ├── bias_detector.py     ← 7 cognitive bias detectors
│   │   ├── scorer.py            ← Master scoring engine
│   │   ├── narrator.py          ← AI narrative generation (Groq)
│   │   ├── parser.py            ← NLP input extraction (Groq)
│   │   └── web_search.py        ← Real-world data fetching (Tavily)
│   ├── api/
│   │   └── routes.py            ← API endpoints
│   ├── models/
│   │   └── decision.py          ← Pydantic data models
│   ├── database.py              ← SQLite setup
│   ├── config.py                ← Secure settings loader
│   └── main.py                  ← FastAPI entry point
└── frontend/
    ├── app/
    │   ├── page.tsx             ← Landing page
    │   ├── analyze/page.tsx     ← 4-step guided form
    │   ├── chat/page.tsx        ← Quick mode (natural language)
    │   └── result/page.tsx      ← Analysis results
    └── components/ui/           ← shadcn/ui components
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Free API keys: [Groq](https://console.groq.com) + [Tavily](https://tavily.com)

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Fill in your API keys in .env

uvicorn main:app --reload
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Running at http://localhost:3000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Structured decision analysis |
| `POST` | `/api/chat` | Natural language decision analysis |
| `GET` | `/api/history` | Past decisions |
| `GET` | `/api/stats/biases` | Bias detection statistics |
| `GET` | `/api/health` | Health check |

Full interactive docs at `http://localhost:8000/docs`

---

## Research References

1. Kahneman, D. & Tversky, A. (1979) — *Prospect Theory: An Analysis of Decision Under Risk* — Econometrica, 47(2)
2. Tversky, A. & Kahneman, D. (1992) — *Advances in Prospect Theory* — Journal of Risk and Uncertainty, 5(4)
3. Schwartz, S.H. (1992) — *Universals in the Content and Structure of Values* — Advances in Experimental Social Psychology, 25
4. Lerner, J.S. et al. (2015) — *Emotion and Decision Making* — Annual Review of Psychology, 66
5. Arkes, H.R. & Blumer, C. (1985) — *The Psychology of Sunk Cost* — OBHDP, 35(1)
6. Samuelson, W. & Zeckhauser, R. (1988) — *Status Quo Bias in Decision Making* — Journal of Risk and Uncertainty, 1(1)
7. Klein, G. (2007) — *Performing a Project Premortem* — Harvard Business Review
8. Evans, J.S.B.T. & Stanovich, K.E. (2013) — *Dual-Process Theories of Higher Cognition* — Perspectives on Psychological Science
9. Ruggeri, K. et al. (2020) — *Replicating patterns of prospect theory* — Nature Human Behaviour, 4
10. Ramos, E.C., Campos, M.L.M. & Baião, F.A. (2024) — *ABI: Automatic Bias Identification* — arXiv:2405.14067

---

## Open Source Credits

- **shadcn/ui** — MIT License — [ui.shadcn.com](https://ui.shadcn.com)
- **Next.js** — MIT License — [nextjs.org](https://nextjs.org)
- **FastAPI** — MIT License — [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Tailwind CSS** — MIT License — [tailwindcss.com](https://tailwindcss.com)
- **Llama 3.3** — Meta Llama License — [Meta AI](https://ai.meta.com)

---


