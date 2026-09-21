# KOHLER AI BathPlan

**An AI bathroom planning agent that turns space, budget, preferences and priorities
into feasible, explainable, sustainability-aware configurations.**

> The AI can imagine a bathroom. The constraint engine decides whether it survives reality.

Built for the KOHLER–MIT-WPU AI Research Lab Program, Track 1.

---

## 1. The problem

Someone planning a bathroom renovation does not have an imagination problem. They can
already picture what they want. What they cannot do is answer:

> *"Will these products actually fit in my room, together, within my budget — and if
> not, what should I give up?"*

That is a **configuration decision under hard constraints**, not an image-generation
problem. A 72-inch vanity does not fit a 5-foot wall no matter how good the render
looks, and a plan that ignores the 21 inches of clear floor a toilet legally needs is
not a plan.

## 2. What this does

1. You describe your bathroom — dimensions, budget, style, what matters to you.
2. A **deterministic layout solver** places every fixture against a wall with the clear
   space plumbing codes require, respects the door swing, and confirms by flood-fill
   that you can still reach everything.
3. A **constraint engine** checks budget, product compatibility, electrical needs and
   installation requirements — and refuses to turn an unknown into a pass.
4. A **recommendation engine** ranks what survives and returns two or three options
   that differ in ways you'd actually choose between.
5. A **sustainability engine** estimates annual water use against the regulatory
   baseline, showing every formula and assumption.
6. You change your mind in plain language, and the whole plan is recomputed.

**And when your requirements cannot all hold at once, it says so** — naming what broke,
how far off it was, and which specific changes would help. Then you decide.

## 3. What makes it different

Most AI design tools optimise for how the output *looks*. This one optimises for whether
the output is *true*.

| | Typical AI design tool | BathPlan |
|---|---|---|
| Spatial reasoning | Implied by a rendering | Solved geometry with code clearances |
| Feasibility | Asserted | Computed, with the failing check named |
| Unknown information | Filled in plausibly | Stays unknown, surfaced as a verification step |
| Impossible request | Something close, presented as the answer | Refused, explained, alternatives offered |
| Water savings | A percentage | A formula, a baseline, and its assumptions |
| The LLM's role | Decides | Interprets and explains; never decides |

The single most important interaction is the one where the system says **no**.

---

## 4. Architecture

```
                  ┌──────────────────────────────────────┐
   Your brief ───▶│  Frontend (React + TypeScript)       │
   + photo        └───────────────┬──────────────────────┘
                                  │ JSON
                  ┌───────────────▼──────────────────────┐
                  │  FastAPI                             │
                  └───────────────┬──────────────────────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      │                           │                           │
┌─────▼──────┐  advisory   ┌──────▼────────────────────┐  ┌───▼─────────┐
│  Vision    │  only,      │  DETERMINISTIC CORE       │  │  LLM layer  │
│  (Gemini)  │  never ───▶ │                           │  │  (Gemini)   │
│            │  reaches    │  layout solver            │  │             │
│ confidence │  the core   │  constraint engine        │  │ interprets  │
│ + unknowns │             │  recommendation engine    │  │ + explains  │
└────────────┘             │  sustainability engine    │  │ never       │
                           │  product catalog          │  │ decides     │
                           └───────────┬───────────────┘  └───┬─────────┘
                                       │                      │
                           ┌───────────▼──────────────────────▼───┐
                           │ Options · 2D plan · water · conflicts│
                           └──────────────────────────────────────┘
```

The core is pure Python with no LLM dependency and no network calls. **The entire
product works with no API keys configured** — the AI layers are enhancements with
tested fallbacks, not load-bearing components.

### Repository layout

```
backend/
  layout/          deterministic fixture placement + code clearances
  constraints/     feasibility checks; unknown never becomes pass
  recommendation/  ranking, candidate selection, trade-off generation
  sustainability/  transparent water-impact estimation
  catalog/         catalog loading, derived fields, validation
  llm/             intent extraction, prompts, fallback parser
  vision/          image → structured, non-authoritative evidence
  api/             HTTP routes and request/response schemas
  services/        planning orchestration, in-memory project store
frontend/          React + TypeScript SPA (Vite)
catalog/           products.json — the curated product data
tests/             197 tests, including an adversarial suite
sample-data/       golden_path.py — the demo, as a runnable check
docs/              research, spec, architecture, prompts, verified facts
```

---

## 5. Setup

**Requirements:** Python 3.11+, Node 18+.

> ⚠️ **Do not clone into a path containing `#`.** Vite/Rollup cannot resolve modules
> under such a path and the frontend will not build. Any normal path is fine.

