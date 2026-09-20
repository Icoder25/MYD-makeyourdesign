> **Historical document — pre-implementation design record.**
>
> This was written before any code existed and describes a system that was
> *planned*. Parts of it were not built as specified: the frontend is Vite +
> React rather than Next.js, the agent does not use LLM function-calling (intent
> extraction is a single structured call with a deterministic fallback), and the
> endpoint set differs. DesignPulse, versioning, decision memory and export are
> not in here at all — they came later.
>
> It is kept because the decisions and the reasoning behind them are worth
> reading. For the architecture as built, see **[architecture.md](architecture.md)**.

---

# KOHLER AI BathPlan — Implementation Architecture

**Phase:** Architecture only. No application code in this document.
**Scope constraint applied:** MVP = product-spec.md Section 6 (P0) only. P1 (2D viz, image input, rendering) treated as stretch, not load-bearing.

---

## 0. Assumptions this architecture depends on — verify these first

Architecture decisions below assume the following are true. If any are false, parts of this document need to change before you start building, not after.

1. **Runway is ~72 hours, not 48** (see chat message). If it's actually 48, cut P1 entirely and cut the multi-objective optimizer (innovation-gap.md #9) down to a single weighted formula with 3 preset weight vectors — don't build a general optimizer.
2. **The product catalog will exist as static, hand-curated JSON before the constraint engine is built.** If catalog curation slips past Hour 10, everything downstream slips with it. This is the single highest-risk dependency in the whole project and it's manual data entry work, not engineering — treat it as the critical path, not a side task.
3. **No live KOHLER API exists.** Confirmed by kohler-current-state.md and product-spec.md Section 8. This architecture assumes zero external product data integration.
4. **"Vision-assisted room understanding" is decorative, not load-bearing.** product-spec.md P1.2 explicitly says the image must not be an authoritative measurement source. That means the vision model's output is *context*, not *input to the validator*. Architecture below reflects that — vision results never reach the constraint engine directly.

---

## 1. System Architecture

Three-tier, single-repo, monolithic backend. Not microservices — there's no scale requirement and splitting services would burn hours on deployment plumbing instead of the constraint engine, which is the actual product.

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js + TypeScript)                             │
│  - Intake form  - Plan cards  - Trade-off view  - Chat panel │
└───────────────────────────┬───────────────────────────────────┘
                             │ HTTPS / JSON
┌───────────────────────────▼───────────────────────────────────┐
│  BACKEND (FastAPI, single process)                            │
│                                                                 │
│  ┌───────────────┐   ┌──────────────────┐                     │
│  │ Agent/Orchestr.│──▶│ Intent Parser (LLM)│                  │
│  │ (LLM, tool-use)│   └──────────────────┘                     │
│  └───────┬────────┘                                            │
│          │ calls tools (function calling), never computes      │
│          │ dimensions/prices/feasibility itself                │
│          ▼                                                     │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Product Catalog │  │ Constraint Engine │  │ Recommendation │ │
│  │ (read-only data)│─▶│ (deterministic)   │─▶│ Engine (scoring)│ │
│  └────────────────┘  └──────────────────┘  └────────┬───────┘ │
│                                                        │         │
│                                              ┌─────────▼──────┐ │
│                                              │ Sustainability  │ │
│                                              │ Calculator      │ │
│                                              └─────────┬──────┘ │
│                                                        │         │
│                                              ┌─────────▼──────┐ │
│                                              │ Explanation Gen │ │
│                                              │ (LLM, reads     │ │
│                                              │  rejection codes│ │
│                                              │  — never invents│ │
│                                              │  reasons)       │ │
│                                              └─────────────────┘ │
│                                                                  │
│  ┌────────────────┐  (P1 only, optional)                       │
│  │ Vision Module   │  produces context tags, not measurements   │
│  └────────────────┘                                             │
└──────────────────────────┬──────────────────────────────────────┘
                            │
                  ┌─────────▼─────────┐
                  │ Data layer         │
                  │ catalog.json /     │
                  │ SQLite             │
                  └────────────────────┘
