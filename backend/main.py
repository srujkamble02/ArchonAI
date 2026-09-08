"""
main.py — Archon AI Backend
FastAPI application exposing the full architecture generation pipeline.
"""

import os
import time
import traceback
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from modules.feature_extractor import extract_features
from modules.architecture_engine import decide_architecture
from modules.graph_builder import build_graph
from modules.cost_engine import estimate_cost
from modules.failure_engine import simulate_failures
from modules.diagram_generator import generate_diagrams
from modules.llm_explainer import generate_explanation
from modules.jenkins_engine import generate_jenkins_pipeline
from modules.workforce_engine import calculate_workforce_cost, calculate_total_cost
from modules.recommendation_engine import generate_recommendations


# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Archon AI — Architecture Generation API",
    description="AI-driven platform for automated software architecture, cloud planning, and pipeline generation.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────
class WorkforceRole(BaseModel):
    role: str = "Software Developers"
    count: int = 0
    wage: float = 0
    period: str = "monthly"   # hourly | daily | monthly | yearly

class ArchitectureRequest(BaseModel):
    project_description: str
    anthropic_api_key:   Optional[str] = None
    cloud_provider:      Optional[str] = "AWS"
    scale_override:      Optional[str] = None   # "startup"|"mid"|"large"|"enterprise"
    workforce_config:    Optional[List[WorkforceRole]] = None
    workforce_currency:  Optional[str] = "INR"


class HealthResponse(BaseModel):
    status: str
    version: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_model=HealthResponse)
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/generate-architecture")
async def generate_architecture(req: ArchitectureRequest):
    start = time.time()

    if not req.project_description or len(req.project_description.strip()) < 10:
        raise HTTPException(status_code=400, detail="project_description must be at least 10 characters.")

    try:
        # ── STEP 1: Feature Extraction ────────────────────────────────────
        features = extract_features(req.project_description)

        # Apply scale override if provided
        if req.scale_override:
            scale_map = {"startup": 5_000, "mid": 50_000, "large": 500_000, "enterprise": 2_000_000}
            if req.scale_override in scale_map:
                features["scale"] = scale_map[req.scale_override]
                features["scale_label"] = req.scale_override

        # ── STEP 2: Architecture Decision (rule-based) ────────────────────
        architecture = decide_architecture(features)

        # ── STEP 3: Graph Construction ────────────────────────────────────
        graph = build_graph(architecture, features)

        # ── STEP 4: Cost Estimation ───────────────────────────────────────
        cost = estimate_cost(features, architecture)

        # ── STEP 5: Failure Simulation ────────────────────────────────────
        failures = simulate_failures(features, architecture, cost)

        # ── STEP 6: Diagram Generation ────────────────────────────────────
        diagrams = generate_diagrams(graph, architecture, features)

        # ── STEP 7: Jenkins CI/CD Pipeline ────────────────────────────────
        jenkins = generate_jenkins_pipeline(features, architecture, req.cloud_provider or "AWS")

        # ── STEP 8: Workforce Cost Calculation ────────────────────────────
        wf_config = [r.model_dump() for r in req.workforce_config] if req.workforce_config else []
        workforce_cost = calculate_workforce_cost(wf_config, req.workforce_currency or "INR")
        total_cost = calculate_total_cost(cost, workforce_cost)

        # ── STEP 9: Multi-Option Recommendations ─────────────────────────
        recommendations = generate_recommendations(features, architecture, req.cloud_provider or "AWS")

        # ── STEP 10: LLM Explanation (optional, needs API key) ────────────
        api_key = req.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        explanation = await generate_explanation(features, architecture, cost, failures, api_key)

        # ── STEP 11: Assemble final response ──────────────────────────────
        elapsed = round(time.time() - start, 3)

        return {
            "success":     True,
            "elapsed_ms":  int(elapsed * 1000),
            # ── Raw user inputs (for full report traceability) ──
            "input": {
                "project_description": req.project_description,
                "cloud_provider":      req.cloud_provider or "AWS",
                "scale_override":      req.scale_override or "Auto-detect",
                "anthropic_key_used":  bool(api_key),
            },
            "features":         features,
            "architecture":     architecture,
            "graph":            graph,
            "cost":             cost,
            "failures":         failures,
            "diagrams":         diagrams,
            "explanation":      explanation,
            "cloud_provider":   req.cloud_provider,
            "jenkins_pipeline": jenkins,
            "workforce_cost":   workforce_cost,
            "total_cost":       total_cost,
            "recommendations":  recommendations,
            "pipeline": {
                "steps": [
                    "Feature Extraction",
                    "Architecture Decision (rule-based)",
                    "Graph Construction",
                    "Cost Estimation",
                    "Failure Simulation",
                    "Diagram Generation",
                    "Jenkins CI/CD Pipeline Generation",
                    "Workforce Cost Calculation",
                    "Multi-Option Recommendations",
                    "LLM Explanation",
                ],
                "ai_used_for": "explanation only — all architecture decisions are rule-based",
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/explain-only")
async def explain_only(req: ArchitectureRequest):
    """Lightweight endpoint — just runs steps 1-2 and returns text explanation."""
    features     = extract_features(req.project_description)
    architecture = decide_architecture(features)
    cost         = estimate_cost(features, architecture)
    failures     = simulate_failures(features, architecture, cost)
    api_key      = req.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    explanation  = await generate_explanation(features, architecture, cost, failures, api_key)
    return {"explanation": explanation, "architecture_type": architecture["architecture"]}
