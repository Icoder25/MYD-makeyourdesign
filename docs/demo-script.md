# Demo script

Every figure below is the actual output of the deterministic engines for this
brief, verified end to end in a browser. Nothing here is illustrative. If a number
in this document does not match what the screen shows, the document is wrong —
regenerate it by running the walkthrough.

---

## Before you start

```bash
# terminal 1
uvicorn backend.main:app --reload

# terminal 2
cd frontend && npm run start        # http://localhost:4173
```

The demo needs **no API key**. Set `LLM_ENABLED=false` to guarantee the
deterministic intent parser runs, which makes the demo bit-for-bit repeatable —
the language model is an enhancement here, not a dependency, and a demo should not
depend on a network round trip.

Expect V1 generation to take **about two seconds**.

---

## The story in one minute

> A designer gives BathPlan a bathroom brief. The system generates a feasible
> baseline. The designer changes one thing. DesignPulse immediately explains what
> else changes. The designer chooses a trade-off. BathPlan creates a new version
> while preserving the original decision. The designer can compare, check the water
> impact, finalize and export.

---

## Walkthrough

### 1 · The brief (20 seconds)

The setup screen opens pre-filled with the demo project. Point at one thing:

| Field | Value |
|---|---|
| Project | Master Bathroom |
| Room | 6 × 8 ft |
| Door | Hinged, opens inward |
| Budget | ₹2,50,000 |
| Fixtures | Vanity, basin, faucet, toilet, shower, storage |
| Electrical supply | **Not confirmed** |
| Toilet rough-in | **blank** |

> "The last two are the point. I don't know them, so I'm not going to pretend I do.
> Watch where they end up."

Click **Generate baseline design**.

### 2 · V1 (25 seconds)

The workspace opens. Four regions, each answering a different question:

- **Left** — where things are. Every rectangle is a coordinate the layout solver
  computed. The dashed red zone is the floor the inward door swing reserves.
- **Centre** — what is specified. Six fixtures, ₹2,10,000 of a ₹2,50,000 budget.
- **Right** — DesignPulse, waiting.
- **Bottom** — ten constraint checks. Nine ticks and one amber.

> "Nine checks passed. One is amber — installation. That's the rough-in I didn't
> measure. It didn't become a tick, and it didn't stop the plan either. It's
> recorded as needing verification, and it will follow this design all the way into
> the export."

Header reads: **Feasible — verification required**.

Optional aside — click **Clearances** in the plan tabs to show the code-minimum
clear floor in front of every fixture. That is what the solver was actually solving.

### 3 · The change (30 seconds) — *this is the demo*

In DesignPulse, click the suggestion **"Make the vanity 60 inches"**.

```
Vanity: 24in → 60in cannot be built as requested:
2 constraint(s) fail. 5 evaluated way(s) to resolve it.

Read as: resize the vanity to 60 inches wide   [deterministic parser]
```

The change figure is large and unmissable:

```
24in  →  60in   +36in
```

Then the counts, then the detail:

| | |
|---|---|
| **Affected** | 2 |
| **Unaffected** | 4 |
| **Constraints moved** | 2 |
| **Trade-offs** | 5 |

**Affected**
- *Vanity* — substituted. The change itself.
- *Basin* — **re-checked**. "Vessel Basin needs a vanity top to mount into, which
  Double-Basin Vanity 60in is part of providing. The connection was re-checked and
  still holds."

**Unaffected** — toilet, shower, faucet, storage. Each says why: same
specification, same position, same connections.

**Constraints moved**
- *Layout* ✓ → ✕ — "No wall position leaves the vanity a 60in run with 21in of
  clear space in front of it once the other fixtures and the door swing are placed."
- *Budget* ✓ → ✕ — ₹2,10,000 → ₹2,94,000, which is ₹44,000 over.

> "This is the part that matters. It didn't just say no. It told me the basin is
> downstream of the vanity and re-checked it. It told me four fixtures are
> genuinely untouched — that's computed, not assumed. And it told me exactly which
> two constraints broke and why."

Notice the vanity is now ringed on the plan and edged in the specification list.
All three panes are talking about the same fixture.

### 4 · The trade-offs (30 seconds)

Scroll the DesignPulse pane. Five options, each already run through the constraint
engine:

| Option | Result | Total |
|---|---|---|
| **Fit a sliding door, and raise the budget by ₹44,000** | feasible — verification required | ₹2,94,000 |
| Settle for 36in instead of 60in | feasible — verification required | ₹2,35,000 |
| Leave out the toilet | feasible | ₹2,26,000 |
| Leave out the shower, and raise the budget by ₹10,000 | feasible — verification required | ₹2,60,000 |
| Plan for a 6.5 × 8.5 ft room, and raise the budget by ₹44,000 | feasible — verification required | ₹2,94,000 |

> "None of these is a guess. Each one was built and run through the layout solver
> and the constraint engine before it was offered. If the engine said no, it isn't
> on this list."

Click **Detail** on the sliding door option:

