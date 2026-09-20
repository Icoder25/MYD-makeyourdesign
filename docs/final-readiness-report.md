# KOHLER AI BathPlan
# FINAL SUBMISSION READINESS REPORT

*Audit date: 2026-09-18. Every claim below is backed by a command that was run or
a screen that was driven. Where something was not verified, it says so.*

---

## 1. Executive status

**READY WITH KNOWN LIMITATIONS.**

The golden demo runs end to end in a real browser with zero console errors and
zero page exceptions. 161 backend tests pass. The frontend typechecks and builds
clean.

The qualifier is not hedging — there are three specific things a reader should
know before the demo:

1. **`npm run dev` does not work from this repository's current path.** The `#` in
   `D:\#bigbathroom\` breaks Vite's module resolution, and the failure mode is a
   blank page rather than an error. `npm run start` (build + preview) works and is
   the demo path. A `predev` check now refuses to start and explains this.
2. **Projects are in memory** and do not survive a backend restart. A refresh of
   the browser is fine — that is handled — but restarting uvicorn loses the project.
3. **The catalog is illustrative.** Prices are not KOHLER pricing and identifiers
   are not KOHLER SKUs. This is stated in the UI and in every export.

None of the three is a defect introduced by this work; all three are documented.

---

## 2. Phase status

The repository's own phase numbering (in its git history) differs from the phase
numbering in the build brief. This table uses the brief's numbering and points at
the evidence.

| Phase | Status | Evidence |
|---|---|---|
| 1 — DesignState / versioning foundation | **DONE** | `backend/designpulse/project.py`. Frozen `DesignVersion`, append-only chain. 8 tests in `test_designpulse.py`, 6 in `test_designpulse_api.py`. Verified: V1 is byte-identical after V2 exists. |
| 2 — Dependency graph + impact engine | **DONE** | `backend/designpulse/graph.py`, `impact.py`. Edges read off catalog interface declarations, not hand-authored. 11 tests. Verified: vanity → basin → faucet chain; a pedestal basin correctly has no vanity dependency. |
| 3 — API integration + intent parsing | **DONE** | `backend/api/designpulse_routes.py`, `backend/llm/intent.py`. Size, doorway and room vocabulary added — the demo sentence was previously unparseable. 30 tests in `test_llm_layer.py`, 17 in `test_designpulse_api.py`. |
| 4 — Professional DesignPulse UI | **DONE** | `frontend/src/components/DesignPulsePanel.tsx`, `screens/Workspace.tsx`. Three panes plus constraint ledger. Driven in headless Chrome; screenshots 02–05. |
| 5 — Inspiration + export | **PARTIAL** | Export: **DONE** — three documents, `backend/designpulse/export.py`, 6 tests, screenshots 10–12. Inspiration: **NOT BUILT** — see §12 for the reasoning. |
| 6 — Vision integration | **DONE (pre-existing), hardened** | `backend/vision/`. Untouched except `api.py`: it now honours `VISION_ENABLED` and returns a plain advisory instead of leaking `GEMINI_API_KEY is required…` to the UI. 6 tests, 2 of them new. |
| 7 — Professional designer workspace | **DONE** | Full rebuild. The previous frontend was a two-column scroll with DesignPulse below the fold. |
| 8 — Decision memory + version history | **DONE** | `DecisionRecord` on every version; timeline and diff drawers. 9 tests. Screenshots 06–07. |
| 9 — Sustainability intelligence | **DONE** | Engine pre-existed and is sound; surfaced as a drawer with per-fixture arithmetic, baseline, assumptions and cross-version comparison. 12 tests. Screenshot 08. |
| 10 — Final QA + demo readiness | **DONE** | This report. Browser-driven golden demo, failure-path walk, accessibility audit, security audit, screenshots, documentation. |

---

## 3. Automated tests

### Backend

```
python -m pytest -q
161 passed, 1 warning in 38.55s
```

| | |
|---|---|
| **Total** | 161 |
| **Passed** | 161 |
| **Failed** | 0 |
| **Skipped** | 0 |
| **Warnings** | 1 — `PendingDeprecationWarning` from starlette's form parser (third-party, not ours) |

Baseline at the start of this work was **111 passing**. The build brief expected
"179+"; that figure was wrong, and the actual baseline is recorded here rather
than reconciled to it. 50 tests were added; none were deleted, weakened, or
converted into smoke checks.

| File | Tests |
|---|---|
| `test_designpulse.py` | 29 *(new)* |
| `test_designpulse_api.py` | 17 *(new)* |
| `test_llm_layer.py` | 30 *(+2)* |
| `test_api.py` | 17 |
| `test_catalog.py` | 16 |
| `test_layout.py` | 14 |
| `test_recommendation.py` | 13 |
| `test_sustainability.py` | 12 |
| `test_constraints.py` | 7 |
| `test_vision.py` | 6 *(+2)* |

One pre-existing test changed behaviour and was re-examined rather than adjusted:
`test_oversized_vanity_fails_spatial_fit_and_zone_fit`. The first version of the
fixture-zone fix suppressed a genuine failure against a *user-stated* zone. The
rule was narrowed so that only a derived-and-underivable zone is skipped, and the
test passes unmodified.

### Frontend

| | |
|---|---|
| **Typecheck** | `tsc -b --force` — clean, no output |
| **Build** | `vite build` — 30 modules, 218.72 kB JS (64.80 kB gzip), 19.57 kB CSS |
| **Console errors during the driven demo** | 0 |
| **Uncaught page exceptions** | 0 |

There is no frontend unit-test suite. The frontend is verified by driving the
built application in headless Chrome over CDP (§4), which exercises the real
integration rather than mocks.

---

## 4. Golden demo

Driven in headless Chrome against the built app and a live backend, with
`LLM_ENABLED=false` so the deterministic path is what runs.

| # | Step | Result | Observed |
|---|---|---|---|
| 1 | Open the application | **PASS** | Setup screen renders; health strip shows 33 products |
| 2 | Create project (6×8 ft, ₹2,50,000, 6 fixtures, inward door) | **PASS** | — |
| 3 | Leave electrical and rough-in unknown | **PASS** | Both carried forward as verification requirements |
| 4 | Generate V1 | **PASS** | ~2s; 3 options; ₹2,10,000 selected |
| 5 | Plan, products, DesignPulse, ledger all visible at once | **PASS** | 6 spec items, 6 plan rects, 10 ledger cells, no scrolling needed |
| 6 | Ledger shows 9 pass + 1 verification-required | **PASS** | `✓Fixtures ✓Envelope ✓Layout ✓Circulation ✓Zones ✓Compatibility ✓Budget ✓Power ⚠Install ✓Brief` |
| 7 | Request "Make the vanity 60 inches" | **PASS** | Read by the deterministic parser; resolved to the catalog's 60in entry |
| 8 | Change figure computed | **PASS** | `24in → 60in +36in`, `₹2,10,000 → ₹2,94,000` |
| 9 | Affected elements | **PASS** | Vanity (substituted, direct); Basin (revalidated_unchanged, interface dependency) |
| 10 | Unaffected elements | **PASS** | Faucet, shower, storage, toilet — each with the reason |
| 11 | Constraint deltas | **PASS** | Layout ✓→✕ with the geometric reason; Budget ✓→✕ with the overage. Unchanged constraints also reported |
| 12 | Trade-offs offered | **PASS** | 5, each re-verified against the constraint engine by a test |
| 13 | Select a trade-off | **PASS** | Sliding door; detail shows what it gives up and what it has not priced |
| 14 | Apply → V2 | **PASS** | Version chips `V1 V2`; 60in vanity in the spec; plan redrawn |
| 15 | V1 preserved | **PASS** | ₹2,10,000 and the 24in vanity, unchanged |
| 16 | V1/V2 comparison | **PASS** | 1 changed, 5 unchanged; dimension deltas; brief changes; rationale |
| 17 | Decision rationale recorded | **PASS** | Request, understanding, impact, trade-off, what it gave up, the designer's reason |
| 18 | Sustainability | **PASS** | 73,450 L/yr vs 94,507 L baseline, 22% below, per-fixture arithmetic shown |
| 19 | Visual preview / clearance view | **PASS** | Plan, clearances, elevations, site photo tabs |
| 20 | Return to plan | **PASS** | — |
| 21 | Finalization review | **PASS** | 19 satisfied, 1 outstanding — the rough-in skipped at step 3 |
| 22 | Finalize requires acknowledgement | **PASS** | Refused without it (409); accepted with it |
| 23 | Export client presentation | **PASS** | 7 sections, stamped `V2 · active` |
| 24 | Export designer specification | **PASS** | 8 sections including the full constraint ledger and solved coordinates |
| 25 | Export dealer BOM | **PASS** | 6 line items; unavailable before finalization |
| 26 | Switch versions | **PASS** | Read-only bar; DesignPulse input disabled |
| 27 | Export follows the version | **PASS** | V1's dealer BOM refused: "Version V2 was finalized, not V1" |

**Result: 27/27.**

---

## 5. DesignPulse verification

| Claim | Verified by | Result |
|---|---|---|
| Change detection | `test_impact_reports_the_real_dimension_and_price_delta` | Width delta and price delta match the catalog exactly |
| Impact analysis is a dry run | `test_impact_is_a_dry_run_and_creates_no_version` | No version created |
| Affected elements | `test_impact_separates_affected_from_unaffected` | Basin appears as an interface dependency, re-checked |
| Unaffected elements | same | Toilet in unaffected; the two sets are disjoint |
| Constraint evaluation | `test_impact_detects_the_spatial_conflict_the_room_actually_has` | Layout pass→fail, with the 60in-run reason |
| Unchanged constraints reported | `test_unchanged_constraints_are_reported_not_hidden` | Compatibility reported as unchanged, not omitted |
| Trade-offs are real | `test_every_offered_tradeoff_survives_the_constraint_engine` | **Every** proposal re-run through `validate_configuration`; status must match |
| Multi-axis conflicts | `test_a_resolution_blocked_only_by_money_keeps_its_place_with_the_shortfall_named` | Spatial fix + budget shortfall kept, shortfall in the title and the patch |
| Clearances never traded | `test_no_tradeoff_ever_relaxes_a_clearance` | Only the six legitimate kinds are produced |
| V2 creation | `test_applying_a_tradeoff_creates_v2_and_leaves_v1_untouched` | — |
| Version preservation | same | V1's product ids and price unchanged |
| Refusal without a trade-off | `test_applying_an_infeasible_change_without_a_tradeoff_is_refused` | 409; **no version created** |
| Rationale memory | `test_the_decision_record_remembers_why` | Parent, request, rationale, trade-off, affected categories, budget delta |
| Version labelled by outcome | `test_the_version_label_names_what_the_design_became` | A 60in request resolved to 36in is labelled 36in, not 60in |

### One honesty fix worth naming

The trade-off generator described every substitution as "freeing floor area". For
a basin mounted in a vanity top that is false — it reserves no floor at all, and
the benefit is cost. It now tests whether the product actually occupies floor in
*this* configuration and words the proposal accordingly.
`test_a_substitution_does_not_claim_to_free_floor_when_it_cannot` holds it there.

---

## 6. Vision verification

Phase 6 was treated as frozen. The only change is in `backend/vision/api.py`, and
it is additive.

| Property | Status | Evidence |
|---|---|---|
| Advisory only | **CONFIRMED** | `authoritative: Literal[False]`; `test_schema_rejects_authoritative_vision_and_out_of_bounds_boxes` |
| Confidence classification | **CONFIRMED** | `test_confidence_penalizes_occlusions_and_ambiguities` |
| Unknown handling | **CONFIRMED** | Every `unverifiable_attributes` entry typed `status: "unknown"`, `verification_required: True` |
| Verification handling | **CONFIRMED** | Surfaced in the UI under "What a photograph cannot establish" |
| Manual fallback | **CONFIRMED** | `test_vision_route_degrades_without_a_key_and_never_names_it` — planning works with vision off |
| Gemini unavailable | **CONFIRMED** | 503 with a plain advisory. **Previously leaked** `GEMINI_API_KEY is required for Gemini vision analysis` into the UI |
| `VISION_ENABLED=false` honoured | **CONFIRMED (new)** | `test_vision_disabled_by_flag_is_also_a_clean_advisory` — previously ignored |
| No path into the constraint engine | **CONFIRMED** | `backend/vision` is a leaf: no engine imports it |

**Not verified:** behaviour against a live Gemini endpoint. No API key was
available, so the provider adapter is exercised only through a fake. The failure
handling around it is tested; the happy path against the real service is not.

---

## 7. Sustainability verification

Calculated fields, all from recorded catalog figures:

| Field | V1 value |
|---|---|
| `configuration_annual_litres` | 73,449.8 |
| `baseline_annual_litres` | 94,506.6 |
| `annual_litres_saved` | 21,056.8 |
| `percent_saved` | 22.3 |
| Per-fixture formulas | Shown for toilet, shower, faucet |
| `unquantified_products` | Named, never dropped from the total |
| `manufacturer_claims` | Surfaced verbatim, never folded into the total |

Cross-version water delta is computed and, when a change does not affect water, is
reported as **"no change"** rather than as a fabricated saving. In the golden demo
the vanity change produces exactly that — the honest answer, and a useful one.

**Not fabricated:** nothing on the sustainability screen is an estimate of CO₂,
cost saving, or environmental impact beyond water. Those were not computed, so
they are not shown.

---

## 8. Export verification

| Document | Status | Content |
|---|---|---|
| Client presentation | **PASS** | Project, design table, explanation, water with baseline, layout, outstanding verification, decision |
| Designer specification | **PASS** | 11-column product table, full constraint ledger, solved layout with coordinates and clearance sources, water arithmetic, usage assumptions, decision record |
| Dealer BOM | **PASS** | Line items with catalog reference, qty, unit and line price, order total, pre-order notes |

Verified:

- Every product name and the configuration total appear in all three documents
  (`test_exports_price_every_line_from_the_selected_configuration`).
- Documents follow the **selected option**, not just the version
  (`test_selecting_a_different_option_changes_what_exports`).
- A superseded version is stamped `[SUPERSEDED VERSION]`
  (`test_export_carries_the_version_it_was_built_from`).
- Dealer BOM gated on finalization, and on finalization *of that version*.
- Catalog references labelled "not KOHLER SKUs"; prices labelled illustrative.
- Absent catalog data prints "Not available", never `0`
  (`test_export_says_not_available_rather_than_printing_zero`).

---

## 9. Security

| Check | Result |
|---|---|
| Secrets in tracked files | **None.** `git grep` for Google/OpenAI/GitHub/Slack key shapes and private-key headers: no matches |
| Secrets in git history | **None.** `.env.example` is the only env file ever committed |
| `.env` ignored | **Yes.** `.env` and `.env.*` ignored, `!.env.example` excepted |
| `.env.example` contents | **No values.** `GEMINI_API_KEY=` is empty |
| `frontend/.env.local` | Present locally, **untracked and ignored** |
| Frontend reads a key | **No.** The only occurrence is UI copy naming the server-side variable |
| Key read locations | `backend/settings.py`, `backend/vision/provider.py` — environment only, never hard-coded |
| Build artefacts tracked | Fixed: `frontend/tsconfig.tsbuildinfo` was tracked; untracked and added to `.gitignore` |

No secret is printed in this report, and none was found to print.

---

## 10. UX QA

### Desktop

Target 1366×768 / 1440×900 / 1920×1080. Verified at 1440×900 (screenshots 01–14)
and 1024×768 (screenshot 15).

| Width | Layout |
|---|---|
| ≥1280 | Three panes side by side; each scrolls independently; ledger pinned |
| 900–1279 | Two panes; DesignPulse spans the full width below them |
| <860 | Single column; masthead wraps; ledger un-pins |

No overlapping controls at any width. Critical status (the constraint ledger)
stays visible. Header facts scroll horizontally within their own strip rather than
pushing the page.

### States

| State | Handling |
|---|---|
| Loading | Named by task: "Evaluating every valid configuration…", "Computing change impact…", "Generating the new version…", "Preparing the document…". **No fake percentages** |
| Empty | Setup screen explains the unknown-stays-unknown rule; DesignPulse explains what it will do before you ask |
| Error | Every failure answers what happened / what it means / what to do. Backend down offers Retry and says the project is safe |
| Disabled | Apply disabled until a trade-off is selected, with the button text saying why |
| Read-only | Black bar naming the viewed version and the active one, with a return button; DesignPulse input disabled |

### Accessibility

Audited on the live application across the setup screen, workspace, an active
impact analysis, and all six drawers:

| Check | Result |
|---|---|
| Buttons without an accessible name | **0** |
| Inputs without a label | **0** |
| Images without `alt` | **0** |
| SVG without `aria-label` | **0** |
| WCAG AA contrast failures | **0** — was 16, worst 3.54:1 |
| Keyboard: Escape closes a drawer | **Yes** |
| Focus moves into the dialog on open | **Yes** |
| Focus visible | `:focus-visible` outline on every interactive element |
| Semantic roles | `role="dialog"` + `aria-modal`, `role="tablist"`/`"tab"` + `aria-selected`, `aria-pressed` on toggles |

All 16 contrast failures traced to one token (`--ink-muted`), darkened from
`#767d84` to `#5f666d`.

