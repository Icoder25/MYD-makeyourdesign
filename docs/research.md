# KOHLER AI BathPlan — Research

> Implementation research for the KOHLER-MITWPU AI Research Lab, Track 1.  
> **Evidence status:** this document captures the research conclusions already established for the project. Current public claims should be re-verified immediately before submission if they affect a factual demo statement.

## Executive conclusion

The market does **not** leave a clean innovation claim around “AI bathroom design.” Image redesign, AI room generation, 2D/3D planning, conversational design and even constraint-aware bathroom planning already exist in competing products.

The defensible opportunity is narrower:

> **Turn bathroom planning into a validated decision problem around real KOHLER products, explicit constraints, quantified trade-offs and evidence-backed water impact.**

Core system principle:

> **Generative AI proposes. Deterministic systems validate. The user controls the trade-offs.**

The LLM must never be the source of truth for dimensions, price, compatibility, installation requirements, physical feasibility or calculated water impact.

---

## 1. Exact customer problem

### Primary user
A homeowner/renovator who knows roughly what they want but does not know which actual bathroom configuration will work within their space, budget and priorities.

### Painful moment

> “I have this bathroom, this budget and these preferences. What should I actually buy and how should it fit together?”

The problem is therefore a **configuration decision**, not an image-generation problem.

### Decision improved
Choose among feasible combinations of:
- toilet
- vanity
- basin
- faucet
- shower/digital shower components
- storage
- selected accessories

while respecting:
- room dimensions
- known openings/obstacles
- product dimensions
- budget
- must-have features
- selected installation assumptions
- sustainability priorities

### Explicitly not our problem
- construction drawings
- professional code certification
- structural engineering
- exact plumbing engineering
- contractor management
- procurement/checkout
- live inventory
- exact installation quotation
- full-home design
- AR
- production CAD

---

# 2. KOHLER current-state findings

## 2.1 Bathroom design services

**FACT:** KOHLER offers bathroom design services involving collaboration with a KOHLER design expert. Public descriptions include detailed floorplans, photo-realistic room renderings and a detailed shopping list.

**MODE:** Human-assisted + digital deliverables.

**OPPORTUNITY:** BathPlan should not pretend to replace this service. Position it as an AI self-serve decision layer that can help a customer reach a structured, validated concept before a designer/purchase conversation.

Source:
- https://www.kohler.com/en/services/bathroom-design-services

---

## 2.2 Digital planning / visualization

**FACT:** KOHLER has strong digital product discovery, product visualization/inspiration and design-service rendering capabilities.

**UNKNOWN / IMPORTANT BOUNDARY:** Public evidence does not justify claiming that KOHLER has “no digital bathroom design.” The defensible distinction is between KOHLER's product/design-service ecosystem and a self-serve AI decision workflow that continuously re-optimizes a whole bathroom configuration.

**OPPORTUNITY:** Make the product about configuration reasoning rather than prettier rendering.

---

## 2.3 Smart bathroom ecosystem

**FACT:** KOHLER markets a smart-home ecosystem spanning connected bathroom products.

**MODE:** Digital / connected-product ecosystem.

Source:
- https://www.kohler.com/en/products/smart-home

**OPPORTUNITY:** Use smart capabilities as structured product attributes in planning. Do not attempt live smart-home integration in the 48-hour MVP.

---

## 2.4 KOHLER Konnect

**FACT:** KOHLER Konnect is used as a digital hub/control experience for compatible smart KOHLER products.

**MODE:** Digital / connected.

**OPPORTUNITY:** Treat “smart ecosystem readiness” as a future planning dimension. MVP can represent smart features as catalog attributes without integrating the app.

---

## 2.5 Smart toilets

KOHLER's smart-toilet portfolio includes families/products such as Numi 2.0, Veil and Innate.

Public product descriptions include combinations of:
- bidet functionality
- heated seating
- automatic/motion features
- self-cleaning functions
- night lighting
- personalized controls
- other smart features depending on model

Source:
- https://www.kohler.com/en/products/smart-home/shop-smart-toilets

**OPPORTUNITY:** Smart-toilet features can become preference weights in the recommendation engine.

---

## 2.6 Digital showers / Anthem family

KOHLER's digital shower ecosystem includes Anthem products.

Relevant dimensions for BathPlan:
- shower configuration
- digital controls
- personalization
- water usage
- installation/configuration assumptions

Do not infer exact compatibility between arbitrary components. Encode only relationships documented in product data.

---

## 2.7 Anthem EvoCycle

**FACT:** KOHLER markets Anthem EvoCycle as a recirculating shower system and states that it can save **up to 80% water compared with a standard shower system** under the manufacturer's stated conditions.

Source:
- https://www.kohler.com/en/products/showers/anthem-evocycle

**IMPLEMENTATION RULE:** Store the manufacturer claim as a product-level attribute. Do not present “80% savings” as a universal household result.

---

## 2.8 Faucets

KOHLER has a broad faucet portfolio.

For BathPlan, faucet data should be normalized around:
- category
- collection
- finish
- installation type
- dimensions
- water-efficiency attributes where available
- compatibility assumptions
- price
- source URL
- verification date

Public catalog:
- https://www.kohler.com/en/shop/pt-index

---

## 2.9 Vanities

KOHLER offers vanity/cabinet products across collections.

For BathPlan, the critical fields are:
- width
- depth
- height
- basin configuration
- installation type
- storage characteristics
- collection/style
- finish
- price
- source URL