```

**Key boundary, stated explicitly because it's the whole product thesis:** the Agent/Orchestrator can only reach the Constraint Engine, Recommendation Engine, and Sustainability Calculator through defined tool calls with typed inputs/outputs. It cannot write directly into the response the user sees for any numeric, price, or feasibility claim. Every number in the final output must trace back to a non-LLM function call. This is enforced by *not giving the LLM a way to emit those fields freely* — the response schema separates "LLM-authored text" fields from "system-computed" fields, and the API layer populates the latter itself, ignoring anything the LLM might have said about them.

---

## 2. Module Boundaries

| Module | Owns | Must never do |
|---|---|---|
| `catalog/` | Product data access, filtering, lookup by ID | Compute feasibility, prices, or scores |
| `constraints/` | Hard-rule evaluation (spatial, budget, must-have) | Explain *why* in natural language, rank options |
| `recommendation/` | Deterministic scoring/ranking of already-valid candidates | Validate feasibility (that's constraints' job), invent candidates outside the catalog |
| `sustainability/` | Water-use math from documented formulas | Present manufacturer "up to" claims as guaranteed results |
| `agent/` | LLM prompting, tool-call orchestration, structured requirement extraction, natural-language explanation of system-provided facts | Compute anything numeric; invent product IDs, prices, or rejection reasons not returned by `constraints/` |
| `vision/` (P1) | Image → style/context tags | Feed measurements into `constraints/` |
| `api/` | Request validation, response assembly, error envelopes | Contain business logic |

This table is the actual enforcement mechanism — if a module violates its "must never" column, that's a code review failure, not a runtime check, because there's no time to build a governance layer. Flagging this as a real risk in Section C below.

---

## 3. API Endpoints

Minimal surface. No REST purism for its own sake — a handful of task-shaped endpoints, not one per resource.

```
POST /api/v1/project                  # create a project from intake form
GET  /api/v1/project/{id}             # fetch current state
POST /api/v1/project/{id}/parse       # NL text -> structured requirements (LLM)
POST /api/v1/project/{id}/recommend   # requirements -> 3 validated options
POST /api/v1/project/{id}/modify      # conversational modification -> re-optimize -> re-validate
GET  /api/v1/project/{id}/plan/{plan_id}   # full detail for one option
POST /api/v1/project/{id}/vision      # (P1) image upload -> context tags only
GET  /api/v1/catalog                  # debug/dev: list curated products
GET  /api/v1/health
```

No auth, no multi-user concerns — out of scope per product-spec.md Section 8, and correctly so. Don't add it.

---

## 4. Request/Response Schema — conventions

Every response follows:

```json
{
  "ok": true,
  "data": { ... },
  "meta": {
    "confidence_notes": ["..."],
    "computed_by": "constraint_engine | recommendation_engine | sustainability_calculator | llm"
  }
}
```

Error responses (Section 12) use a separate shape, never a 200 with `"ok": false` buried in a 200 status — use real HTTP status codes so the frontend doesn't need to parse body content to know if something failed.

The `computed_by` field on every numeric claim is not cosmetic — it's the thing you point to when a judge asks "how do I know the LLM didn't make this up." Keep it.

---

## 5. Product Schema

Adopting kohler-current-state.md's proposed model directly — it's already well-specified, no changes needed except making `confidence` mandatory rather than optional, since research.md's data integrity rules require it on every field, not just the record.

```json
{
  "id": "kohler_vanity_001",
  "name": "string",
  "category": "toilet|smart_toilet|faucet|shower_system|digital_shower|vanity|sink|bathtub|accessory",
  "collection": "string",
  "market": "US",
  "currency": "USD",
  "price": 0,
  "last_verified": "YYYY-MM-DD",
  "dimensions": { "width_in": 0, "depth_in": 0, "height_in": 0 },
  "installation": { "type": "string|null", "rough_in": "string|null" },
  "style": ["modern", "minimalist"],
  "finish": ["string"],
  "water": {
    "flow_rate_gpm": null,
    "flush_volume_gal": null,
    "watersense_certified": "true|false|unknown",
    "manufacturer_efficiency_claim": {
      "type": "up_to|null",
      "value": null,
      "comparison": "string|null",
      "source_url": "string|null"
    }
  },
  "smart": { "features": [], "konnect_compatible": "true|false|unknown" },
  "compatibility_group": ["string"],
  "sustainability_attributes": ["string"],
  "source_url": "string",
  "confidence": "verified|assumed|unknown"
}
```

**Note that's easy to miss:** "compatibility_group" is a string list, not a graph. kohler-current-state.md warns against inferring arbitrary compatibility. For the MVP, treat compatibility as "same group = compatible," full stop — no partial-compatibility logic, no LLM judgment calls on it. If two products don't share a group tag, they're `unknown`, not `incompatible` — matches the three-state confidence model used everywhere else.

---

## 6. Bathroom-State Schema

This is the structured requirement object the agent produces and the whole system operates on downstream.

```json
{
  "project_id": "string",
  "space": {
    "length_ft": 0,
    "width_ft": 0,
    "ceiling_height_ft": null,
    "door_location": "string|unknown",
    "window_location": "string|unknown",
    "existing_fixtures": [
      { "type": "string", "location": "string", "fixed": true }
    ]
  },
  "budget": { "max": 0, "currency": "INR" },
  "style": ["modern_minimalist"],
  "must_have": ["walk_in_shower"],
  "priorities": {
    "storage": 0.0,
    "water_efficiency": 0.0,
    "style": 0.0,
    "budget": 0.0
  },
  "confidence_flags": {
    "space": "verified|assumed|unknown",
    "existing_fixtures": "verified|assumed|unknown"
  },
  "version": 1
}
```

`version` matters — every `/modify` call produces a new version, and the "what changed" engine (innovation-gap.md #12) diffs `version N` against `version N-1`. Without versioning you have to reconstruct history from logs, which is slower to build and easier to get wrong during a live demo.

---

## 7. Recommendation / Plan Schema

```json
{
  "plan_id": "string",
  "objective": "budget_first|balanced|water_first",
  "products": [ { "product_id": "string", "role": "vanity|toilet|..." } ],
  "total_cost": 0,
  "currency": "INR",
  "fit_score": 0.0,
  "score_breakdown": {
    "style_match": 0.0,
    "budget_fit": 0.0,
    "space_fit": 0.0,
    "sustainability_fit": 0.0,
    "preference_match": 0.0
  },
  "constraint_status": "valid|invalid",
  "constraint_results": [ /* see Section 8 */ ],
  "water_impact": { /* see Section 9 */ },
  "trade_offs": [
    { "dimension": "storage_vs_circulation", "description": "string", "computed_by": "recommendation_engine" }
  ],
  "explanation": "string (LLM-authored, reads score_breakdown + trade_offs, does not alter numbers)",
  "assumptions": ["string"]
}
```

`score_breakdown` is exposed, not hidden — product-spec.md 6.5 requires an auditable formula, and the constraint-heatmap / "why rejected" ideas (innovation-gap.md #6, #10) only work if the breakdown is inspectable rather than a single opaque number.

---

## 8. Constraint Schema

```json
{
  "rule_id": "WALL_WIDTH_EXCEEDED",
  "severity": "hard|soft",
  "status": "pass|fail",
  "subject": { "product_id": "string", "field": "width_in" },
  "expected": "<= available_wall_width",
  "actual": 0,
  "limit": 0
}
```

Fixed rule-code enum, matching innovation-gap.md #6 exactly:

```
WALL_WIDTH_EXCEEDED
DEPTH_EXCEEDED
CLEARANCE_VIOLATION
BUDGET_EXCEEDED
MISSING_MUST_HAVE
INSTALLATION_UNKNOWN
COMPATIBILITY_UNKNOWN
```

The LLM is only ever allowed to translate a `rule_id` + its structured fields into a sentence. It never generates a `rule_id`, never decides `pass`/`fail`. This is the actual implementation of the "impossible-request detection" demo moment — worth building and testing before anything else, because it's the single highest-impact 60 seconds of the judge demo per innovation-gap.md's own scripted walkthrough.

---

## 9. Water-Impact Schema

```json
{
  "baseline": { "annual_gallons": 0, "assumptions": ["string"] },
  "configuration": { "annual_gallons": 0, "assumptions": ["string"] },
  "delta": { "gallons": 0, "percent": 0.0 },
  "manufacturer_claims_used": [
    { "product_id": "string", "claim_type": "up_to", "value": 0.80, "comparison": "standard shower system", "source_url": "string" }
  ],
  "disclaimer": "Actual household water use depends on usage patterns and is not guaranteed."
}
```

Formulas locked to product-spec.md Section 13 exactly — no deviation, since those are the only formulas anyone has fact-checked against the source docs. Toilets and showers only for MVP; don't try to model faucet/vanity water use unless catalog data actually supports it, per kohler-current-state.md's "unknown stays unknown" rule.

---

## 10. Vision-Result Schema (P1 — build last, cut first if time is short)

```json
{
  "detected_style_tags": ["string"],
  "detected_fixture_hints": [ { "type": "string", "confidence": "low|medium|high" } ],
  "authoritative": false,
  "note": "Image-derived hints are contextual only and are not used for dimension validation."
}
```

`authoritative: false` is hardcoded, not model output — never let the vision model or its prompt claim otherwise. This schema deliberately has no field the constraint engine could accidentally consume, because product-spec.md P1.2 forbids it and the easiest way to enforce that is to make it structurally impossible, not policy-dependent.

---

## 11. Agent Tool Definitions

The orchestrator gets a fixed, small tool list — not open-ended function calling against the whole codebase.

```
parse_requirements(raw_text: str) -> BathroomState
  # LLM-only; produces structured data, calls nothing else

