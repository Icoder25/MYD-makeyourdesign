# KOHLER AI BathPlan --- Product Specification

> **Competition context:** Individual submission for the **KOHLER
> MIT-WPU AI Research Lab --- Track 1: KOHLER AI Bathroom Designer &
> Planner**.
>
> **Time constraint:** Approximately 48 hours.
>
> **Purpose of this file:** This is the implementation-facing product
> specification. It defines exactly what we are building, why it exists,
> what is in/out of scope, the product behavior, technical requirements,
> validation philosophy, and MVP acceptance criteria. It is
> intentionally narrow so the team does not waste the 48-hour window
> rebuilding commodity AI interior-design features.

## 1. Product

### Working name

**KOHLER AI BathPlan**

### One-line thesis

> **An AI bathroom planning agent that turns space, budget, style and
> preferences into validated bathroom options, then explains the
> trade-offs behind each recommendation.**

### Core product promise

Most AI design tools optimize for visual output. BathPlan should
optimize for **decision quality under constraints**.

The user should be able to say:

> "I have a 6 × 8 ft bathroom, a ₹2 lakh budget, want a modern
> minimalist look, a walk-in shower, good storage, and lower water use."

BathPlan should:

1.  Convert natural-language intent into structured requirements.
2.  Retrieve appropriate KOHLER products from a curated product
    knowledge base.
3.  Generate candidate configurations.
4.  Validate those configurations against deterministic rules.
5.  Reject invalid configurations rather than hallucinating feasibility.
6.  Compare valid alternatives.
7.  Explain cost, space, preference and sustainability trade-offs.
8.  Allow conversational modification and re-validation.

------------------------------------------------------------------------

# 2. Problem Definition

Bathroom renovation is a multi-objective decision problem involving:

-   physical space
-   fixture dimensions
-   existing fixture/plumbing constraints
-   budget
-   aesthetics
-   comfort
-   storage
-   product compatibility
-   sustainability
-   installation considerations

The current customer journey is fragmented:

**inspiration → measurements → product research → layout planning →
expert consultation → pricing → revision → purchase**

KOHLER already supports parts of this journey through human design
services, product catalogs, smart products and sustainability
information. Competitors also provide visualization and AI planning.

Therefore, the product is **not**:

> "AI that can design a pretty bathroom."

The product is:

> **"AI that can reason over bathroom requirements and make
> recommendations that are explicitly validated and explainable."**

------------------------------------------------------------------------

# 3. Target User

## Primary MVP user

A homeowner / renovator who:

-   has a bathroom to renovate
-   knows approximate dimensions
-   has a budget
-   has style preferences
-   does not know which products/configuration to choose
-   wants rapid exploration before speaking with a professional

## Secondary future users

-   KOHLER showroom visitors
-   KOHLER design-service leads
-   interior designers
-   architects/specifiers
-   contractors
-   hospitality/property developers

Do **not** attempt to support all personas in the MVP.

------------------------------------------------------------------------

# 4. Product Positioning

### Existing tools

Many competitors already provide:

-   image-to-design
-   2D planning
-   3D visualization
-   generic furniture/fixture libraries
-   AI-generated room designs
-   conversational design in some cases

### KOHLER opportunity

KOHLER has:

-   a real bathroom product ecosystem
-   product specifications
-   smart bathroom products
-   sustainability-oriented products
-   design experts and design services
-   customer-facing product browsing

BathPlan should act as an **intelligent decision layer between customer
intent and the KOHLER ecosystem**.

------------------------------------------------------------------------

# 5. Core User Journey

``` text
User starts project
       ↓
Enter bathroom dimensions
       ↓
Enter existing conditions
       ↓
Enter budget
       ↓
Choose style + priorities
       ↓
AI converts input → structured requirements
       ↓
Retrieve candidate KOHLER products
       ↓
Generate candidate layouts/configurations
       ↓
Deterministic constraint validation
       ↓
Remove invalid configurations
       ↓
Rank remaining valid options against user priorities
       ↓
Generate explanations + trade-offs
       ↓
Show 3 options
       ↓
User says “make it cheaper / greener / more storage”
       ↓
Re-optimize
       ↓
Re-validate
       ↓
Return updated plan
```

------------------------------------------------------------------------

# 6. MVP Feature Requirements

## P0 --- Required

### 6.1 Bathroom requirements intake

Inputs:

-   length
-   width
-   optional ceiling height
-   door location / opening
-   window location if known
-   existing fixture locations if known
-   budget
-   style
-   must-have features
-   priorities

Example:

``` json
{
  "space": {
    "length_ft": 8,
    "width_ft": 6
  },
  "budget": 200000,
  "currency": "INR",
  "style": "modern_minimalist",
  "must_have": [
    "walk_in_shower"
  ],
  "priorities": [
    "budget",
    "water_efficiency",
    "storage"
  ]
}
```

### 6.2 Natural-language requirement parsing

The LLM converts conversational input into structured requirements.

The parsed requirements should be inspectable/debuggable during
development.

### 6.3 Curated KOHLER product knowledge base