**One item not fully verified:** focus return to the opening element after a
drawer closes. The mechanism is implemented, but the audit drove clicks
programmatically, which does not move focus, so the restore had nothing to return
to. It was not observed working with a real pointer.

### Navigation

- Two screens only: setup and workspace. Everything else is a drawer over the
  workspace, so the designer never loses their place.
- A refresh restores the project from the server. If the server has restarted, it
  falls back to setup and says why.

---

## 11. Known limitations

Only limitations that actually exist.

**Physical and methodological**

1. A single photograph cannot provide metric depth. Vision output is advisory and
   supplies no dimension, rough-in, or electrical fact.
2. Hidden plumbing, wall structure and electrical routing require field
   verification and are not knowable from these inputs.
3. Approximate wall regions from vision are advisory and never reach the solver.
4. Clearance figures are US residential-code minimums (IRC 2021/2024 Ch.27).
   Indian local codes differ and take precedence.
5. Usage assumptions are US-derived EPA planning benchmarks. No equivalent Indian
   per-fixture benchmark was verified.
6. The layout solver is first-fit, not an optimal packer. A layout it rejects may
   be achievable by a human designer with a cleverer arrangement.

**Data**

7. Catalog prices are illustrative and are not KOHLER pricing.
8. Catalog identifiers are prototype references, not KOHLER SKUs.
9. Dimensions are class-typical where a specification sheet could not be verified.
10. WaterSense eligibility is computed against the published threshold. It is not
    a certification claim; per-SKU certification was not verifiable and is unset.

