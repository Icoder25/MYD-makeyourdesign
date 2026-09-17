# KOHLER AI BathPlan — Project State

## Project
KOHLER MIT-WPU AI Research Lab — Track 1

## Deadline
September 20, 2026 — 11:59 PM IST

## Time Constraint
~48 hours from project start

## Product
KOHLER AI BathPlan

## Product Thesis
An AI bathroom planning agent that transforms bathroom space,
budget, preferences and priorities into feasible, explainable,
sustainability-aware KOHLER configurations.

## Core Differentiator
Constraint-aware planning and trade-off resolution.

## Locked MVP
- Bathroom image upload
- Manual dimensions
- Budget
- Style/preferences
- Vision-assisted room understanding
- Curated KOHLER product catalog
- Deterministic constraint engine
- Recommendation engine
- Budget validation
- Trade-off/conflict resolution
- Water-impact estimation
- 2D bathroom visualization
- Explainable recommendations

## Explicitly NOT Building
- Full CAD
- AR
- Voice interface
- Custom CV model training
- Huge catalog
- Production e-commerce
- Complex 3D engine
- Microservices

## Team
Human: Product Owner + Integrator
ChatGPT: Research + Strategy + Architecture + Critic
Claude: Lead Developer
Gemini: Vision + Multimodal QA

## Current Phase
0 — Product Freeze

## Current Blockers
None

## Decisions
- Bathroom Vision is an advisory evidence module only; manual dimensions and deterministic constraints remain authoritative.
- Vision output is validated against `backend/vision/models.py` and cannot provide dimensions, clearances, plumbing, rough-ins, structural constraints, or installation feasibility.
- Gemini structured JSON is isolated behind `backend/vision/provider.py`.
- Constraint validation is pure Python with no LLM dependency; unknown inputs return `verification_required` and never pass.

## Change Log
- Project initialized
- Bathroom Vision module implemented with structured Gemini adapter, image preprocessing, isolated API route, and focused safety tests.
- Deterministic constraint engine implemented with structured checks and catalog-backed unit tests.
- Deterministic recommendation and configuration-ranking layer implemented (`backend/recommendation/`): candidate retrieval, hard-constraint filtering via the constraint engine, configurable weighted scoring (spatial, budget, preference, water efficiency, style, smart-feature), structured `NO_FULLY_COMPLIANT_CONFIGURATION` handling with violations/closest-alternatives/relaxations, and a rule-based trade-off engine (`propose_budget_reduction`). No LLM dependency.
