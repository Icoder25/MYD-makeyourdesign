# KOHLER AI BathPlan — Project State

## Project
KOHLER–MIT-WPU AI Research Lab — Track 1

## Product
**KOHLER AI BathPlan** — an AI bathroom planning agent that turns space, budget,
preferences and priorities into feasible, explainable, sustainability-aware
configurations.

> The AI can imagine a bathroom. The constraint engine decides whether it survives reality.

## CURRENT_PHASE
Phase 13 — final review. Build complete; all phases delivered.

---

## COMPLETED

| Phase | Delivered |
|---|---|
| 0 | Read-only repository audit; two stop-ship defects identified |
| 1 | Git repository initialised; `.env.example` reconciled with code; `uvicorn` added; `google-genai` installed |
| 2 | `docs/verified-facts.md` — every calculated number classified verified / assumption / illustrative, with sources |
| 3 | **Deterministic layout solver** (`backend/layout/`); three-state constraint verdict; both stop-ship defects fixed |
| 4 | Catalog expanded 4 → 33 products with provenance; interface-based compatibility; loader + validation |
| 5 | Transparent water-impact engine with formulas, baselines and assumptions |
| 6 | Performance: 26s → 3.9s (basin-on-vanity, layout memoization, budget pruning) |
| 7 | Planning API, project store, conflict-resolution round trip, CORS |
| 8 | Conversational modification with a fully capable deterministic fallback |
| 9 | Frontend — five screens, real solved geometry, visible uncertainty |
| 10 | Adversarial suite, cases A–G, plus four standing invariants |
| 11 | Golden-path rehearsal script; two further defects found and fixed |
| 12 | `docs/prompts.md` generated from code; prompt PDF; 4-slide deck; README |

## IN_PROGRESS
Final self-review (product / engineering / demo).

## BLOCKED
Nothing.

## TEST_STATUS
**130 passing**, 0 failing.

| Suite | Tests | Covers |
|---|---|---|
| `test_constraints.py` | 7 | Feasibility checks, unknown-never-passes |
| `test_layout.py` | 15 | Placement, clearances, circulation, determinism, cache-leak regression |
| `test_recommendation.py` | 12 | Ranking, weights, budget scoring, trade-offs |
| `test_catalog.py` | 16 | Data integrity, provenance, WaterSense derivation |
| `test_sustainability.py` | 12 | Formulas, baselines, insufficient-data, claim isolation |
| `test_api.py` | 16 | End-to-end HTTP, conflict resolution, validation |
| `test_llm_layer.py` | 26 | Intent extraction, deterministic application, constraint integrity |
| `test_adversarial.py` | 18 | Cases A–G and standing invariants |
| `test_vision.py` | 4 | Schema safety, preprocessing, confidence recomputation |

Demo rehearsal: `python sample-data/golden_path.py` → **PASS**.

---

## KNOWN_BUGS
None outstanding.

Fixed during the build, recorded because each was real:

1. **Every realistic request returned "no configuration."** Fixture zones were required but
   nothing produced them. Fixed by the layout solver deriving them from room geometry.
2. **`CheckResult.blocking` was dead code.** "Nobody measured the rough-in" was treated as
   identically fatal to "this does not fit." Fixed by the three-state verdict.
3. **Cache placeholders leaked into user text** — users were told "slot_2 will not fit."
   Fixed; regression test covers the cached path.
4. **Redundant cascade message** — an unplaced product also produced "no fixture zone exists,"
   restating the same failure less usefully. Zone-fit now only evaluated for placed products.
5. **Budget score rewarded underspending** — a ₹76k plan outranked better options on a ₹2.5L
   brief. Now peaks near 85% of budget.
6. **Water score was flat at 0.50** — it read a certification field that is always unknown and
   averaged non-water products into it.

---

## DECISIONS

| Decision | Reasoning |
|---|---|
| Vite + React over Next.js | No SSR need; faster start; `.env.example` already implied Vite |
| Gemini for both vision and language | One key, one SDK, already a declared dependency |
| Layout solver as the keystone module | Fixes the stop-ship bug, makes the spatial claim real, and produces the 2D geometry — one module serving three needs |
| Three-state constraint verdict | Unknown never becomes pass, but is distinguished from proven failure |
| First-fit placement, not optimal packing | Explainable by hand; stable when a product changes by an inch |
| Engine tests on a fixture catalog | Catalog growth must not break unrelated assertions |
| In-memory project store | Persistence would add migrations and deployment surface for no needed capability |
| Manufacturer claims never folded into computed totals | An "up to 80%" marketing figure is not a measurement; a test enforces this |
| All prices marked `illustrative` | No live KOHLER pricing feed was available |

---

## SCOPE_CUTS
Deliberately not built: 3D rendering · AR · AI concept-image generation · voice ·
custom CV training · authentication · database persistence · e-commerce · live inventory ·
microservices · containers/K8s · cloud deployment · analytics dashboard · multi-room ·
floor-plan PDF parsing · real-time collaboration · i18n · native mobile.

---

## NEXT_STEP
Three final reviews (product, engineering, demo), then record the demo video.

## OUTSTANDING FOR THE OWNER

1. **Record the 1–3 minute demo video.** Run `sample-data/golden_path.py` first to confirm
   the path is green, then follow the sequence in README §6.
2. **Capture screenshots** into `screenshots/` (currently empty).
3. **Push to GitHub** — the repository has full local history but no remote configured.
4. **Delete the stale copy** at `D:\#bigbathroom\kohler-ai-bathplan`. The project moved to
   `D:\kohler-ai-bathplan` because Vite cannot resolve modules under a path containing `#`.
   The old folder is a pre-move snapshot and is **not** current.
5. *(Optional)* Set `GEMINI_API_KEY` to enable the vision and language layers. Everything
   works without it; the AI layers only improve wording and photo context.