**Engineering**

11. Projects are in memory and do not survive a backend restart. A browser refresh
    is handled; a server restart is not, and the UI says so.
12. `npm run dev` cannot run from a path containing `#`. `npm run start` works.
13. The vision provider has not been exercised against a live Gemini endpoint.
14. There is no frontend unit-test suite; the frontend is verified by driving the
    built app.
15. Finalizing means a designer reviewed the design and acknowledged the
    outstanding verification items. It does not mean any has been measured or
    approved on site.

---

## 12. Remaining submission tasks

### Code complete

- [x] Backend engines, DesignPulse, versioning, export, finalization
- [x] Frontend workspace
- [x] 161 backend tests
- [x] Security audit
- [x] Accessibility audit
- [x] README, architecture, demo script, prompts reference, verified facts
- [x] 15 screenshots from the running application

### Submission assets still needed

- [ ] **4-slide deck** — suggested spine: (1) the problem: iteration cost and
      late-discovered infeasibility; (2) DesignPulse, with the 24in→60in impact
      screenshot; (3) architecture, AI proposes / deterministic verifies; (4)
      water and the three-state rule. Screenshots 03, 05, 07, 08 carry it.
- [ ] **1–3 minute video** — `docs/demo-script.md` is timed to roughly 3 minutes
      and can be cut to 90s by dropping steps 7–9.