```bash
git clone <repository-url>
cd kohler-ai-bathplan

# Backend
python -m pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### Environment variables

Copy `.env.example` to `.env`. **Every variable is optional.** With none set, the
deterministic planner, the 2D plan, water estimation, conflict resolution and
conversational modification all work.

| Variable | Default | Effect if unset |
|---|---|---|
| `PORT` | `8000` | — |
| `CORS_ORIGINS` | `localhost:5173` | — |
| `CATALOG_PATH` | `catalog/products.json` | — |
| `GEMINI_API_KEY` | _(none)_ | Vision and LLM layers use fallbacks |
| `VISION_ENABLED` | `true` | Set `false` to force manual-input path |
| `GEMINI_VISION_MODEL` | `gemini-2.5-flash` | — |
| `LLM_ENABLED` | `true` | Set `false` to force the keyword parser |
| `GEMINI_LLM_MODEL` | `gemini-2.5-flash` | — |

### Running

Two terminals:

```bash
# Terminal 1 — backend on :8000
uvicorn backend.main:app --reload

# Terminal 2 — frontend on :5173
cd frontend && npm run dev
```

Open <http://localhost:5173>. API docs at <http://localhost:8000/docs>.

### Verifying it works

```bash
python -m pytest -q                    # 197 tests
python sample-data/golden_path.py      # rehearses the demo end-to-end
```

`golden_path.py` prints **PASS** or **FAIL**. If it fails, the demo is broken.

---

## 6. The demo

**Brief:** 6 × 8 ft bathroom · ₹2,50,000 · modern minimalist · water efficiency and
smart features prioritised.

1. **Plan.** ~1,460 configurations evaluated; three options returned, each within budget
   and differing meaningfully — recommended, lowest-cost, most water-efficient.
2. **Plan view.** The solver's actual geometry, with the dashed code-clearance zones
   and door swing that decided feasibility drawn in.
3. **Water.** ~73,450 L/year against a 94,507 L baseline — about 22% lower — with every
   formula and assumption shown.
4. **Modify:** *"Add a smart shower and a smart toilet and a bathtub, keep my budget."*
5. **Conflict.** Over budget by ₹18,300 *and* physically unplaceable in 6 × 8 ft. The
   system shows both, and notes that **more budget would not fix a spatial problem**.
6. **Resolve.** User drops the bathtub; the plan is recomputed from scratch; both smart
   fixtures survive and the budget still holds.

---

## 7. How the pieces work

### Layout solver (`backend/layout/`)

Places fixtures against walls at 1-inch increments, taking the first position where the
footprint and its required front clearance both fit, overlap no other footprint, and
clear the door swing. Two fixtures' *clearance* zones may overlap — that is how real
bathrooms work — but clearance into a footprint is forbidden. A 3-inch grid flood-fill
from the doorway then confirms every fixture is reachable.

Clearances are IRC 2021/2024: **21 in** clear in front of a toilet, **15 in** from
centreline to a side wall, **30 × 30 in** minimum shower interior.

First-fit rather than optimal packing, deliberately: a judge can follow it by hand, and
the layout does not change unpredictably when a product changes by an inch.

### Constraint engine (`backend/constraints/`)

Eight checks producing a three-state verdict:

- `feasible` — everything passed.
- `feasible_pending_verification` — nothing is proven broken, but something is unverified.
  Offered to the user, ranked strictly below any fully verified option, and carrying
  every outstanding item with it.
- `infeasible` — a check failed on evidence.

**An unknown never becomes a pass.** An unmeasured rough-in is not the same as a
mismatched one, and conflating them either blocks every real plan or fakes confidence.

### Recommendation engine (`backend/recommendation/`)

Hard constraints filter first; scoring only ever orders what already survived. Weights
across six dimensions are configurable per request. Candidates are chosen by *archetype*
so the options differ genuinely rather than being one plan with a component swapped.
The budget score rewards **using** the budget well, not spending as little as possible.

### Sustainability engine (`backend/sustainability/`)

Separates verified specification, usage assumption, and calculation — and keeps them
separate. Every fixture reports its formula, its recorded spec, and the federal-standard
baseline it was compared against. A manufacturer's "up to 80%" claim is shown verbatim
with its source and caveats and is **never** folded into a computed total; a test fails
if it ever is. Missing flow data returns `insufficient_data`, not a plausible guess.

### Product catalog (`catalog/products.json`)

33 curated products across 9 categories. Every record carries `price_status` and
`verification_status`. **All prices are `illustrative`** — no live KOHLER pricing feed
was available. WaterSense eligibility is *computed* by the loader from the recorded flow
figure against the published threshold, so the flag cannot drift from the number behind
it; it is an eligibility calculation, not a certification claim. Products name the
KOHLER family their class is modelled on as a taxonomy pointer, never as a SKU claim.

The catalog is designed to be replaced wholesale by an authorised live feed without any
engine change.

---

## 8. Known limitations

Stated plainly, because a planning tool that hides these is dangerous.

- **Prices are illustrative.** Not KOHLER pricing, not quotes, not MRP.
- **Dimensions are class-typical** where a specification sheet could not be verified.
- **Clearances are US residential-code figures** (IRC). Indian local codes differ. They
  are used as planning minimums, and the product does not claim local-code compliance.
- **Usage benchmarks are US-derived** (EPA). Indian household patterns differ; no
  equivalent per-fixture benchmark was verified. They are adjustable inputs.
- **A photograph establishes nothing measurable.** Vision output is advisory and
  structurally cannot reach the constraint engine.
- **Hidden plumbing, rough-in, electrical capacity and structure are unknown** and stay
  unknown until you verify them.
- **The layout is first-fit, not optimal.** A better arrangement may exist.
- **Projects are in-memory** and do not survive a restart. There is no database. The
  browser keeps your saved designs in `localStorage`; reopening one after the backend
  has restarted rebuilds the planning session from the saved brief and starts again
  at V1, so version history earlier than that is not recoverable.
- **The AI layers need quota, not just a key.** With a Gemini free-tier key the intent
  and vision calls are rate limited (20 requests/minute at the time of writing) and
  will fall back to the deterministic path once exhausted. The fallback is complete —
  the whole product works without any key — but the fallback is now logged at WARNING
  so an exhausted quota is visible rather than silent.
- **Gemini model ids are retired on a schedule.** `GEMINI_LLM_MODEL` and
  `GEMINI_VISION_MODEL` are pinned to a currently-served release; a `404 NOT_FOUND`
  from the provider means the pin needs moving.
- **360° is a schematic walk-around**, generated from the solved layout — four wall
  elevations, not a rendered panorama or photography.
- **AR is not implemented.** The tab explains what it would need (per-product USDZ and
  glTF assets, which the prototype catalog does not carry) and points at the 2D, 3D
  and elevation views instead.
- **Finalization is a sign-off in the browser**, not a server-side lock. It records
  that the checklist was confirmed; it does not prevent later edits through the API.
- **This is a planning aid, not an engineering drawing.** Final dimensions, plumbing,
  electrical, structural and local-code requirements must be verified by a qualified
  professional before installation.

## 9. Production roadmap

1. **Authorised catalog integration** — replace illustrative data with a live KOHLER
   feed; the schema already separates verified from illustrative fields.
2. **Regional code packs** — swap the IRC clearance table for a jurisdiction's own,
   including Indian standards. The rules are already isolated in one module.
3. **Rough-in capture** — guided measurement flow to convert the commonest verification
   requirement into a verified fact.
4. **Designer handoff** — export the configuration, plan and verification list as a
   package for a KOHLER design consultant, positioning BathPlan upstream of the existing
   human service rather than competing with it.
5. **Installed-base water tracking** — compare estimates against Konnect-connected
   actuals to replace assumed usage with measured usage.

---

## 10. Documentation

| Document | Contents |
|---|---|
| [docs/product-spec.md](docs/product-spec.md) | Product specification and MVP scope |
| [docs/bathplan-architecture.md](docs/bathplan-architecture.md) | Architecture and module boundaries |
| [docs/verified-facts.md](docs/verified-facts.md) | Every number classified verified / assumption / illustrative, with sources |
| [docs/prompts.md](docs/prompts.md) | Prompt documentation, generated from the running code |
| [docs/KOHLER_AI_BathPlan_Prompt_Documentation.pdf](docs/KOHLER_AI_BathPlan_Prompt_Documentation.pdf) | The same prompt documentation, rendered for submission |
| [docs/KOHLER AI BathPlan Pitch Deck.pdf](docs/KOHLER%20AI%20BathPlan%20Pitch%20Deck.pdf) | The 4-slide deck |
| [docs/presentation.pptx](docs/presentation.pptx) | The same deck as an editable PowerPoint file |
| [docs/research.md](docs/research.md) | Market and problem research |
| [docs/competitor-matrix.md](docs/competitor-matrix.md) | Evidence-based capability comparison |
| [docs/innovation-gap.md](docs/innovation-gap.md) | Where the defensible opportunity is |
| [docs/kohler-current-state.md](docs/kohler-current-state.md) | KOHLER capability audit |
| [PROJECT_STATE.md](PROJECT_STATE.md) | Current build state and decisions |

The four generated artefacts are built from the code, not written by hand — the prompt
document is read out of `backend/llm/prompts.py`, and the plan on slide 3 of both decks
is the layout solver's real output for the demo brief. Rebuild them with:

```bash
pip install -r requirements-docs.txt
python scripts/generate_prompt_docs.py   # docs/prompts.md
python scripts/build_pdfs.py             # docs/KOHLER_AI_BathPlan_Prompt_Documentation.pdf, docs/KOHLER AI BathPlan Pitch Deck.pdf
python scripts/build_pptx.py             # docs/presentation.pptx
```

---

*Prototype built for the KOHLER–MIT-WPU AI Research Lab Program. Product data is
illustrative and is not KOHLER pricing or verified specification.*