Do not treat a product name alone as enough information for feasibility.

---

## 2.10 Water-efficient products

KOHLER maintains product groupings and sustainability information around water efficiency.

Source:
- https://www.kohler.com/en/products/sustainability

**OPPORTUNITY:** Move from product-level sustainability labels to a planning-level comparison:
- baseline configuration
- water-efficient configuration
- estimated usage
- estimated delta
- assumptions

---

## 2.11 WaterSense

WaterSense should be represented as a **certification/attribute when explicitly documented**, not as a blanket claim for all KOHLER water products.

For the MVP, use a field such as:
`watersense_certified: true/false/unknown`

Only populate `true` when the underlying source or authoritative certification evidence supports it.

---

## 2.12 Product specifications

KOHLER public product pages and installation/specification materials can expose useful structured facts, including dimensions and installation-related information for individual products.

Useful normalized schema:

```text
id
name
category
collection
market
currency
price
last_verified
width
depth
height
installation_type
rough_in
style
finish
water_usage
watersense_certified
smart_features
compatibility_group
sustainability_attributes
source_url
confidence
```

**Key architecture point:** source facts belong in the product database, not in the LLM's memory.

---

## 2.13 Installation constraints

Public installation/specification documents can contain rough-in, mounting, dimensions and other requirements.

But a consumer prototype should **not** convert incomplete public information into a claim of installation certification.

Use three states:
- `verified`
- `assumed`
- `unknown`

When unknown, the UI must say so.

---

## 2.14 Personalization

KOHLER personalizes through product families, collections, finishes, smart-product settings and design consultation.

BathPlan can extend personalization from **single-product preferences** to **whole-bathroom trade-offs**:
- more storage vs. more circulation
- larger vanity vs. shower size
- lower cost vs. premium finish
- water efficiency vs. product choices

This is the core planning opportunity.

---

# 3. Current customer journey

A defensible synthesized journey is:

1. Inspiration
2. Define project
3. Explore style/products
4. Consider dimensions/preferences
5. Design consultation where needed
6. Floorplan/rendering
7. Product selection/shopping list
8. Purchase/installation

This is a synthesis of KOHLER's public design/product experience, not a claim that every customer follows the exact same path.

**BathPlan insertion point:**

`Inspiration → BathPlan → structured project brief → validated concepts → KOHLER products → designer/purchase journey`

This makes BathPlan complementary to KOHLER rather than adversarial.

---

# 4. Competitor research

## Planner 5D

Sources:
- https://planner5d.com/use/ai-bathroom-design
- https://planner5d.com/use/bathroom-planner-tool

Publicly marketed capabilities include:
- AI bathroom design
- 2D/3D planning
- dimensions
- scanning
- fixture placement
- bathroom layout variables
- plumbing-related constraints
- visual design

**Important correction:** Planner 5D means we cannot claim that competitors simply “ignore constraints.”

**Opportunity:** Differentiate through explicit, inspectable validation tied to a curated KOHLER product knowledge base and quantified trade-offs.

---

## Homestyler

Sources:
- https://www.homestyler.com/
- https://www.homestyler.com/about/updates

Public capabilities include:
- 2D/3D
- AI Floor Planner
- AI rendering
- moodboards
- AI design
- conversational/agent-style experiences
- large object libraries

**Implication:** “Conversational AI interior design” is not enough.

---

## Houzz

Houzz combines:
- inspiration
- product discovery
- professionals/services
- project/design workflows

Houzz Pro has room scanning / floor-plan-related capabilities.

Relevant source:
- https://www.houzz.com/

**Implication:** Product discovery + design + professionals is already a mature pattern.

---

## RoomGPT-style tools

Representative:
- https://www.roomgpt.io/

Typical strengths:
- upload room image
- generate redesigned images
- style transformation

Typical weaknesses relative to BathPlan:
- dimensioned feasibility
- real bathroom SKU configuration
- explicit budget optimization
- installation/compatibility reasoning
- quantified planning-level sustainability
- inspectable rejection/repair loop

These tools should be treated as evidence for the commoditization of image-first room redesign.

---

## Bathroom-specific AI tools

Examples:
- https://home-design.ai/ai-bathroom-design
- https://www.myarchitectai.com/bathroom-design-generator

These demonstrate that “AI bathroom design” itself is already a category.

**Implication:** A visual concept generator is not enough for the competition thesis.

---

# 5. What is commoditized / weak differentiation

The following should NOT be the headline innovation:

| Capability | Strategic status |
|---|---|
| Upload room photo | Commodity/expected |
| Style transfer | Commodity |
| Pretty bathroom render | Commodity |
| Generic chatbot | Commodity |
| Generic RAG product Q&A | Weak |
| Basic 2D planner | Crowded |
| Basic 3D planner | Crowded |
| Moodboard | Crowded |
| Generic AI layout generation | Crowded |
| Conversational design alone | Crowded |
| Generic product recommendation | Crowded |

Yellow / useful but insufficient:
- image understanding
- product search
- budget display
- AI layout
- recommendation explanations

Stronger:
- curated real KOHLER product configuration
- deterministic validation
- transparent rejection
- re-optimization after user changes a constraint
- quantified trade-offs
- planning-level water impact

---

# 6. Research conclusion

The competitive whitespace is not:

> “AI that designs bathrooms.”

It is closer to:

> **“AI that helps a customer decide which real bathroom configuration actually works, why it works, and what changes when priorities change.”**

That is the research basis for the locked MVP.