- [ ] **Prompts PDF** — `docs/prompts.md` is the source; convert directly.
- [ ] **GitHub repository cleanup** — decide whether `screenshots/` (4.7 MB) and
      the research documents in `docs/` ship with the submission.

### Not built, with reasoning

**Inspiration engine.** The brief said to keep an existing inspiration feature.
There was none in the repository — no module, no route, no data, no tests. Adding
one in the final hours would have meant either curating a style corpus (data entry
that competes with nothing else here) or scraping at demo time, which §33 and §38
both rule out. The judgement was that a shallow new feature would weaken the
submission more than its absence: DesignPulse is the differentiator, and the time
went into making it defensible. Style preference *is* modelled — it influences
ranking through `PreferenceProfile` and is stated in the UI as ranking-only.

---

## 13. Files changed

65 files, +11,607 / −1,509 since the pre-work baseline (`ea81e28`), excluding
lockfile and screenshots.

**New — backend**

```
backend/designpulse/models.py       contracts: impact, decisions, versions, diff, finalization
backend/designpulse/graph.py        dependency edges read off the catalog
backend/designpulse/impact.py       hold constant, change one thing, re-solve, compare
backend/designpulse/tradeoffs.py    proposals, each verified before it is offered
backend/designpulse/project.py      immutable version chain and store
backend/designpulse/diff.py         version comparison
backend/designpulse/export.py       three documents from stored version data
backend/designpulse/service.py      create, analyse, apply, finalize
backend/designpulse/resolve.py      size request → catalog product
backend/api/designpulse_routes.py   HTTP surface
scripts/generate_prompts_doc.py     docs/prompts.md generator
```