Target:

**30--80 carefully selected products**, not the entire catalog.

Suggested categories:

-   toilets
-   smart toilets
-   faucets
-   shower systems
-   digital showers
-   vanities
-   sinks
-   bathtubs/accessories where relevant

Suggested fields:

``` text
product_id
name
category
collection
price
currency
width
depth
height
installation_type
style
finish
water_usage
water_efficiency
smart_features
compatibility
source_url
confidence
```

### 6.4 Deterministic constraint engine

The constraint engine must be independent from the LLM.

Examples:

``` text
IF fixture_width > available_wall_width
    INVALID

IF fixture_depth > available_depth
    INVALID

IF estimated_total > budget
    INVALID

IF must_have_feature is unsupported
    INVALID

IF required clearance < defined project rule
    INVALID
```

The exact rules must be explicitly documented.

### 6.5 Recommendation engine

Generate candidate configurations from:

-   user requirements
-   product attributes
-   spatial constraints
-   budget
-   preferences

Do not rely on an LLM "score" without an auditable formula.

A practical MVP can use weighted deterministic scoring:

``` text
fit_score =
    style_match
    + budget_fit
    + space_fit
    + sustainability_fit
    + preference_match
```

The exact weights should be configurable.

### 6.6 Three-option output

Return:

1.  **Budget-focused**
2.  **Balanced**
3.  **Sustainability / experience-focused**

These labels describe optimization objectives, not "best/worst"
rankings.

Each option shows:

-   estimated cost
-   products
-   layout concept
-   style rationale
-   constraint status
-   sustainability metrics
-   trade-offs

### 6.7 Trade-off explanation

Example:

> "Moving from a 36-inch to a 48-inch vanity increases storage but
> reduces available shower width by approximately 6 inches in this
> configuration."

The explanation must be based on actual changed variables.

### 6.8 Conversational modification

Supported examples:

-   "Make it cheaper."
-   "Prioritize water efficiency."
-   "Give me more storage."
-   "I want a larger shower."
-   "Keep the same style."
-   "Replace the smart toilet."
-   "Stay under ₹1.5 lakh."

Every modification must trigger:

**new requirements → new recommendation → validation**

### 6.9 Sustainability estimate

At minimum:

-   product-level water-efficiency attributes
-   estimated annual water use where source data supports calculation
-   comparison against a defined baseline
-   explicit assumptions

Do not claim full lifecycle carbon accounting in the MVP.

### 6.10 Final bathroom plan

The final result should contain:

``` text
Bathroom summary
Dimensions
Budget
Design intent

Recommended configuration
Product list
Estimated cost

Constraint checks
✓ Space
✓ Budget
✓ Must-have requirements

Trade-offs
...

Sustainability
...

Assumptions / limitations
...

Next steps
...
```

------------------------------------------------------------------------

# 7. Optional P1 Features

Only implement these if P0 is stable.

### P1.1 Simple 2D visualization

A lightweight top-down diagram showing:

-   walls
-   door
-   shower
-   toilet
-   vanity

It does not need CAD precision.

### P1.2 Image input

Optional photo upload for context/style recognition.

The image should **not** be treated as an authoritative measurement
source in the MVP.

### P1.3 AI-generated concept rendering

Only as a visual layer.

The generated image must be clearly separated from validated layout
data.

------------------------------------------------------------------------

# 8. Explicitly Out of Scope

Do not build:

-   full CAD editor
-   AR bathroom placement
-   engineering-grade plumbing simulation
-   building-code certification
-   electrical compliance certification
-   automated LiDAR scanning
-   full KOHLER inventory integration
-   real-time inventory synchronization
-   checkout/payment
-   installation booking
-   contractor marketplace
-   full room photogrammetry
-   autonomous web shopping
-   complete 3D modeling engine
-   full lifecycle environmental assessment
-   generalized home-design assistant

These are scope traps for a 48-hour competition.

------------------------------------------------------------------------

# 9. Trust Architecture

The most important technical design principle:

> **LLM proposes. Deterministic systems validate.**

``` text
                 USER
                   ↓
             LLM / Agent
                   ↓
       Structured Requirements
                   ↓
          Product Retrieval
                   ↓
         Candidate Generator
                   ↓
        ┌────────────────────┐
        │ Constraint Engine  │
        └─────────┬──────────┘
                  ↓
           Valid Candidates
                  ↓
          Recommendation
                  ↓
        Trade-off Calculator
                  ↓
            Explanation
                  ↓
              USER
```

The LLM must not be the source of truth for:

-   dimensions
-   prices
-   product existence
-   water specifications
-   feasibility

Those must come from structured data/rules.

------------------------------------------------------------------------

# 10. Technical Architecture

## Frontend

Recommended:

-   Next.js
-   React
-   Tailwind CSS
-   shadcn/ui

Primary screens:

1.  Project intake
2.  Requirements summary
3.  Candidate plans
4.  Plan details / trade-offs
5.  Conversational refinement

## Backend

Recommended:

-   FastAPI
-   Python
-   Pydantic

Core modules:

``` text
backend/
├── api/
├── schemas/
├── products/
│   └── kohler_products.json
├── constraints/
│   ├── spatial.py
│   ├── budget.py
│   └── requirements.py
├── recommendation/
│   └── engine.py
├── sustainability/
│   └── calculator.py
├── agent/
│   └── orchestrator.py
└── tests/
```

## Data

For MVP:

-   JSON or Postgres is sufficient.
-   Supabase/Postgres can be used if already available.

Do not introduce a vector database unless retrieval complexity actually
requires it.

------------------------------------------------------------------------

# 11. AI Agent Responsibilities

The AI agent should:

1.  Ask for missing critical information.
2.  Interpret natural-language preferences.
3.  Convert them into structured requirements.
4.  Retrieve relevant product candidates.
5.  Call deterministic planning/validation functions.
6.  Explain valid options.
7.  Ask for a priority when trade-offs cannot be resolved automatically.
8.  Re-run the planning process after user changes.

The AI agent should **not**:

-   invent product IDs
-   invent prices
-   decide physical feasibility without rules
-   claim building-code compliance
-   manufacture sustainability figures
-   silently override hard user constraints

------------------------------------------------------------------------

# 12. Constraint Model

Separate constraints into:

## Hard constraints

Must never be violated:

-   room dimensions
-   fixture dimensions
-   defined clearances
-   budget ceiling
-   explicit must-have features
-   known existing fixture/plumbing constraints

## Soft constraints

Can be traded off:

-   style similarity
-   storage
-   water efficiency
-   luxury
-   shower size
-   vanity size
-   smart features

This allows the system to solve a real optimization problem instead of
pretending there is one perfect bathroom.

------------------------------------------------------------------------

# 13. Sustainability Model

Use transparent calculations.

Example:

``` text
annual_water_use =
    usage_per_event
    × events_per_day
    × household_size
    × 365
```

For showering:

``` text
water =
    flow_rate
    × duration
    × events
```

For toilets:

``` text
water =
    flush_volume
    × flushes_per_day
    × household_size
    × 365
```

Only use values available in the product dataset.

For products such as Anthem EvoCycle, use KOHLER's stated product-level
water-saving claim and preserve its wording/assumptions rather than
converting it into an unsupported universal lifecycle claim.

------------------------------------------------------------------------

# 14. Safety / Accuracy Boundary

The product is a **planning assistant**, not a licensed architectural,
plumbing, electrical or construction authority.

Every final plan should contain a short limitation:

> "This concept is preliminary planning guidance. Final dimensions,
> plumbing, electrical, structural and local-code requirements should be
> verified by a qualified professional before installation."

------------------------------------------------------------------------

# 15. 48-Hour Build Priority

## Hours 0--4

-   freeze PRD
-   collect product dataset
-   define rules
-   define demo scenario

## Hours 4--10

-   product data
-   schemas
-   constraint engine
-   tests

## Hours 10--17

-   recommendation engine
-   sustainability calculator
-   trade-off calculator

## Hours 17--25

-   AI orchestrator
-   structured output
-   tool/function calling

## Hours 25--34

-   frontend
-   plan cards
-   validation display
-   conversational controls

## Hours 34--40

-   simple visualization
-   polish

## Hours 40--44

-   adversarial testing
-   hallucination testing
-   impossible-input testing

## Hours 44--48

-   demo hardening
-   presentation
-   architecture diagram
-   final documentation

------------------------------------------------------------------------

# 16. MVP Acceptance Criteria

The MVP is complete only if:

### Input

-   [ ] User can specify room dimensions.
-   [ ] User can specify budget.
-   [ ] User can specify style.
-   [ ] User can specify priorities.
-   [ ] User can specify must-have requirements.

### AI

-   [ ] Natural language is converted into structured requirements.
-   [ ] Missing critical inputs are requested.
-   [ ] Product recommendations come from the product dataset.

### Validation

-   [ ] Every proposed configuration passes the deterministic validator.
-   [ ] Invalid configurations are rejected.
-   [ ] Budget violations are detected.
-   [ ] Defined spatial violations are detected.
-   [ ] Must-have violations are detected.

### Recommendation

-   [ ] At least three valid options can be generated for the demo
    scenario.
-   [ ] Options expose meaningful trade-offs.
-   [ ] Product selections are traceable to product data.

### Sustainability

-   [ ] Water-related assumptions are visible.
-   [ ] Calculations are reproducible.
-   [ ] No unsupported environmental claims are generated.

### Conversation

-   [ ] User can request at least three modification types.
-   [ ] Each modification causes re-optimization.
-   [ ] The modified result is revalidated.

### Demo

-   [ ] A deliberately impossible request produces "no feasible
    solution" rather than a hallucinated design.
-   [ ] The system can explain why an option changed after a user
    constraint changed.

------------------------------------------------------------------------

# 17. Definition of Success

The judge should leave with this mental model:

> **"This isn't another AI bathroom image generator. It is a planning
> agent with a deterministic constraint layer and real KOHLER product
> intelligence."**

That is the product we are building.
