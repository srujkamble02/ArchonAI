# Archon AI — Setup & Run Guide

## Project Structure

```
archon_ai/
├── backend/
│   ├── main.py                         ← FastAPI app (entry point)
│   ├── requirements.txt
│   └── modules/
│       ├── feature_extractor.py        ← Step 1: Rule-based NLP
│       ├── architecture_engine.py      ← Step 2: Architecture decision
│       ├── graph_builder.py            ← Step 3: NetworkX graph
│       ├── cost_engine.py              ← Step 4: Cost computation
│       ├── failure_engine.py           ← Step 5: Failure simulation
│       ├── diagram_generator.py        ← Step 6: SVG + Mermaid
│       └── llm_explainer.py            ← Step 7: Claude explanation
└── frontend/
    └── index.html                      ← Full UI (no build step needed)
```

---

## Backend Setup

### 1. Install Python 3.10+

```bash
python3 --version   # should be 3.10+
```

### 2. Create virtual environment

```bash
cd archon_ai/backend
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
# OR: venv\Scripts\activate   # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Set Anthropic API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or enter it directly in the frontend UI — no env var needed.

### 5. Run the backend

```bash
uvicorn main:app --reload --port 8000
```

Backend is now live at: http://localhost:8000

API docs at: http://localhost:8000/docs

---

## Frontend Setup

No build step. Just open `frontend/index.html` in any browser.

```bash
# Option 1: Open directly
open archon_ai/frontend/index.html

# Option 2: Serve with Python
cd archon_ai/frontend
python3 -m http.server 3000
# Open: http://localhost:3000
```

Make sure Backend URL in the sidebar is set to: `http://localhost:8000`

---

## Test the API directly

```bash
curl -X POST http://localhost:8000/generate-architecture \
  -H "Content-Type: application/json" \
  -d '{
    "project_description": "Build a food delivery app like Swiggy with real-time GPS, payments, 1M users",
    "cloud_provider": "AWS",
    "anthropic_api_key": "sk-ant-..."
  }'
```

---

## Module Responsibilities (for viva)

| Module | Role | Uses LLM? |
|--------|------|-----------|
| feature_extractor.py | Keyword-based NLP — extracts scale, real-time, payments, AI, IoT flags | NO |
| architecture_engine.py | Rule-based decision engine — picks Microservices / Serverless / Monolithic | NO |
| graph_builder.py | Builds directed graph with NetworkX — nodes=services, edges=protocols | NO |
| cost_engine.py | Computes AWS cost from formulas — EC2, RDS, S3, Kafka, etc. | NO |
| failure_engine.py | Simulates failures with thresholds — DB overload, traffic spike, crash | NO |
| diagram_generator.py | Generates SVG + Mermaid from graph data dynamically | NO |
| llm_explainer.py | Sends structured output to Claude for human-readable explanation | YES |

---

## Architecture Decision Rules

```
scale > 1,000,000 + real_time  → Event-Driven Microservices
scale > 100,000                → Microservices
iot = true                     → Edge-Driven IoT Architecture
ai + scale > 20,000            → AI-Augmented Microservices
scale < 20,000 + no real_time  → Monolithic
scale < 50,000 + real_time     → Serverless Event-Driven
else                           → Hybrid (Modular Monolith)
```

---

## Requirements

```
fastapi==0.110.0
uvicorn[standard]==0.29.0
pydantic==2.6.4
httpx==0.27.0
networkx==3.3
python-dotenv==1.0.1
```
