# KOHLER AI BathPlan — UI/UX Design Specification

> **Product:** KOHLER AI BathPlan  
> **Tagline:** Imagine. Plan. Live Better.  
> **Primary experience:** AI-assisted bathroom planning and design for homeowners and professional designers.

---

## 1. Product Design Vision

KOHLER AI BathPlan is a **bathroom-specific design decision system**, not a generic AI chatbot.

The interface should help users move from an empty/uncertain bathroom brief to a feasible, explainable, product-ready design through a clear workflow:

**Brief → Design → Refine → Finalize**

The product combines:

- AI-assisted requirement understanding
- Structured bathroom planning
- Deterministic feasibility and compatibility validation
- KOHLER product discovery
- DesignPulse™ impact analysis
- Sustainability insights
- 2D / 3D / 360° / AR visualization
- Versioning and decision history
- Export and sharing

### Core UX promise

> **Describe your space. Define your style. Explore possibilities. Understand the impact of every change. Finalize with confidence.**

---

## 2. Core Product Principle

### AI is not the source of truth

The UI must communicate a clear separation between:

| Layer | Responsibility |
|---|---|
| **AI** | Understand intent, ask clarifying questions, summarize preferences, explain recommendations, orchestrate workflows |
| **Deterministic engine** | Dimensions, clearances, feasibility, compatibility, budget calculations, sustainability calculations, impact analysis |
| **Vision** | Observe visible elements and approximate locations with uncertainty labels |
| **Catalog** | Product facts, specifications and supported product data |
| **User** | Confirms measurements, assumptions and unknowns |

The interface must never imply that an AI-generated image or computer vision result is an engineering measurement.

---

## 3. UX North Star

Every major decision should help the user understand:

1. **What am I changing?**
2. **Why is it being suggested?**
3. **Is it feasible?**
4. **What else changes?**
5. **What stays unchanged?**
6. **What does it cost?**
7. **What do I need to verify?**
8. **What will it look like?**

The UI should minimize long AI conversations and instead use **contextual assistance** near the decision being made.

---

# 4. Primary User Modes

## 4.1 Homeowner Mode

Designed for users with little or no bathroom-design knowledge.

The experience should:

- use plain language
- ask one logical question at a time during onboarding
- explain technical terms only when necessary
- allow unknown optional information
- provide visual examples
- keep advanced specifications hidden until useful
- focus on confidence and understandable trade-offs

### Guided onboarding

**Step 1 — Space**

> How big is your bathroom?

Fields:

- Length
- Width
- Height (optional)

Optional:

- Upload floor plan
- Upload sketch
- Upload bathroom photo

**Step 2 — Entrance & openings**

- Door location
- Door swing
- Window location
- Window size (optional)

**Step 3 — What do you want?**

- Shower
- Bathtub
- Toilet
- Vanity
- Storage
- Mirror
- Other

**Step 4 — Style**

- Modern
- Minimal
- Luxury
- Natural
- Traditional
- Custom

**Step 5 — Budget & priorities**

- Budget range
- Storage priority
- Open-space priority
- Accessibility priority
- Sustainability priority
- Smart-home priority

---

## 4.2 Designer Mode

Expose additional information without changing the core workflow.

Designer mode can reveal:

- exact dimensions
- clearances
- product specifications
- compatibility checks
- assumptions
- verification requirements
- price sources/assumptions
- design versions
- comparison tools
- detailed exports

**Homeowner Mode and Designer Mode must use the same underlying DesignState and validation logic.**

---

# 5. Application Shell

## Desktop target

Primary reference width:

**1440–1600px**

Suggested minimum desktop width:

**1280px**

### Main structure

```text
┌──────────────┬─────────────────────────────────────────────────────────────┐
│              │  Project Header / Workflow                                 │
│   Sidebar    ├─────────────────────────────────────────────────────────────┤
│              │                                                             │
│              │                        Main Workspace                      │
│              │                                                             │
│              ├─────────────────────────────────────────────────────────────┤
│              │  DesignPulse │ Sustainability │ Visualization │ Export     │
└──────────────┴─────────────────────────────────────────────────────────────┘
```