**Modified — backend**

```
backend/constraints/engine.py    fixed false fixture-zone verification requirements
backend/constraints/models.py    pinned_product_ids
backend/layout/solver.py         flat-tuple geometry: 8.5s → 2.0s, same results
backend/llm/intent.py            size / doorway / room vocabulary
backend/llm/agent.py             applies them deterministically
backend/llm/prompts.py           documented the new intent fields
backend/api/routes.py            /modify and /resolve append versions
backend/services/store.py        delegates to the version store
backend/settings.py              CORS defaults include the preview origin
backend/vision/api.py            honours VISION_ENABLED; no key name in user errors
backend/recommendation/engine.py honours pins
```

**Frontend** — `App.tsx` rewritten; `screens/` and 8 of 12 `components/` new;
`styles.css` rewritten as a design system; 5 superseded components deleted.

**Tests** — `test_designpulse.py` (29), `test_designpulse_api.py` (17) new;
`test_llm_layer.py` +2, `test_vision.py` +2.

**Docs** — `architecture.md`, `demo-script.md`, `prompts.md`, this report new;
`README.md` and `PROJECT_STATE.md` rewritten; `bathplan-architecture.md`
annotated as historical.

---

## 14. Final recommendation

### What is working

The differentiator is real and it is defensible. "Make the vanity 60 inches"
produces a genuine spatial conflict in a 6×8 ft room — the toilet takes the south
wall, the shower is pushed to the north wall, and no run long enough remains — and
the system explains that in the room's own geometry, names the one downstream
dependency it re-checked, names the four fixtures it did not touch, and offers
five ways out that it has actually tested. A judge can follow the arithmetic by
hand, which is worth more here than a more impressive-sounding claim.

