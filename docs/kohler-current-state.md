# KOHLER AI BathPlan — KOHLER Current State

## Purpose

This is an implementation-facing audit of the KOHLER capabilities most relevant to BathPlan.

The key question is not “what does KOHLER sell?” It is:

> **What existing KOHLER capability does BathPlan complement, extend or connect?**

---

# Capability audit

| KOHLER capability | What is publicly evident | Mode | BathPlan implication |
|---|---|---|---|
| Bathroom design services | Design expert + floorplans + renderings + shopping list | Human + digital | BathPlan can be an upstream self-serve decision layer |
| Product discovery | Broad bathroom catalog | Digital | Curate structured subset |
| Product visualization | Product imagery/inspiration + design-service renderings | Digital | Do not compete primarily on rendering |
| Smart bathroom ecosystem | Connected bathroom products | Digital/connected | Use smart attributes; skip live integration |
| Konnect | Connected-product control experience | Digital/connected | Future planning dimension |
| Smart toilets | Numi/Veil/Innate and other smart products | Digital product | Encode features as preferences |
| Digital showering | Anthem family | Digital/connected | Encode configuration and efficiency attributes |
| Anthem EvoCycle | Recirculating shower; manufacturer states up to 80% water savings vs standard system | Digital/physical | Use as evidence-backed efficiency attribute |
| Faucets | Broad portfolio | Physical/digital catalog | Normalize specs |
| Vanities | Broad portfolio | Physical/digital catalog | Normalize dimensions/storage/style |
| Water-efficient products | Sustainability and efficiency positioning | Physical/digital | Enable configuration-level comparison |
| WaterSense | Relevant certification/efficiency context | Certification | Only mark where evidence supports it |
| Product specifications | Public product/specification pages | Digital data | Source of deterministic rules |
| Installation information | Product/specification/installation documentation | Technical documentation | Encode only verified constraints |
| Personalization | Design consultation, collections, finishes, smart settings | Human + digital | Extend personalization to system-level trade-offs |

---

# Sources and implementation notes

## Bathroom Design Services

Official:
https://www.kohler.com/en/services/bathroom-design-services

Publicly described outputs include:
- detailed floorplans
- photo-realistic room renderings
- shopping list
- collaboration with KOHLER design expertise

### Product decision
Do not pitch BathPlan as a replacement for professional design. Pitch it as a fast decision layer that can prepare a customer for professional service or purchase.

---

# Smart Home / Konnect

Official:
https://www.kohler.com/en/products/smart-home

### Product decision
Create catalog fields such as:

```text
smart_capable
smart_features[]
konnect_compatible
```

For MVP these are static attributes.

Do not build:
- live Konnect account integration
- device control
- post-install telemetry

Those are outside the 48-hour objective.

---

# Smart Toilets

Official:
https://www.kohler.com/en/products/smart-home/shop-smart-toilets

### Product decision

Normalize:

```text
bidet
heated_seat
automatic_flush
night_light
self_cleaning
personalized_settings
smart_features
```

Only populate a field when the selected product page supports it.

---

# Anthem / Anthem+

Anthem products belong to KOHLER's digital showering ecosystem.

### Product decision

Represent shower systems through explicit component/configuration records rather than treating “Anthem” as a single generic SKU.

Potential fields:

```text
shower_system_family
control_type
digital
components[]
installation_type
water_usage
compatibility_group
```

### Safety

Never infer arbitrary component compatibility. If the relationship is not documented in the curated dataset, mark it unknown.

---

# Anthem EvoCycle

Official:
https://www.kohler.com/en/products/showers/anthem-evocycle

KOHLER publicly states an **up to 80% water-saving** comparison against a standard shower system.

### Product decision

Store:

```text
manufacturer_water_claim:
  type: "up_to"
  value: 0.80
  comparison: "standard shower system"
  source_url: ...
```

Then display the claim accurately.

Do not calculate:

> “You will save 80%.”

Instead:

> “KOHLER states up to 80% water savings vs. a standard shower system; your estimated household impact depends on usage and conditions.”

---

# Faucets

Official catalog:
https://www.kohler.com/en/shop/pt-index

### Required fields

```text
category
collection
finish
installation_type
dimensions
flow_rate
price
source_url
last_verified
```

Where flow data is unavailable, use `unknown`, not an inferred number.

---

# Vanities

### Required fields

```text
category
width
depth
height
basin_count
installation_type
storage_class
collection
finish
price
source_url
```

The validator needs physical dimensions; product names are insufficient.

---

# Water efficiency / sustainability

Official:
https://www.kohler.com/en/products/sustainability

### Product decision

Create:

```text
water_efficiency_class
flow_rate
flush_volume
watersense_certified
manufacturer_efficiency_claim
source_url
```

Do not claim a complete environmental life-cycle assessment.

---

# Public specifications and installation documents

The public KOHLER ecosystem can expose technical product facts through product/specification/installation materials.

BathPlan should convert only selected, verified facts into deterministic rules.

Example:

```text
if vanity.width > available_wall_width:
    reject("WALL_WIDTH_EXCEEDED")
```

Do not attempt to infer building-code compliance from incomplete product metadata.

---

# Personalization

KOHLER already supports personalization through:
- collections
- finishes
- product configurations
- smart-product settings
- design consultation

BathPlan's proposed extension is:

> **personalization of the whole configuration and its trade-offs**

Example:

`Storage ↑ → vanity size ↑ → circulation ↓`

or:

`Budget ↓ → premium product substitution → style similarity ↓`

This is the core strategic bridge between KOHLER's product ecosystem and the proposed AI workflow.

---

# Recommended KOHLER data model

```json
{
  "id": "kohler_example_001",
  "name": "Example Product",
  "category": "vanity",
  "collection": "Example",
  "market": "US",
  "currency": "USD",
  "price": null,
  "last_verified": "YYYY-MM-DD",
  "dimensions": {
    "width": null,
    "depth": null,
    "height": null
  },
  "installation": {
    "type": null,
    "rough_in": null
  },
  "style": [],
  "finish": [],
  "water": {
    "flow_rate": null,
    "flush_volume": null,
    "watersense": null
  },
  "smart": {
    "features": [],
    "konnect_compatible": null
  },
  "compatibility_group": [],
  "sustainability_attributes": [],
  "source_url": "",
  "confidence": "verified|assumed|unknown"
}
```

---

# Data integrity rules

1. Every product needs a source URL.
2. Every price needs a verification date.
3. Every dimension used by the validator must have evidence.
4. Unknown values must remain unknown.
5. Manufacturer “up to” claims must remain “up to.”
6. Compatibility must be explicit, not inferred by the LLM.
7. The LLM must not invent missing product facts.
8. Demo data should be clearly labeled as a curated prototype catalog.

---

# KOHLER journey model

A practical synthesis:

`Inspiration`
→ `Project definition`
→ `Style/product exploration`
→ `Dimensions/preferences`
→ `Design consultation`
→ `Floorplan/rendering`
→ `Product selection`
→ `Purchase/installation`

BathPlan sits at:

`Inspiration`
→ **BathPlan**
→ `Validated configuration`
→ `Design service / purchase`

This makes the product strategically complementary to KOHLER's existing experience.

---

# What BathPlan should NOT claim

Avoid these claims unless separately verified:

- “KOHLER has no digital bathroom planner.”
- “No competitor handles constraints.”
- “KOHLER does not use AI.”
- “BathPlan is the first AI bathroom designer.”
- “Our system guarantees installation feasibility.”
- “Our water savings are exact.”
- “We have the complete KOHLER catalog.”
- “We have live KOHLER inventory.”
