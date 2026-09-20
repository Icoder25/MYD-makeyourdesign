# KOHLER AI BathPlan — Project Report

## 1. Overview

KOHLER AI BathPlan is a bathroom planning and recommendation system developed for the KOHLER MIT-WPU AI Research Lab — Track 1. The project is centered on one clear idea: the AI can help imagine and describe a bathroom, but a deterministic constraint engine decides whether the design is actually feasible in real-world conditions.

The system combines:

- a curated product catalog
- bathroom constraint validation
- layout solving with clearance and door-swing logic
- recommendation and trade-off generation
- sustainability and water-impact calculation
- DesignPulse impact analysis
- immutable versioning and decision records
- exportable design outputs

This project is designed to help designers understand not just what could be planned, but what is truly possible and what changes are required when a requirement changes.

---

## 2. What We Have Done

We have successfully built and verified the product’s core workflow.

### Product and core workflow

- Created a bathroom planning application that accepts room size, budget, door type, required fixtures, style, and priorities.
- Developed a deterministic recommendation engine that generates valid bathroom configurations.
- Implemented layout solving with clearance rules, circulation checks, and door swing logic.
- Built a constraint engine with a structured three-state validation model: pass, verification required, and fail.
- Added DesignPulse functionality that evaluates a requested change before it is applied.
- Added trade-off analysis where each option is tested through the same deterministic engine.
- Implemented version history so changes create new versions without overwriting the prior state.
- Added finalization and explicit verification acknowledgements for uncertain items.
- Delivered exportable project documents for client presentation, designer specification, and dealer BOM.

### Technical implementation

- Built backend APIs for planning, project creation, impact analysis, application of changes, history, diff, finalization, and export.
- Created a rule-driven recommendation and scoring system.
- Implemented water-use calculation with assumptions and documented disclaimers.
- Added a vision module that is advisory only and never allowed to directly determine feasibility.
- Added deterministic intent parsing and fallback logic for user changes.
- Integrated an in-memory project store for the prototype workflow.
- Built a frontend workspace with plan, specification, DesignPulse, and constraint ledger views.

### Verified status

The current project state reports:

- backend tests passing
- frontend typecheck/build passing
- browser-based workflow verified end-to-end
- API and UI proven for the main deterministic planning path
- DesignPulse and finalization flow working in live operation

The system is therefore considered ready with known limitations, not completely unlimited or production-grade in every sense.

---

## 3. What We Had Done Before

Before reaching the current completed stage, the project went through several major design and engineering milestones.

### Early project foundation

- Initial product research and definition for a bathroom planning assistant.
- Product thesis defined around the idea that AI can imagine a bathroom while the constraint engine decides survivability.
- Research on bathroom design constraints, clearance rules, fixture compatibility, and project requirements.
- Definition of architecture separating AI assistance from deterministic validation.

### System development phases

- Built the curated catalog of bathroom products and product metadata.
- Implemented structured constraint validation and compatibility checks.
- Added recommendation and search logic to rank feasible bathroom combinations.
- Developed the layout solver to place fixtures on walls and validate clearances.
- Introduced the concept of DesignPulse as the core differentiator: showing the impact of a design change before it is applied.
- Added version chain and decision memory so a project remains auditable.
- Integrated sustainability analysis and water consumption calculations.
- Improved the UI into a professional workspace layout with multiple panes and a logic ledger.

### Iterative fixes and improvements

During the lifecycle, multiple defects and workflow problems were fixed, including:

- false verification requirements that made feasible plans unreachable
- overwrite issues in version modification flows
- missing vocabulary for room and size changes
- CORS issues affecting preview/origin handling
- analysis being incorrectly applied twice or against the wrong version
- performance improvements in the layout solver
- documentation cleanup and architecture stabilization

These fixes were essential because they moved the project from a rough prototype to a reliable demonstration-grade system.

---

## 4. What We Are Doing Now

At the current stage, the team is validating the product as a complete but scoped prototype.

### Current focus

- Final verification of the system against the working tree and runtime environment.
- Confirming backend and frontend functionality together.
- Validating the live workflow with the real product paths.
- Documenting the known limitations and non-goals clearly.
- Preparing release and submission assets.

### Current status

The project is in a high-confidence delivery state:

- code is complete
- core backend workflows are verified
- frontend builds and renders correctly
- real planning and impact-analysis flows operate in the app
- known limitations are documented rather than hidden

The product has reached a point where it is effectively a polished prototype or demo-ready implementation with clear boundaries.

---

## 5. What We Will Be Doing Next

The next step is to prepare the project for final delivery and presentation.

### Immediate next steps

- Finalize project documentation and summary reports.
- Prepare the remaining external deliverables beyond the repository, such as:
  - a 4-slide deck
  - a short demo video
  - a prompts PDF
- Ensure the demo narrative explains the technical value clearly.
- Present the deterministic workflow and DesignPulse value proposition in a concise, non-overpromising way.

### Future-oriented roadmap

If this is extended beyond the current prototype phase, the likely next work would include:

- persistence with a real database and migration system
- stronger authentication and project ownership
- improved export formats such as PDF or spreadsheet-ready BOMs
- richer 3D, 360, and AR planning experiences
- live product inventory and supplier integration
- production-grade deployment and monitoring
- accessibility and browser automation coverage

### Strategic direction

The long-term goal remains the same:

- AI supports ideation and interpretation
- deterministic systems verify feasibility
- designers receive explainable trade-offs instead of risky guesswork

That core principle is the main product value and should remain the focus of future development.

---

## 6. Final Assessment

The project has reached a meaningful milestone. We have built a working, test-verified bathroom planning platform with a real DesignPulse mechanism, a robust deterministic constraint engine, and a usable end-to-end workflow. We have also documented the current limitations honestly, which is essential for a prototype with strong technical foundations but not full production persistence or advanced visualization.

In short:

- What we have done: built and verified the core product.
- What we had done before: layered the system architecture, product logic, and iterative fixes into a working prototype.
- What we will be doing: finalize presentation assets, document the product’s known limitations, and plan the next-generation improvements for real-world deployment.

This is a strong project outcome: innovative, technically grounded, and ready for demonstration with clear scope boundaries.