### Three-column design workspace

```text
┌──────────────┬────────────────────────────────┬────────────────────────────┐
│ Space Input  │                                │ Products in this Design    │
│              │          Design Canvas         │                            │
│ Dimensions   │                                │ Product cards              │
│ Entrance     │          2D / 3D / AR          │ Product specs              │
│ Preferences  │                                │ Catalog access              │
│              │                                │                            │
└──────────────┴────────────────────────────────┴────────────────────────────┘
```

Suggested visual proportions inside the main workspace:

- Left control panel: **22–26%**
- Central design canvas: **45–52%**
- Right product panel: **24–30%**

The central canvas is the visual focal point.

---

# 6. Sidebar

Width target:

**210–230px**

### Brand block

```text
KOHLER
AI BathPlan
Imagine. Plan. Live Better.
```

### Navigation

- Home
- New Project
- My Designs
- Inspiration
- Product Catalog
- DesignPulse™
- Sustainability
- Export & Share

### Bottom account area

- Avatar
- Name
- Role: Homeowner / Designer
- Settings

### Sidebar behavior

- Fixed on desktop
- Collapsible on tablet
- Drawer on mobile
- Active route uses a strong dark navy pill/rounded container
- Inactive items remain visually quiet

The sidebar should never compete with the bathroom canvas.

---

# 7. Global Header

The header contains the product workflow.

### Progress navigation

```text
① Brief ───── ② Design ───── ③ Refine ───── ④ Finalize
```

Each stage should contain:

- step number/status
- title
- short description

Example:

```text
Brief
Tell us about your space

Design
AI plans your layout

Refine
Explore options

Finalize
Export & bring to life
```

### Right side controls

- Search
- Help
- Save Project
- Autosave status

Example status:

> ✓ Saved just now

---

# 8. Project Summary Card

Use a compact contextual card rather than a large dashboard block.

### Example

```text
PROJECT
Modern Serenity

Room Size
2.4m × 1.8m · 4.32 m²

Budget
₹2,50,000 – ₹4,00,000

Style
Modern Minimal

Entrance
Left Wall · Inward

STATUS
● Design Ready
```

Include an edit icon for quick modifications.

---

# 9. Contextual Hero

A premium bathroom image can establish the design mood, but the hero must remain compact so that the application feels like a **working product**, not a marketing landing page.

### Suggested copy

> **Your Dream Bathroom, Designed with Intelligence**

Supporting copy:

> Enter your space, explore beautiful designs, and make confident decisions with DesignPulse™.

### Hero rules

- One strong image
- Strong readable contrast
- No excessive overlay text
- Avoid full-screen hero behavior
- Keep the working interface immediately visible

---

# 10. Space Input Panel

Title:

**SPACE INPUT**

Tabs:

- Dimensions
- Entrance
- Preferences

### Dimensions

```text
Length
[ 2.4 m ]

Width
[ 1.8 m ]

Height (optional)
[ 2.4 m ]
```

### Floor-plan upload

```text
┌─────────────────────────────┐
│        Upload Floor Plan     │
│                             │
│ PNG, JPG or PDF · Max 10MB  │
└─────────────────────────────┘
```

Supporting text:

> You can also upload a floor plan or sketch and our AI will help extract measurements.

CTA:

**Next: Entrance →**

Unknown optional information should never require fabricated input.

---

# 11. Design Canvas

The design canvas is the core of the application.

### Tabs

```text
[ 2D Plan ] [ 3D View ] [ 360° View ] [ AR Preview ]
```

## 11.1 2D Plan

This represents the spatial/engineering truth of the design.

Show:

- wall boundaries
- room dimensions
- door location
- door swing
- windows
- shower
- toilet
- vanity
- mirror
- storage
- fixture locations
- circulation zones