retrieve_candidates(state: BathroomState) -> list[ProductID]
  # deterministic filter over catalog, no LLM

validate_configuration(products: list[ProductID], state: BathroomState) -> list[ConstraintResult]
  # deterministic, pure function

score_configuration(products, state, weights) -> ScoreBreakdown
  # deterministic

calculate_water_impact(products, state) -> WaterImpact
  # deterministic

explain(rejection_codes | trade_offs | score_breakdown) -> str
  # LLM-only; reads structured data, produces text, cannot alter input data

diff_versions(state_v1, state_v2, plan_v1, plan_v2) -> ChangeSummary
  # deterministic
```

The agent orchestrator's only real judgment calls are: (1) deciding when required intake fields are missing and asking the user, and (2) deciding which of the three weight-vector presets a conversational modification implies (e.g., "make it cheaper" → shift weight toward `budget_fit`). Everything else is a straight pipeline call. Keep the LLM's decision space that narrow — every additional LLM judgment call is a new hallucination surface and a new thing to test adversarially in Hours 40–44.

---

## 12. Error-Handling Strategy

| Failure | Handling |
|---|---|
| No valid configuration exists | Return `"no_feasible_solution": true` with the specific `constraint_results` that eliminated every candidate. This is a *product feature* per product-spec.md's acceptance criteria — never silently degrade to "closest match" unless the user explicitly asks for one. |
| LLM parse fails / returns malformed JSON | Backend validates against `BathroomState` schema server-side (Pydantic). On failure, re-prompt once with the validation error, then fall back to asking the user directly — never pass unvalidated LLM output downstream. |
| LLM invents a product_id not in the catalog | Reject at the `retrieve_candidates`/`validate_configuration` boundary — any ID not in the catalog is a hard error, not silently dropped, so it surfaces in testing rather than in front of a judge. |
| Catalog data missing a field the validator needs | Treat as `unknown`, which is itself a valid constraint outcome (`INSTALLATION_UNKNOWN`, etc.) — never default to an assumed-safe value. |
| Vision module fails/times out (P1) | Degrade silently — image context is decorative; a failure there should never block the rest of the flow. |
| Timeout on LLM calls | 10–15s timeout, single retry, then explicit "explanation unavailable, here is the raw constraint data" fallback — the deterministic result must still reach the user even if the LLM layer is down. |

---

## 13. Test Architecture

Given the acceptance criteria in product-spec.md Section 16, tests should skew heavily toward the constraint engine and adversarial input — that's what's actually graded, not UI polish.

```
tests/
├── unit/
│   ├── test_constraints_spatial.py      # every rule_id, both pass and fail cases
│   ├── test_constraints_budget.py
│   ├── test_recommendation_scoring.py   # verify formula, not just "runs without error"
│   └── test_water_calculator.py         # verify against hand-computed values
├── integration/
│   ├── test_full_pipeline_happy_path.py
│   ├── test_conversational_modify.py    # verify hard constraints survive re-optimization
│   └── test_versioning_diff.py
└── adversarial/
    ├── test_impossible_dimensions.py    # the demo's core moment — must not hallucinate
    ├── test_llm_invents_product_id.py   # simulate malformed LLM output, verify rejection
    ├── test_budget_zero_or_negative.py
    └── test_conflicting_must_haves.py   # e.g. must-have exceeds every catalog option