> "The inward swing reserves a 30in square of floor that no fixture may occupy. A
> sliding or pocket door reserves none, which releases that area for the requested
> change."
>
> *Gives up:* a hinged door. Converting to sliding is a joinery change, not a
> fixture swap. It also needs ₹44,000 more than the stated budget.
>
> *Side effect:* the cost of the door conversion is not in the catalog and is not
> in this total.

> "It tells me what I'm giving up, and it tells me what it hasn't priced."

Select it. Type a reason: **"Client wanted twin basins."** Click **Apply**.

### 5 · V2 (20 seconds)

- Header now shows two version chips: **V1 V2**.
- The specification shows **Double-Basin Vanity 60in, 60in × 22in, ₹1,08,000**.
- The plan redraws — the 60-inch vanity is on the north wall, the door swing zone
  is gone, and everything else holds its position.
- DesignPulse says: *"Recorded as V2. The version it came from is unchanged and
  still available to compare against."*

Click the **V1** chip. A black bar appears:

> **Read-only — viewing V1.** This version has been superseded. The active design
> is V2.

The DesignPulse input is disabled. Click **Return to V2**.

> "V1 is exactly as it was. Nothing overwrote it."

### 6 · Compare (20 seconds)

**History** → **Compare**. V1 → V2:

| | |
|---|---|
| Cost | ₹2,10,000 → ₹2,94,000 **(+₹84,000)** |
| Annual water | 73,450 L → 73,450 L **(no change)** |
| Outstanding verifications | 1 → 1 |
| Brief changes | Door: inward → sliding · Budget limit: INR 250,000 → INR 294,000 |
| Products | **1 changed, 5 unchanged** |

The product table shows all six rows. Only the vanity is highlighted:
`width 24in → 60in · depth 18in → 22in · height 32in → 34in`.

Reason for the change: *"Client wanted twin basins."*

Switch to the **Timeline** tab to show the decision records — what was requested,
what the impact was, which trade-off was accepted, what it gave up, and why.

> "Five products unchanged is a claim, and it's checked. Water didn't move, because
> a vanity isn't a water fixture — so it says 'no change' rather than inventing a
> saving."

### 7 · Water (15 seconds)

**Water** in the header:

| | |
|---|---|
| This configuration | **73,450 L/year** |
| Regulatory baseline | 94,507 L/year |
| Difference | 21,057 L/year less — **22% below baseline** |

Baseline stated underneath: *US federal maximum flow standards (Energy Policy Act
of 1992): 1.6 gpf toilets, 2.5 gpm showerheads, 2.2 gpm lavatory faucets.*

Expand **Show the arithmetic**:

```
1.28 gpf x 4 flushes/person/day x 3 people x 365 days x 3.78541 L/gal
```

> "A percentage with no baseline is a marketing number. The baseline is printed
> next to every figure, and the arithmetic is one click away."

### 8 · Finalize (20 seconds)

**Finalize**:

- **Satisfied** — 19 checks, each with the engine's own reasoning.
- **Requires field verification** — 1: *"Toilet rough-in for Wall-Hung Toilet with
  Concealed Tank cannot be verified."*

That is the measurement skipped in step 1, still outstanding, seven steps later.

The acknowledgement is explicit:

> I have reviewed this configuration and acknowledge the 1 outstanding verification
> item listed above. I understand that finalizing does not mean any of them has
> been measured or approved on site.

Tick it, click **Finalize design**.

> "Finalized doesn't mean verified. It means a designer looked at what's
> outstanding and accepted responsibility for it. The item stays on the record."

### 9 · Export (20 seconds)

**Export** — three documents, all built from the stored V2:

- **Client presentation** — the design in plain language, the water story, the
  layout, and the outstanding verification.
- **Designer specification** — full product table with catalog references,
  dimensions, installation type, rough-in, interfaces, water spec, price basis;
  the complete constraint ledger; the solved layout with coordinates and the
  clearance source for each; the water arithmetic; the decision record.
- **Dealer bill of materials** — line items, quantities, totals.

Each is stamped **V2 · active**. Try the dealer BOM before finalizing and it says:

> The bill of materials is available once the design has been finalized.

> "The dealer document is the one that turns a design into an order, so it's the
> one gated on a designer having reviewed what's outstanding."

**Download .txt** produces exactly what is on screen.

---

## Closing line

> "One change. The system told me what else it touched, what it broke, what it
> didn't, and five ways out it had actually tested. I picked one, and it kept both
> versions and the reason. The AI read my sentence and wrote the explanation.
> It didn't decide a single number on this screen."

---

## If something goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| Every request fails; banner says the service is not responding | Backend not running, or an origin not in `CORS_ORIGINS` | Start uvicorn; the defaults already allow `:5173` and `:4173` |
| Frontend page is blank | `npm run dev` from a path containing `#` | Use `npm run start` |
| "This project is not in the planner's memory" | Backend restarted; projects are session-scoped | Create the project again |
| Site image analysis shows an advisory | No `GEMINI_API_KEY` | Expected. Nothing else is affected — this is worth showing deliberately |

## Repeatability

The demo is deterministic. The same brief always produces the same V1: the search
is exhaustive within its bounds, the layout solver is first-fit over a fixed
ordering, and scoring has no randomness. With `LLM_ENABLED=false` there is no
network call in the entire path.