Use architectural symbols and dimension annotations.

### Canvas controls

- Zoom in
- Zoom out
- Fit to screen
- Fullscreen
- Orientation/north indicator where appropriate

The plan should feel like a real architectural planning workspace rather than a decorative diagram.

---

# 12. 3D / 360° / AR

## 3D View

Purpose:

- visual composition
- materials
- product appearance
- spatial understanding

## 360° View

Purpose:

- exploration
- immersive presentation

## AR Preview

Purpose:

- contextual preview in the user's physical environment

### Trust rule

3D/360/AR are **visualization aids**, not engineering verification.

Use subtle language such as:

> Preview only — confirm dimensions and site conditions before installation.

---

# 13. Product Panel

Title:

**PRODUCTS IN THIS DESIGN (4)**

Each product card contains:

- product image
- product name
- price
- compact compatibility/status signal
- contextual menu

Example:

```text
┌───────────────────────┐
│       Product image   │
│                       │
└───────────────────────┘
Veil Wall-Hung Toilet
₹48,000
✓ Compatible
```

Additional cards can include:

- Shower System
- Vanity
- Mirror
- Bathtub
- Faucet
- Storage

CTA:

**Explore Full Catalog →**

### Product interaction

Selecting a product should:

1. highlight the corresponding element on the plan
2. open contextual product details
3. display known compatibility information
4. expose relevant trade-offs
5. allow replacement/comparison

---

# 14. DesignPulse™

DesignPulse is a defining product interaction and must be visually discoverable on the main workspace.

### Headline

**Make a change. See the full impact.**

Example interaction:

```text
Try:
“Increase vanity width”

[ → ]
```

### Impact presentation

```text
VANITY
750mm → 900mm

CIRCULATION
−50mm

MIRROR
Requires resize

STORAGE
+12%

BUDGET
+₹8,000

FEASIBILITY
✓ Valid
```

### Unchanged section

```text
UNCHANGED
✓ Toilet position
✓ Shower location
✓ Entrance
```

### Alternative

> 850mm vanity gives more circulation space while increasing storage over the current design.

Actions:

- Apply Change
- Compare
- Keep Current

### UX goal

DesignPulse should answer:

> **“If I change this, what else changes?”**

It must not resemble a generic AI chat panel.

---

# 15. Sustainability Card

Title:

**SUSTAINABILITY**

Primary metric example:

```text
Estimated Water Savings
32%
██████████████░░░░
Compared to standard fixtures
```

Possible supporting metrics:

- estimated water use
- fixture efficiency
- annual estimated savings
- sustainability considerations

The card should be simple enough for a homeowner to understand while allowing expansion into detailed metrics.

Avoid presenting unsupported precision as fact.

---

# 16. Visualization Card

Title:

**VISUALIZATION**

Copy:

> Explore your bathroom in immersive 3D.

Include:

- preview image
- play/launch affordance
- 360° indicator
- AR action

Primary CTA:

**Open 3D View**

Secondary CTA:

**Launch AR**

---

# 17. Export & Share

Title:

**EXPORT & SHARE**

Copy:

> Generate professional outputs.

Actions:

- Download 2D Plan PDF
- Export Product List PDF
- Share Design Link
- Save Design
- Duplicate Version
- Compare Versions

Export status should be explicit:

- Preparing
- Generating
- Complete
- Failed

Errors must provide recovery actions.

---

# 18. Decision & Validation Ledger

The ledger is a persistent, collapsible transparency layer.

### Domains

```text
FEASIBILITY
✓ Layout feasible

BUDGET
₹3.02L estimated

SPACE
✓ Required clearances

PRODUCT COMPATIBILITY
✓ Checked

ASSUMPTIONS
2

VERIFICATION REQUIRED
3

UNKNOWN
Plumbing location

SUSTAINABILITY
32% estimated water saving
```

### Important distinction

**Verification required ≠ constraint failure.**