```

The adversarial suite is not optional polish — it's what Hours 40–44 in product-spec.md's own schedule are for, and it directly maps to acceptance criteria items you've already committed to ("deliberately impossible request produces no feasible solution rather than a hallucinated design").

---

## 14. Environment Configuration

```
# .env (backend)
LLM_API_KEY=
LLM_MODEL=                  # pin an exact model string, don't leave it implicit
VISION_MODEL=               # P1 only
DATABASE_URL=sqlite:///./bathplan.db   # or postgres:// if already available
CATALOG_PATH=./products/kohler_products.json
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000

# .env.local (frontend)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Keep the catalog as a file path config, not hardcoded — you will edit that JSON file dozens of times over the build window and don't want a redeploy cycle attached to a data fix.

---

## 15. Folder Structure

Matches product-spec.md Section 10 almost exactly — no reason to deviate from a structure that's already been thought through, with two additions (`agent/tools.py` split out, `tests/adversarial/`).

```
bathplan/
├── frontend/
│   ├── app/
│   │   ├── intake/
│   │   ├── plans/
│   │   └── chat/
│   ├── components/
│   ├── lib/api.ts
│   └── types/            # mirror backend Pydantic schemas by hand or codegen
├── backend/
│   ├── api/
│   │   └── routes.py
│   ├── schemas/
│   │   ├── product.py
│   │   ├── bathroom_state.py
│   │   ├── plan.py
│   │   ├── constraint.py
│   │   └── water_impact.py
│   ├── products/
│   │   └── kohler_products.json
│   ├── constraints/
│   │   ├── spatial.py
│   │   ├── budget.py
│   │   └── requirements.py
│   ├── recommendation/
│   │   └── engine.py
│   ├── sustainability/
│   │   └── calculator.py
│   ├── vision/            # P1
│   │   └── analyzer.py
│   ├── agent/
│   │   ├── orchestrator.py
│   │   ├── tools.py
│   │   └── prompts.py
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── adversarial/
├── .env.example
└── README.md
```

