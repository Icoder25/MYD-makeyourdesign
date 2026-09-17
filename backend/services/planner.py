"""Planning orchestration.

This is the seam between the HTTP layer and the deterministic engines. It runs
the same pipeline every time, in the same order, with no AI anywhere in it:

    brief -> constraints -> recommend -> per-candidate layout + water -> explain

The explanation produced here is templated from the structured results. When the
LLM layer is available it *rewrites* this text into something more fluent, but it
never produces the numbers and never changes the verdict. If the LLM is
unavailable the user still gets a complete, accurate explanation — just a
plainer one.
"""

from backend.catalog import get_catalog
from backend.constraints import BathroomConstraints, build_layout
from backend.recommendation import recommend
from backend.recommendation.engine import (
    generate_configurations,
    retrieve_candidate_products,
)
from backend.sustainability import estimate_water_impact

from ..api.schemas import BathroomBrief, CandidatePlan, PlanMeta, PlanResponse

COMPUTED_BY = [
    "constraint_engine",
    "layout_solver",
    "recommendation_engine",
    "sustainability_calculator",
]


def brief_to_constraints(brief: BathroomBrief) -> BathroomConstraints:
    """Translate the user's brief into the constraint engine's input.

    Deliberately lossless about unknowns: a field the user left blank arrives
    here as None and stays None. Nothing is defaulted into a fact.
    """
    return BathroomConstraints(
        room_length_ft=brief.room_length_ft,
        room_width_ft=brief.room_width_ft,
        ceiling_height_ft=brief.ceiling_height_ft,
        budget=brief.budget,
        currency=brief.currency,
        required_categories=list(brief.required_categories),
        electrical_available=brief.electrical_available,
        toilet_rough_in_in=brief.toilet_rough_in_in,
        door=brief.door,
    )


def _money(value: float, currency: str) -> str:
    return f"{currency} {value:,.0f}"


def build_explanation(candidate: CandidatePlan) -> str:
    """Compose an explanation from structured results, with no LLM involved.

    Every sentence here is generated from a value the deterministic engines
    produced. This is the fallback that makes the LLM optional rather than
    load-bearing.
    """
    parts: list[str] = []
    report = candidate.constraint_report

    if report.status == "feasible":
        opening = "Every constraint check passed for this configuration."
    else:
        opening = (
            f"This configuration is physically and financially workable, with "
            f"{len(report.verification_requirements)} item(s) still to confirm before purchase."
        )
    parts.append(opening)

    if candidate.remaining_budget is not None:
        parts.append(
            f"It costs {_money(candidate.total_price, candidate.currency)}, leaving "
            f"{_money(candidate.remaining_budget, candidate.currency)} of the budget unspent."
        )
    else:
        parts.append(f"It costs {_money(candidate.total_price, candidate.currency)}.")

    placed = len(candidate.layout.placed)
    if placed:
        parts.append(
            f"The layout solver placed {placed} floor-standing fixture(s) against the walls "
            "with the clear space each one needs in front of it, and confirmed all of them "
            "remain reachable from the doorway."
        )

    water = candidate.water_impact
    if water.status == "calculated" and water.percent_saved is not None:
        if water.annual_litres_saved and water.annual_litres_saved > 0:
            parts.append(
                f"Estimated water use is {water.configuration_annual_litres:,.0f} litres a year, "
                f"about {water.percent_saved:.0f}% below the regulatory baseline "
                f"({water.baseline_annual_litres:,.0f} litres) under the stated usage assumptions."
            )
        else:
            parts.append(
                f"Estimated water use is {water.configuration_annual_litres:,.0f} litres a year, "
                "which is not an improvement on the regulatory baseline."
            )
    elif water.unquantified_products:
        parts.append(
            "Water use could not be estimated for "
            f"{', '.join(water.unquantified_products)} because no flow figure is recorded."
        )

    if candidate.trade_offs:
        parts.append("Trade-offs: " + " ".join(candidate.trade_offs))

    if report.verification_requirements:
        parts.append(
            "Before ordering, confirm: " + " ".join(report.verification_requirements)
        )

    return " ".join(parts)


def create_plan(brief: BathroomBrief, project_id: str) -> PlanResponse:
    """Run the full deterministic pipeline and assemble a response."""
    catalog = list(get_catalog())
    room = brief_to_constraints(brief)

    result = recommend(
        catalog,
        room,
        preference=brief.preferences,
        weights=brief.weights,
        max_candidates=brief.max_candidates,
    )

    # Recomputed purely so the response can report how much search happened.
    by_slot = retrieve_candidate_products(catalog, room)
    evaluated = (
        len(generate_configurations(by_slot, room.budget))
        if all(by_slot.values())
        else 0
    )

    notes: list[str] = []
    if brief.room_width_ft is None or brief.room_length_ft is None:
        notes.append(
            "Room dimensions were not supplied, so no layout could be solved and spatial "
            "feasibility remains unverified."
        )
    if brief.electrical_available is None:
        notes.append(
            "Electrical availability was not confirmed, so any powered product carries a "
            "verification requirement."
        )
    if brief.toilet_rough_in_in is None:
        notes.append(
            "The toilet rough-in measurement was not supplied, so it remains a verification "
            "requirement on every configuration containing a toilet."
        )

    candidates: list[CandidatePlan] = []
    for candidate in result.candidates:
        layout = build_layout(candidate.products, room)
        water = estimate_water_impact(candidate.products, brief.usage)
        plan = CandidatePlan(
            label=candidate.label,
            products=candidate.products,
            total_price=candidate.total_price,
            currency=candidate.currency,
            remaining_budget=candidate.remaining_budget,
            constraint_report=candidate.constraint_report,
            score=candidate.score,
            layout=layout,
            water_impact=water,
            strengths=candidate.strengths,
            trade_offs=candidate.trade_offs,
            installation_warnings=candidate.installation_warnings,
            verification_requirements=candidate.verification_requirements,
        )
        plan.explanation = build_explanation(plan)
        candidates.append(plan)

    from backend.settings import get_settings

    settings = get_settings()

    return PlanResponse(
        project_id=project_id,
        status="ok" if result.status == "ok" else "no_fully_compliant_configuration",
        brief=brief,
        candidates=candidates,
        conflict=result.no_compliant_configuration,
        meta=PlanMeta(
            computed_by=COMPUTED_BY,
            catalog_size=len(catalog),
            configurations_evaluated=evaluated,
            llm_available=settings.llm_available,
            vision_available=settings.vision_available,
            notes=notes,
        ),
    )