A missing piece of site information must be represented as uncertainty, not incorrectly treated as an infeasible design.

---

# 19. Trust & Uncertainty Language

Use compact status labels where they improve decision quality.

| Status | Meaning |
|---|---|
| **Confirmed** | Supplied or explicitly confirmed by user |
| **Observed** | Visible in uploaded image |
| **Estimated** | Approximate AI-derived interpretation |
| **Unknown** | Not available from current information |
| **Verify** | Requires physical/on-site confirmation |

Recommended visual notation:

- ✓ Confirmed
- ◌ Observed
- ≈ Estimated
- ? Unknown
- ! Verify

Do not expose these labels everywhere. Use them at decision-critical points.

---

# 20. AI Interaction Pattern

AI assistance should be embedded into the workflow.

Example:

```text
✨ BathPlan AI

I found 2 feasible layouts within your budget.

Layout A prioritizes storage.
Layout B gives you more open circulation.

[ View Layout A ]
[ View Layout B ]
```

### Avoid

- giant conversational transcript
- full-screen chatbot
- excessive AI narration
- vague recommendations with no explanation

### Prefer

- contextual recommendations
- concise explanations
- decision cards
- actionable suggestions
- evidence/constraint references

---

# 21. Design Versioning

The interface must support design versions without confusing the user.

Example:

```text
VERSION 3
Modern Serenity
Saved 2 min ago

Version 1  Original
Version 2  Larger Vanity
Version 3  Current
```

Actions:

- Compare
- Restore
- Duplicate

The user should always know which version is active.

---

# 22. Responsive Design

## Desktop

Three-column workspace:

**Controls | Canvas | Product Intelligence**

## Tablet

Two-column workspace.

The product inspector and DesignPulse ledger may become collapsible drawers.

## Mobile

Single-column flow.

Use:

- bottom sheets
- accordions
- sticky primary action bar
- collapsible inspectors
- swipeable sections where appropriate

Never compress every desktop panel onto a small screen.

Do not introduce horizontal scrolling for the core workflow.

---

# 23. Production UI States

Every major workflow must have designed states for:

### Initial

- empty project
- onboarding
- no design yet

### Processing

- AI thinking
- vision analysis
- layout generation
- export generation

### Success

- design ready
- upload processed
- export complete

### Validation

- invalid dimensions
- incompatible product
- infeasible layout

### Uncertainty

- low-confidence observation
- unknown plumbing
- missing dimension
- required site verification

### System failures

- API failure
- network failure
- catalog unavailable
- upload failure
- export failure

### Persistence

- unsaved changes
- saving
- saved
- version conflict

### Search

- no product results
- catalog filtering
- compare mode

All errors should explain:

1. What happened
2. Why it matters
3. What the user can do next

Never expose raw backend/API errors directly to the user.

---

# 24. Design System

## Typography

Recommended scale:

| Level | Size |
|---|---:|
| Display | 32–40px |
| H1/Hero | 28–36px |
| Section heading | 20–24px |
| Card heading | 16–20px |
| Body | 14–16px |
| Metadata | 12–13px |

Typography should be highly readable at normal desktop viewing distance.

## Spacing

Use a consistent spacing scale:

**4 / 8 / 12 / 16 / 24 / 32 / 48px**

## Radius

Recommended:

**8–14px**

Use larger radius values sparingly.

## Surfaces

- white
- warm white
- soft stone
- very light gray

Use borders and subtle shadows instead of heavy elevation.

---

# 25. Color Direction

The visual system should be premium and restrained.

### Primary

- Deep navy
- Charcoal

### Neutral

- Warm white
- Ivory
- Soft gray
- Stone

### Semantic

- Restrained green → success / sustainability
- Amber → caution / verification
- Restrained red → errors

Avoid:

- neon gradients
- excessive purple “AI” styling
- rainbow semantic systems
- high-saturation decorative colors

---

# 26. Visual Personality

The application should feel:

- Premium
- Calm
- Architectural
- Intelligent
- Trustworthy
- Warm
- Precise
- Modern
- Sophisticated

Reference quality bar:

- Apple
- Notion
- Linear
- Figma
- premium interior-design software
- professional architectural planning tools

These are quality references, not templates to copy.

---

# 27. KOHLER-Inspired Visual Language

Use a restrained, premium visual language inspired by modern bathroom interiors.

Interface:

- warm whites
- stone neutrals
- charcoal/navy typography
- subtle natural green accents
- clean line icons
- carefully spaced controls

Product imagery can feature:

- ceramic
- marble
- stone
- matte finishes
- brushed metal
- wood
- glass

The UI should remain visually calm even when imagery is rich.

---

# 28. Accessibility

Production UI must support:

- WCAG-conscious contrast
- visible keyboard focus
- semantic headings
- labeled form controls
- descriptive buttons
- touch targets of appropriate size
- clear error messaging
- status not communicated by color alone
- screen-reader-friendly navigation
- reduced-motion behavior

Avoid tiny text and low-contrast metadata.

---

# 29. Microinteractions

Interactions should be subtle and purposeful.

### Product hover

Highlight the product's corresponding fixture on the plan.

### Product selection

Open contextual specifications and highlight placement.

### Design change

Trigger DesignPulse analysis.

### Version switch

Animate the transition between layouts subtly.

### Validation

Show inline state change rather than disruptive modal alerts.

### Save

Show:

> ✓ Saved just now

### Export

Show generation progress followed by a clear completion state.

Avoid animations that distract from spatial planning.

---

# 30. Important Anti-Patterns

Do **not** create:

- generic ChatGPT-style UI
- giant chat windows
- futuristic cyberpunk AI interfaces
- neon purple AI gradients
- excessive glassmorphism
- giant marketing hero sections
- dense dashboard card walls
- random charts
- unnecessary metrics
- tiny typography
- excessive badges
- decorative components without purpose
- impossible bathroom layouts
- fake product specifications
- fake prices
- fake engineering certainty

The application should look like a real product that a serious design team could ship.

---

# 31. Main Screen Composition

Target the following hierarchy:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Brief → Design → Refine → Finalize                                  Save ✓  │
├───────────────┬─────────────────────────────────────────────────────────────┤
│               │ Project context                                              │
│               ├─────────────────────────────────────────────────────────────┤
│               │ Compact hero/context                                         │
│   Sidebar     ├────────────────┬───────────────────────────┬────────────────┤
│               │                │                           │                │
│               │ Space Input    │      DESIGN CANVAS        │ Products       │
│               │                │                           │                │
│               │                │      2D / 3D / AR         │ Product cards  │
│               │                │                           │                │
│               ├────────────────┴───────────────────────────┴────────────────┤
│               │ DesignPulse │ Sustainability │ Visualization │ Export       │
│               │                                                            │
│               │ Validation / Decision Ledger                              │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

The **bathroom design canvas is the primary visual focal point**.

---

# 32. Interaction Hierarchy

Primary actions:

- Generate Design
- Apply Change
- Select Product
- Open 3D
- Launch AR
- Finalize Design

Secondary actions:

- Compare
- Edit
- Replace
- Duplicate
- View Details

Tertiary actions:

- Help
- More information
- Settings
- Advanced details

Do not give every action equal visual weight.

---

# 33. Design Decision Flow

### User changes vanity width

```text
User input
    ↓
DesignState updates
    ↓
Dependency graph identifies affected elements
    ↓
Deterministic impact calculation
    ↓
DesignPulse result
    ↓
User reviews consequences
    ↓
User applies / rejects / compares
    ↓
New design version
```

The UI should make this chain understandable without exposing implementation complexity.

---

# 34. Inspiration Experience

Inspiration should help users translate visual preferences into structured design intent.

Users can upload or browse inspiration.

Extract or represent:

