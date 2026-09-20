# Architecture — as built

The design record from before implementation is
[`bathplan-architecture.md`](bathplan-architecture.md). It is kept for the
decisions it explains, but it describes a system that was planned, not the one
that exists. **This document describes what is actually in the repository.**

---

## The one-sentence version

**AI proposes and explains; deterministic systems verify.**

A language model reads the designer's sentence and writes the prose. Everything
that could be wrong in a way that costs money — whether a fixture fits, what it
costs, whether it is feasible, how much water it uses — is computed by pure Python
that has no model in it anywhere.

---

## Flow

```
                        ┌─────────────────┐
                        │ Designer        │
                        └────────┬────────┘
                                 ↓
                          Project brief
                                 ↓
        ┌────────────────────────┼────────────────────────┐
        ↓                        ↓                        ↓
  Site photograph          Change request          Room / budget /
  (optional)               (plain language)        required fixtures
        ↓                        ↓                        │
  ┌───────────┐          ┌──────────────┐                 │
  │ Gemini    │          │ Gemini       │                 │
  │ vision    │          │ intent       │                 │
  │ ADVISORY  │          │ TRANSLATION  │                 │
  └─────┬─────┘          └──────┬───────┘                 │
        │                       │ structured intent       │
        │                       │ (validated, sanitised)  │
        │                       ↓                         │
        │                  DETERMINISTIC ←────────────────┘
        │                  application to the brief
        │                       ↓
        │              ┌────────────────┐    ┌──────────────────┐
        │              │ Catalog        │    │ Clearance rules  │
        │              │ 33 products    │    │ IRC 2021/2024    │
        │              └───────┬────────┘    └────────┬─────────┘
        │                      └──────────┬───────────┘
        │                                 ↓
        │                    ┌────────────────────────┐
        │                    │ Recommendation engine  │
        │                    │ Layout solver          │
        │                    │ Constraint engine      │
        │                    │ Water calculator       │
        │                    └───────────┬────────────┘
        │                                ↓
        │                          Design V1
        │                                ↓
        │                    ┌────────────────────────┐
        └───────────────────▶│ DESIGNPULSE            │
          advisory only,     │ dependency graph       │
          shown beside the   │ impact analysis        │
          plan, never in it  │ evaluated trade-offs   │
                             └───────────┬────────────┘
                                         ↓
                             Designer chooses a trade-off
                                         ↓
                          Design V2  +  decision record
                            (V1 is never overwritten)
                                         ↓
                   ┌─────────────────────┼─────────────────────┐
                   ↓                     ↓                     ↓
            Version diff          Water impact          Finalize + export
```

---

## Modules

| Module | Responsibility | Dependencies |
|---|---|---|
| `backend/catalog` | Load, validate, compute derived water fields | — |
| `backend/layout` | Place fixtures against walls with code clearances; flood-fill circulation | clearance rules |
| `backend/constraints` | Three-state verdicts across ten checks | layout, catalog |
| `backend/recommendation` | Search, score, rank; structured conflict reporting | constraints |
| `backend/sustainability` | Annual water from recorded flow figures | catalog |
| `backend/designpulse` | Dependency graph, impact, trade-offs, versions, diff, export | all of the above |
| `backend/llm` | Prompt registry, intent extraction, deterministic fallback | — |
| `backend/vision` | Gemini adapter; advisory-only schema | — |
| `backend/api` | HTTP contracts and routes | designpulse, services |

The arrows only point one way. `backend/llm` and `backend/vision` are leaves: no
engine imports them, which is what makes "the model never decides" a property of
the import graph rather than a promise in a prompt.

---

## The three-state rule

Every check returns one of:

| State | Meaning | Blocks? |
|---|---|---|
| `pass` | The check succeeded. | — |
| `verification_required` | The information needed was not supplied. | No — but never becomes a pass |
| `fail` | Proven infeasible. | Yes |

Rolled up per configuration:

- `feasible` — everything passed.
- `feasible_pending_verification` — nothing is proven broken, and the outstanding
  items travel with it.
- `infeasible` — at least one proven failure.

A configuration is `offerable` when it is not infeasible. That distinction is why
the product can plan for someone who has not measured their rough-in, without
pretending the rough-in is fine.

---

## The layout solver

Pure geometry. No model, no randomness, no network; the same input always produces
the same layout.

1. Floor-consuming fixtures are sorted by placement priority — the most
   plumbing-constrained first, because it has the fewest legal positions.
2. Each is offered every wall and every 1-inch offset, taking the first position
   where the footprint and its required front clearance both fit inside the room,
   overlap no other footprint and no other fixture's clearance, and clear the door
   swing. Two fixtures' *clearance* zones may overlap each other — that is how real
   bathrooms work — but clearance into a footprint is forbidden, because that is
   what makes a fixture unusable.
3. A 3-inch grid flood-fill from the doorway confirms every placed fixture's clear
   space is actually reachable. This catches the layout that satisfies every
   individual rule and still walls someone out of the shower.
4. Solved geometry becomes the fixture zones the constraint engine consumes, and
   the coordinates the 2D plan renders.

First-fit rather than optimal packing is deliberate: it is fast, reproducible, and
a reviewer can follow it by hand. The cost is honest and stated — a layout it
rejects may be achievable by a human designer with a cleverer arrangement.