The honesty architecture holds under inspection. Unknown never becomes pass, and
that is visible from the brief through the ledger and into the export. The
language model is a leaf in the import graph, so "the model never decides" is
checkable rather than promised. Every trade-off offered has been re-run through
the constraint engine, and a test enforces it.

The workspace looks like a professional tool. Three panes and a status strip, with
the affected fixture ringed on the plan and edged in the spec list at the same
time, so all three regions are visibly discussing the same thing.

### What is still risky

**The dev-server path problem is the biggest demo risk.** `npm run dev` from this
directory produces a blank page. The preflight check makes that loud instead of
silent, but anyone who types `npm run dev` out of habit on the day will lose time.
Rehearse `npm run start`.

**In-memory state.** Restarting the backend mid-demo loses the project. A browser
refresh is safe; a backend restart is not.

**The vision path is the least-exercised code in the repository** — no live key
was available. Its failure handling is tested; its success path against the real
service is not. If vision is demonstrated, test it with a real key beforehand.

**V1's baseline vanity is 24in, not the 48in the brief assumed.** That is what the
engine actually recommends for this brief, and forcing a 48in baseline would have
meant tuning the scoring to produce a predetermined answer. The demo script uses
the real figure. The change is larger and the story is stronger for it, but anyone
presenting from the brief's numbers will be reading from a script that does not
match the screen.

### What must be fixed before submission

Nothing in the code. The remaining work is assets:

1. Record the video from `docs/demo-script.md`, using `npm run start`.
2. Build the 4-slide deck from screenshots 03, 05, 07, 08.
3. Convert `docs/prompts.md` to PDF.
4. Decide what ships in the repository — `screenshots/` is 4.7 MB.

One optional improvement, if there is time and appetite: move or clone the
repository to a path without `#`, which restores `npm run dev` and removes the
single largest operational risk on demo day.