- style
- materials
- finishes
- palette
- form language
- fixture coordination
- smart features
- sustainability preferences

Do not imply that an inspiration image itself is a technically valid bathroom plan.

### Example

```text
DESIGN DNA

Style
Modern Minimal

Palette
Warm White · Stone · Oak

Finish
Matte Black

Mood
Calm · Warm · Clean
```

---

# 35. Finalization Screen

Finalization should summarize the complete design.

### Summary

- room dimensions
- layout
- selected products
- estimated budget
- assumptions
- constraints
- verification checklist
- sustainability information
- design version

### Verification checklist

```text
✓ Room dimensions confirmed
✓ Door location confirmed
! Plumbing location requires verification
! Electrical point requires site verification
```

### Final actions

**Finalize Design**

Secondary:

- Export PDF
- Product List
- Share Link
- Return to Refine

Finalization should not imply physical installation is guaranteed.

---

# 36. UI Copy Principles

Use:

- concise language
- human explanations
- action-oriented labels
- progressive disclosure
- precise status messages

Prefer:

> “Plumbing location is unknown. Confirm on site before installation.”

Avoid:

> “AI confidence insufficient.”

Prefer:

> “This layout fits the current measurements.”

Avoid:

> “Optimization successful.”

Prefer:

> “Increasing the vanity to 900mm leaves 720mm circulation.”

Avoid:

> “Layout score: 94.”

Do not create fake precision merely to make the UI look intelligent.

---

# 37. Performance & Implementation Expectations

The design should map cleanly to reusable frontend components.

Suggested components:

```text
AppShell
Sidebar
WorkflowHeader
ProjectSummary
ProjectHero
SpaceInputPanel
DimensionFields
EntranceEditor
PreferenceSelector
UploadDropzone
DesignCanvas
CanvasToolbar
ViewSwitcher
ProductPanel
ProductCard
ProductInspector
DesignPulsePanel
ImpactSummary
SustainabilityCard
VisualizationCard
ExportCard
DecisionLedger
VersionSwitcher
AIInsightCard
FinalizeModal
Toast
InlineError
EmptyState
LoadingState
VerificationBadge
```

Components should be reusable and state-driven.

Do not build one giant page component.

---

# 38. State & Data Rules

The visual UI must reflect the real application state.

Never hardcode UI values that conflict with actual DesignState.

Examples:

- room dimensions come from project state
- selected products come from project state
- feasibility comes from deterministic validation
- impact comes from DesignPulse engine
- vision status comes from vision analysis
- budget comes from known product/price data
- sustainability metrics come from available calculation data

When information is unavailable, display:

**Unknown**

or

**Verify**

instead of inventing data.

---

# 39. Quality Bar for the Final UI

Before considering the UI finished, verify:

### Product clarity

Can a new homeowner understand the workflow within seconds?

### Visual hierarchy

Is the bathroom plan immediately obvious as the primary work area?

### Decision transparency

Can the user see why a design is feasible and what needs verification?

### AI differentiation

Does DesignPulse feel like a real product capability instead of chat pasted into a dashboard?

### Trust

Are estimated/unknown/verified information clearly differentiated?

### Technical credibility

Does the UI avoid fake precision and unsupported product claims?

### Production readiness

Are loading, errors, empty states, mobile behavior and accessibility considered?

### Brand quality

Does the interface feel premium, calm and appropriate for KOHLER?

---

# 40. Final Design Statement

The final KOHLER AI BathPlan experience should communicate this in seconds:

> **This is my bathroom.**
>
> **This is the plan.**
>
> **These are the products.**
>
> **This is why the plan works.**
>
> **This is what changes when I change something.**
>
> **This is what I still need to verify.**
>
> **This is what it costs.**
>
> **This is how it will look.**
>
> **This is how I finalize it.**

The product is successful when AI feels powerful **without becoming the interface itself**.

**AI interprets. Rules verify. DesignPulse explains consequences. Visualization builds confidence. The user makes the decision.**
