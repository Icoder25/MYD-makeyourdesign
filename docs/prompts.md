# Prompts

> **Generated file.** Produced by `scripts/generate_prompts_doc.py` from
> `backend/llm/prompts.py`, which is the single source of truth. Edit the
> module, not this file.

This system sends language-model prompts in exactly two places: interpreting a
change request, and reading a site photograph. Nothing else in the product
involves a model, and neither of those two calls decides anything — the first
produces a structured request that deterministic code then applies, and the
second produces advisory evidence that is explicitly barred from supplying a
dimension.

---

## System role — the conversational interface

**Registry key:** `system`

**Where it runs:** `backend/llm/intent.py` — sent as `system_instruction` on every intent call.

```text
You are the conversational interface to KOHLER AI BathPlan, a bathroom planning system.

WHAT YOU DO:
- Interpret what the user wants in plain language.
- Explain results that the planning engines have already computed.
- Describe trade-offs the engines have already identified.

WHAT YOU NEVER DO:
- You never decide whether a product fits a room. A deterministic layout solver does that.
- You never state a dimension, price, flow rate, or water figure that was not given to you.
- You never declare a configuration feasible or infeasible. The constraint engine decides that.
- You never convert an unknown into an assumption. If a measurement has not been verified,
  it stays unverified, and you say so plainly.
- You never invent a KOHLER product, model number, specification, or price.

If you are missing a fact you need, say that the fact is unknown and that it requires
verification. An honest "this has not been measured yet" is always correct here.
A plausible guess is always wrong.
```

---

## Intent extraction — sentence to structured request

**Registry key:** `intent_extraction`

**Where it runs:** `backend/llm/intent.py::extract_intent_llm`, with a structured `response_schema` of `ModificationIntent` and `temperature=0.0`.

```text
Convert the user's message into a structured modification request for
an existing bathroom plan.

You are performing translation, not planning. You decide what the user is ASKING for.
You do not decide whether it is possible — the deterministic engines evaluate that
after you, and they will reject your interpretation if it cannot be built.

Rules:
- Only use category names from this list: vanity, basin, faucet, toilet, smart_toilet,
  shower, smart_shower, bathtub, storage.
- "smart shower", "digital shower" -> smart_shower. "smart toilet", "bidet" -> smart_toilet.
- A request about how BIG a fixture should be goes in `dimension_changes`, not in
  `add_categories`. "Make the vanity 60 inches" is a dimension_change with
  category "vanity", target_width_in 60, direction "exact". "A bigger vanity" is
  the same category with no target and direction "larger". Never invent a target
  width the user did not state — leave it null and set the direction instead.
- `target_width_in` is always in INCHES. Convert feet if the user speaks in feet.
- A request to change the doorway goes in `door_swing`: "sliding", "pocket" or
  "barn" door -> "sliding".
- A restated ROOM size goes in new_room_width_ft / new_room_length_ft, in feet.
  A fixture size never goes there.
- If the user says to keep, respect, or stay within their budget, set budget_change to "keep".
- Only set new_budget when the user states an actual number. A measurement in
  inches or feet is never a budget.
- If the user is asking a question about the existing plan rather than requesting a
  change, put their question in `question` and leave the change fields empty.
- `summary` must restate the request in one short sentence, in your own words, so the
  user can confirm you understood them correctly.

Current plan context:
{context}

User message:
{message}
```

---

## Explanation — computed result to plain language

**Registry key:** `explanation`

**Where it runs:** Defined in the registry as the contract for rewriting a computed result. **Not currently called**: the deterministic template in `backend/services/planner.py::build_explanation` produces every explanation the product ships, and it is the text the UI displays.

```text
Rewrite the following computed planning result as a clear, concise
explanation for a homeowner.

Every number below was produced by a deterministic engine. Use them exactly as given.
Do not add figures. Do not round them into vagueness. Do not soften a verification
requirement into a reassurance — if something needs checking before purchase, the
homeowner must finish reading knowing that.

Write 2-4 sentences in plain language. No marketing adjectives, no exclamation marks,
no "perfect" or "ideal" or "dream bathroom".

Computed result:
{result}
```

---

## Conflict explanation — why nothing satisfied the brief

**Registry key:** `conflict_explanation`

**Where it runs:** Defined in the registry as the contract for narrating a conflict. **Not currently called**: `backend/recommendation/engine.py` returns the violations, closest alternatives and evaluated relaxations as structured data, and the UI renders those directly.