**Performance.** A six-category brief explores 2,000 configurations. Identical
geometries are cached (swapping a faucet changes the price, not the floor plan),
and the placement search and flood-fill run on flat coordinate tuples rather than
constructing a validated model per cell per fixture. That is the difference
between 8.5 seconds and 2.0 seconds for the same result.

---

## DesignPulse

### The method

> Hold everything else constant. Change the one thing. Re-solve. Compare.

Re-running the recommendation search instead would produce a *different* good
configuration, and the designer would have no way to tell which differences their
request caused and which were the search wandering. Holding the rest fixed is what
makes "what else changed?" answerable at all.

### The dependency graph

Not a hand-authored rule table. Every edge is read off data the system already
holds:

| Edge | Source |
|---|---|
| Interface | `provides_interfaces` / `requires_interfaces` in the catalog. A basin requiring `vanity_top` depends on the vanity that provides it; a faucet requiring `faucet_mount_single_hole` depends on the basin. |
| Shared floor | `FOOTPRINT_CATEGORIES` in the clearance module, adjusted for products that mount onto another (a basin in a vanity top reserves no floor of its own). |
| Shared budget | Every priced product in the configuration. |
| Shared water | Every fixture that contributes to the annual total. |

The graph supplies the **reason**. It never supplies the **verdict** — whether
something was actually affected is decided by comparing the before and after state
the engines produced:

| Outcome | Test |
|---|---|
| `substituted` | The product id changed. |
| `repositioned` | The solver put it somewhere else. |
| `displaced` | It was placed before and cannot be placed now. |
| `restored` | It could not be placed before and can be now. |
| `revalidated_unchanged` | It depends on the changed item through a declared interface, and the connection still holds. |
| *unaffected* | None of the above: same specification, same position, same connections. |

`revalidated_unchanged` earns its place on the affected list. "We checked, and it
still connects" is a different and more useful statement than silence.

### Trade-offs

Every proposal is run through `validate_configuration` — which means through the
layout solver, the clearance rules, the compatibility graph and the budget check —
**before it is offered**. If the engine says infeasible, it is not shown.

Six kinds, all of them decisions a bathroom designer actually has:

1. Substitute another fixture (frees floor, or costs less — the proposal says which).
2. Change the doorway (an inward swing reserves floor a sliding door does not).
3. Raise the budget.
4. Reduce the request.
5. Drop a requirement.
6. Enlarge the room — found by search, and always labelled as construction.

The one thing never proposed is relaxing a clearance. Those are code minimums;
trading them away would make the product's central claim untrue.

**Multi-axis conflicts.** A large change often breaks space *and* budget at once. A
proposal that fixes the floor plan but leaves the budget over would be discarded
for failing a constraint it was never addressing — so a resolution whose only
remaining blocker is money keeps its place, with the exact shortfall folded into
its title and its patch. The designer sees *"this fits, and it costs ₹44,000
more"*, which is the real choice.

---

## Versioning

A project is a chain of **frozen** `DesignVersion` records. Applying a change
appends; it never writes back into the version it started from. The one mutation
permitted on an existing version is which of its own options is selected, because
choosing between results the engines already computed does not change them.

The active design is always the newest version. Viewing an earlier one is
inspection, marked read-only in the UI and in the API response. There is no
"activate an old version" operation, because rewinding would make the chain
ambiguous about what the current design is.

Each version carries a `DecisionRecord`: the request, how it was understood, which
interpreter understood it, the impact summary, affected and unaffected categories,
the trade-off accepted and what it gave up, the designer's stated reason, the
constraint state, and budget and water deltas.

---

## Export

Three documents, assembled entirely from the stored version. Nothing is recomputed
at export time, so an export cannot disagree with the workspace that produced it,
and every document carries the project and version identity it was built from —
including a `[SUPERSEDED VERSION]` stamp when it is not the active one.

The dealer bill of materials is gated on finalization: it is the document that
turns a design into an order, so it is the one that requires a designer to have
reviewed the outstanding verification items first.

Where the catalog has no verified figure, the document prints "Not available". A
blank, a zero, or an invented SKU would all be worse.

---

## Failure behaviour

| Failure | Behaviour |
|---|---|
| No `GEMINI_API_KEY` | Vision returns 503 with a plain advisory. Intent falls back to the deterministic parser. Everything else is identical. |
| Gemini timeout / malformed JSON / schema violation | Caught; deterministic parser runs; the response records which interpreter was used. |
| Model invents a category | `ModificationIntent.sanitised()` drops it before it reaches the planner. |
| Requested change is infeasible | 409 with the evaluated trade-offs. **No version is created.** |
| Chosen trade-off is not one that was offered | 409. No version is created. |
| Backend unreachable | The UI says so, explains that projects are session-scoped, and offers retry. |
| Server restart | Projects are gone. The 404 says exactly that rather than "not found". |

---

## What is deliberately not here

No authentication, no database, no microservices, no 3D renderer, no AR, no web
scraping, no live product feed, no model training. Each would have cost days and
bought no capability this product needs. The catalog is designed to be replaced
wholesale by an authorised live KOHLER feed without any engine change: swap the
JSON, keep the schema.
