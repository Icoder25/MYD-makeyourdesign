# KOHLER AI BathPlan — Innovation Gap

## Strategic framing

The innovation gap is the intersection of:

`KOHLER product ecosystem`
+
`customer configuration uncertainty`
+
`limitations of image-first AI`
+
`LLM reasoning`
+
`deterministic computation`
+
`48-hour implementation reality`

The objective is not to invent a new foundation model. It is to create a new **decision workflow** using existing AI capabilities.

---

# 10+ innovation directions

| # | Direction | User value | Technical novelty | KOHLER relevance | Difficulty | Demo impact | Risk |
|---|---|---|---|---|---|---|---|
| 1 | Constraint-aware KOHLER configuration agent | High | High | Very high | Medium | Very high | Medium |
| 2 | Impossible-request detection + repair | Very high | High | Very high | Low-Medium | Very high | Low |
| 3 | Conversational re-optimization | Very high | High | Very high | Medium | Very high | Medium |
| 4 | Budget trade-off engine | High | Medium-High | High | Medium | High | Low |
| 5 | Water-impact optimizer | High | Medium | Very high | Low-Medium | High | Medium |
| 6 | “Why rejected?” product reasoning | Medium-High | Medium | High | Low | High | Low |
| 7 | Requirement-to-configuration compiler | High | High | High | Medium | High | Medium |
| 8 | Confidence/assumption layer | Medium | Medium | High | Low | Medium | Low |
| 9 | Multi-objective bathroom optimizer | High | High | Very high | Medium | High | Medium |
| 10 | Constraint heatmap on 2D layout | Medium-High | Medium | High | Medium | High | Low |
| 11 | Designer handoff package | Medium-High | Medium | Very high | Low-Medium | Medium | Low |
| 12 | “What changed?” explanation engine | High | Medium | High | Low | High | Low |
| 13 | Product substitution graph | High | Medium-High | High | Medium | High | Medium |
| 14 | Evidence-linked recommendation cards | Medium | Medium | High | Low | Medium | Low |

---

# Direction details

## 1. Constraint-aware KOHLER configuration agent

### User value
Turns an ambiguous renovation request into a set of feasible product configurations.

### Technical idea
LLM → structured requirements → candidate generator → deterministic validator → optimizer → explanation.

### Why it matters
This becomes the core product architecture rather than a visual gimmick.

### 48-hour feasibility
High if the product catalog is deliberately curated.

---

## 2. Impossible-request detection + repair

Example:

> Available vanity wall = 42 in  
> User requests vanity = 48 in

System:

> “48 in does not fit the declared wall width. I can keep the larger vanity only by changing the wall/fixture assumption. If you want to preserve the current room, I recommend the 36–42 in class.”

### Why it is powerful
Judges can immediately see that the AI cannot simply hallucinate its way through a constraint.

### 48-hour feasibility
Very high.

---

## 3. Conversational re-optimization

Example:

> User: “Make it cheaper.”

The system should:
1. preserve hard constraints
2. identify adjustable soft objectives
3. substitute products/layout
4. recompute total cost
5. rerun validation
6. explain the delta

Example output:

`₹1.98L → ₹1.69L`

Then:

- what changed
- what stayed
- water impact delta
- aesthetic delta
- validation status

This is substantially stronger than a chatbot saying “Sure, here's a cheaper option.”

---

## 4. Budget trade-off engine

Treat budget as a constraint plus optimization objective.

Possible utility:

`Score = style + storage + water_efficiency + smart_features + user_priority_weights`

Subject to:

`total_price <= budget`

Do not let the LLM perform the arithmetic.

---

## 5. Water-impact optimizer

Use transparent assumptions.

For example:

`daily_water = fixture_use_rate × uses_per_day`

Then:

`annual_water = daily_water × 365`

Compare:
- selected configuration
- baseline configuration

Always display:
- source
- assumption
- estimated value
- uncertainty

Never present manufacturer “up to” claims as guaranteed household savings.

---

## 6. Why-rejected reasoning

Store rejection codes:

```text
WALL_WIDTH_EXCEEDED
BUDGET_EXCEEDED
MISSING_MUST_HAVE
INSTALLATION_UNKNOWN
COMPATIBILITY_UNKNOWN
```

Then let the LLM translate those codes into natural language.

This gives explainability without letting the LLM invent the reason.

---

## 7. Requirement-to-configuration compiler

Convert:

