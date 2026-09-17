# KOHLER AI BathPlan

KOHLER MIT-WPU AI Research Lab — Track 1.

KOHLER AI BathPlan transforms bathroom space, budget, preferences, and priorities into feasible, explainable, sustainability-aware KOHLER configurations.

## Project Structure

- `frontend/` — user-facing bathroom planning experience
- `backend/` — planning, constraints, recommendations, and vision integration
- `catalog/` — curated KOHLER product data
- `tests/` — automated tests
- `docs/` — project documentation
- `sample-data/` — development fixtures and example inputs
- `screenshots/` — product screenshots and QA captures

See [PROJECT_STATE.md](PROJECT_STATE.md) for the locked MVP and current project decisions.

## Bathroom Vision

The backend vision module is exposed at `POST /api/v1/project/{project_id}/vision`.
It accepts a multipart image upload and returns the `BathroomVisionEvidence` contract
defined in `backend/vision/models.py`. Gemini is requested in structured JSON mode;
the analyzer then validates the result, removes EXIF orientation ambiguity, limits
the image to 1536px, and recomputes `overall_confidence`.

Vision evidence is advisory only. `authoritative` is hardcoded to `false`, and the
module has no path into dimensions, clearances, plumbing, rough-ins, structural
constraints, or installation feasibility. Manual measurements and deterministic
constraint checks remain the source of truth.

Run the backend locally with:

```text
uvicorn backend.main:app --reload
```

Set `GEMINI_API_KEY` before making vision requests. The application can still start
without that key so the rest of the planning service is not blocked.

## Deterministic Constraint Engine

The pure-Python engine is available from `backend/constraints` and has no LLM
dependency. Its public checks are `fits_room`, `fits_fixture_zone`,
`within_budget`, `check_required_categories`, `check_compatibility`,
`check_power_requirement`, `check_installation`, and `validate_configuration`.

Every check returns structured status and reasoning. Missing dimensions, unknown
rough-ins, undocumented compatibility, unknown prices, and unconfirmed electrical
availability return `verification_required`; they never become a pass. Installation
warnings are retained as non-blocking warnings only when no hard verification is
needed.