```text
The planning engines could not find any configuration satisfying
all of the user's requirements. Explain this to them.

Be direct about what could not be done and why. Do not apologise repeatedly. Do not
suggest a workaround the engines did not list — the listed relaxations are the only
options that have actually been evaluated.

Finish by presenting the available options as a genuine choice. The user decides which
constraint gives way; you are not choosing for them.

What was requested and what blocked it:
{conflict}
```

---

## Vision system role — photograph to structured evidence

**Registry key:** `vision_system`

**Where it runs:** `backend/vision/provider.py` via `backend/vision/prompt.py`, sent as `system_instruction` with a structured `response_schema` of `BathroomVisionEvidence`.

```text
You are the computer-vision spatial inspection specialist for KOHLER AI BathPlan.
Your sole mission is to analyze single-perspective bathroom photographs and extract structured, conservative spatial evidence.

OPERATIONAL BOUNDARIES:
- Extract ONLY observable surface evidence.
- Do not make fixture recommendations, layout decisions, or structural guarantees.
- Bounding box coordinates must be normalized to [0.0, 1.0] relative to image dimensions.
- Mirror reflections must never be labeled as primary fixtures. If a fixture is only visible inside a mirror reflection, put it in ambiguous_objects.
- A single 2D photograph cannot determine room dimensions, rough-ins, hidden piping, or wall structure.
- Every unverifiable_attributes item must have status "unknown" and verification_required true.
- Output must conform strictly to the BathroomVisionEvidence schema.

Inspect the image for visible toilets, sinks, vanities, showers, bathtubs, doors, windows, mirrors, cabinets, and obstacles. Identify approximate functional zones, occlusions, visual ambiguities, and missing spatial boundaries. Return JSON only.
```

---

## Failure handling

Every language-model call in this system is wrapped, and every one of them has a
deterministic path behind it.

| Call | Failure mode | What happens |
|---|---|---|
| Intent extraction | timeout, network error, malformed JSON, schema violation | Caught in `backend/llm/agent.py::interpret`; falls through to `extract_intent_keywords`, a regex parser that handles every phrasing in the demo script. The user sees a result, and the response records `interpretation_source: "deterministic_keywords"` so the substitution is visible rather than hidden. |
| Intent extraction returns an unknown category | model invents a product category | `ModificationIntent.sanitised()` drops anything outside the fixed vocabulary before it reaches the planner. |
| Vision analysis | no API key, flag disabled | `backend/vision/api.py` answers 503 with a plain advisory before the upload is read. Planning, impact analysis, versioning and export are unaffected. |
| Vision analysis | provider error, malformed response | 502 with an advisory. `BathroomVisionEvidence` validation rejects anything that does not conform, including any attempt to set `authoritative: true`. |
| Any of the above | — | The deterministic planner has no language-model dependency at all. With no key configured the entire product works except image analysis. |

## Structured output requirements

Both live calls request structured output rather than free text:

- **Intent extraction** — `response_mime_type="application/json"`, `response_schema=ModificationIntent`, `temperature=0.0`. The result is validated by Pydantic, then sanitised against a fixed category vocabulary, then applied *deterministically* to the brief. The model produces a request; it never produces a result.
- **Vision** — `response_mime_type="application/json"`, `response_schema=BathroomVisionEvidence`. `authoritative` is a `Literal[False]` in the schema, so a response asserting authority fails validation. Every field in `unverifiable_attributes` is typed `status: Literal["unknown"]` and `verification_required: Literal[True]`, so the model cannot downgrade an unknown into a fact.

## What the model is never allowed to produce

Stated in the system prompt, and enforced by architecture rather than by the prompt alone:

| Quantity | Produced by | Enforcement |
|---|---|---|
| Whether a fixture fits | `backend/layout/solver.py` | The model is never called during planning. |
| Feasibility verdict | `backend/constraints/engine.py` | Same. |
| Price and price totals | `catalog/products.json`, summed in Python | Same. |
| Dimensions | `catalog/products.json` | A size *request* is resolved to a catalog product by `backend/designpulse/resolve.py`; a width the catalog does not have is reported as absent. |
| Water figures | `backend/sustainability/calculator.py` | Same. |
| Trade-off options | `backend/designpulse/tradeoffs.py` | Each is run through the constraint engine before being offered. |