---

## 16. Deployment Approach

No production deployment requirement stated anywhere in the source docs — this is a judged demo, not a shipped product. Over-building deployment infrastructure here is wasted hours.

- **Backend:** run locally via `uvicorn`, or a single free-tier container (Render/Railway/Fly) if a public demo URL is genuinely needed for the submission format. Confirm this requirement before spending time on it — if the demo is live/in-person, skip hosting entirely.
- **Frontend:** `next dev` locally, or Vercel free tier if a public URL is required.
- **Database:** SQLite file, checked into the repo or generated at startup from `kohler_products.json`. Do not stand up Postgres unless you already have a reason to — the spec explicitly says JSON/SQLite is sufficient.
- **No CI/CD pipeline** — not worth the setup time for a 3-day competition build. Run tests manually before each milestone.

---

## 17. Local Development Instructions

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn pydantic openai  # or anthropic SDK, per LLM choice
cp .env.example .env   # fill in LLM_API_KEY
uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

---

# A. Architecture Diagram

See Section 1. One diagram, not repeated here.

# B. Critical Decisions

1. **Monolith, single process, no microservices.** Justified purely by time constraint — there is no scale requirement anywhere in the source docs that would justify splitting services.
2. **LLM output never reaches the user unvalidated.** Enforced structurally via schema separation (LLM-authored text fields vs. system-computed fields), not by prompt instructions alone. Prompt-only enforcement is not reliable enough for a judged demo where someone might specifically probe for hallucination.
3. **Fixed, small rule-code enum for rejections**, not free-text reasons. This is what makes "why rejected" (innovation-gap.md #6) both buildable in the time available and actually inspectable by a judge, rather than another opaque LLM paragraph.
4. **Vision module structurally prevented from feeding the validator.** Given product-spec.md's own P1.2 warning, treating this as a schema-level constraint rather than a coding convention removes an entire class of "did we accidentally let the vision hint count as fact" bugs.
5. **Versioned bathroom state**, not mutation-in-place. Required for the "what changed" engine and for the conversational re-optimization demo moment to be reliably reproducible live.
6. **Catalog curation treated as the critical path**, not a background task. This is the one item on this list that isn't really an "architecture" decision — it's a scheduling call, but it's the one most likely to sink the whole build if under-prioritized, so it's stated here explicitly rather than buried in Section 15 of the 48-hour plan.

# C. What Could Fail

Ranked by likelihood, not severity — some of these are near-certain given a solo 3-day build.

1. **Catalog curation takes longer than budgeted.** 30–80 products with verified dimensions, prices, source URLs, and confidence tags is real research work, not a data-entry afternoon. If this slips, everything downstream slips — this is the most probable failure mode, not a hypothetical one.
2. **The "must never" boundaries in Section 2 get violated under time pressure.** There's no automated enforcement described here beyond code review discipline (a solo developer reviewing their own code under deadline pressure is a weak control). If you're tempted to let the LLM "just fill in a plausible price" when catalog data is missing a field, that's the exact failure the whole architecture exists to prevent — and it's also the easiest shortcut to take at Hour 30.
3. **The scoring formula in Section 7 is underspecified.** product-spec.md itself says "weights should be configurable" without specifying them. If you don't lock actual numeric weights early, "fit_score" is not auditable in practice even though the schema exposes a breakdown — an inspectable formula with arbitrary, unjustified weights is not meaningfully more defensible than an LLM score, just differently opaque. Decide and document the weights before Hour 17.
4. **Conversational modification breaking hard constraints.** The re-optimization path (Section 11, `explain` + weight-shift logic) is the part of the system most likely to have an edge case where a soft-constraint change accidentally lets a hard constraint slip through revalidation. This needs its own adversarial test, not just the happy-path integration test.
5. **Vision module (P1) eating time that P0 needs.** Given it's explicitly non-authoritative and cosmetic, any hour spent on it before P0's constraint engine and adversarial tests are solid is a bad trade. This is the first thing to cut if the (corrected) 72-hour or original 48-hour budget is tight.
6. **Demo script fragility.** The scripted judge demo in innovation-gap.md depends on specific numbers (₹1.98L → ₹1.69L) that only work if the catalog and constraint weights happen to produce that exact narrative arc. Don't assume the demo script's numbers will just fall out of the real system — validate the actual demo scenario against the actual built system well before the deadline, not as a last-minute check.

# D. Implementation Order

Revised from product-spec.md Section 15 to reflect the dependency chain actually described above — catalog and constraint engine first, agent layer later, vision last.

1. **Product schema + catalog curation** (Section 5) — start immediately, treat as ongoing background work throughout, not a single blocked phase.
2. **Bathroom-state schema + constraint engine** (Sections 6, 8) — build and unit-test every `rule_id` against hand-written fixture data before any product data is even fully curated, so the engine isn't blocked on catalog completion.
3. **Recommendation engine with locked scoring weights** (Section 7) — decide the weights, don't leave them abstract.
4. **Sustainability calculator** (Section 9) — isolated, testable independently.
5. **Adversarial tests for 2–4** — write these *before* the agent layer exists, so the deterministic core is proven solid before an LLM sits in front of it.
6. **Agent orchestrator + tool calling** (Section 11) — wire the LLM to the now-tested deterministic pipeline.
7. **API layer + error handling** (Sections 3, 12).
8. **Frontend: intake → plan cards → trade-off view.**
9. **Conversational modification end-to-end**, including the hard-constraint-survival adversarial test.
10. **Demo scenario validation against the real system** — run the actual scripted judge demo end-to-end and fix whatever doesn't match the narrative.
11. **P1 (vision, 2D viz) only if steps 1–10 are done with time remaining.**