> “Modern, under ₹2 lakh, large storage, walk-in shower, low water use”

into structured JSON.

Example:

```json
{
  "budget_max": 200000,
  "style": ["modern", "minimal"],
  "must_have": ["walk_in_shower"],
  "priorities": {
    "storage": 0.9,
    "water_efficiency": 0.9,
    "style": 0.7
  }
}
```

The rest of the system operates on this structured representation.

---

## 8. Confidence / assumption layer

Every critical fact gets:
- verified
- assumed
- unknown

The UI can expose:

> “Plumbing location not verified — concept only.”

This is important because bathroom installation is a high-consequence physical domain.

---

## 9. Multi-objective optimizer

The system can generate:
- Cost-first
- Balanced
- Water-first

But they must not be three random LLM answers.

Each is produced by different weights over the same validated candidate space.

---

## 10. Constraint heatmap

Simple 2D visualization:
- green = valid placement
- red = collision/clearance issue
- yellow = assumption/unknown

This makes the deterministic engine visible to the judge.

---

## 11. Designer handoff package

Generate:
- room dimensions
- preferences
- chosen configuration
- product list
- assumptions
- unresolved constraints
- budget
- sustainability estimate

This makes BathPlan complementary to KOHLER's existing design service.

---

## 12. “What changed?” engine

After every conversational modification:

`Before → After`

Show:
- product changes
- cost change
- water change
- layout change
- constraint status

This creates a tangible feedback loop.

---

## 13. Product substitution graph

If a selected product becomes invalid, find alternatives sharing:
- category
- installation type
- collection/style
- size class
- efficiency class

Then validate substitutes.

---

## 14. Evidence-linked recommendations

Each product card can show:
- source
- dimensions
- price verification date
- efficiency attribute
- compatibility group

This reduces hallucination risk.

---

# Recommended thesis

## FINAL

> **KOHLER AI BathPlan is a constraint-aware bathroom decision agent that converts a customer's space, budget and priorities into validated KOHLER configurations, then continuously re-optimizes the configuration when the customer changes a trade-off.**

Supporting principle:

> **Generative AI proposes. Deterministic systems validate. The user controls the trade-offs.**

---

# Why this thesis is defensible

### 1. It does not depend on claiming competitors are primitive
Planner 5D and others already handle substantial planning/constraint functionality.

### 2. It is KOHLER-specific
The value comes from real KOHLER product attributes, collections, installation classes, water-efficiency attributes and product evidence.

### 3. It makes the agent's reasoning operational
The agent must cause a configuration change and pass the configuration through validation again.

### 4. It fits the competition time limit
The catalog can be curated to 30–80 products. The validator can be rule-based. The optimizer can be small and deterministic.

### 5. It can be visibly demonstrated
The judge does not need to trust a backend architecture diagram. They can see an impossible request fail and a valid alternative appear.

---

# 90–120 second judge demo

## 0–15 sec — Input

Upload bathroom image.

Enter:
- room = 6 × 8 ft
- budget = ₹2 lakh
- style = modern minimalist
- must-have = walk-in shower
- priority = storage + water efficiency

## 15–30 sec — Understanding

System shows structured requirements.

Example:

> “I understood: ₹2L maximum, modern, walk-in shower required, high storage priority, water efficiency important.”

## 30–50 sec — Initial plans

Generate 3 validated options:

### Cost-first
Lower cost, meets hard constraints.

### Balanced
Balances style/storage/water.

### Water-first
Higher efficiency, potentially different product choices.

Each shows:
- products
- total price
- validation status
- water estimate

## 50–75 sec — Killer moment

User:

> “Make the vanity 48 inches.”

System detects:

`available_wall = 42 in`
`requested_width = 48 in`

Result:

> “Not feasible under the current room constraint.”

Then proposes:
- smaller vanity
- alternate wall
- reduce another fixture footprint

## 75–100 sec — Trade-off

User:

> “Keep the shower. Make it cheaper.”

System changes actual products/layout and returns:

`₹1.98L → ₹1.69L`

with:
- replaced products
- savings
- water delta
- unchanged must-haves
- revalidated status

## 100–120 sec — Final

Show:

> **Validated KOHLER Bathroom Configuration**

with:
- 2D layout
- product list
- budget
- validation
- water estimate
- assumptions

---

# What judges should remember

Not:

> “They made an AI bathroom image.”

But:

> **“The AI actually had to solve a constrained bathroom configuration and explain what changed when I changed the requirements.”**
