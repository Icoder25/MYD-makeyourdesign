"""Conversational modification orchestration.

The flow, and the order matters:

    message -> structured intent -> DETERMINISTIC application to the brief
            -> engines recompute the whole plan -> explanation of what came back

The model participates at step two and step four only. It never touches step
three. That is why "add a smart shower but keep my budget" cannot produce a plan
that is over budget: the model can express the request, but the constraint engine
still decides, and if the two requirements are incompatible the result is a
conflict with options rather than a fabricated success.

Every LLM call is wrapped: a failure, a timeout, or malformed output falls back
to the deterministic path and the user still gets a complete answer.
"""

import asyncio

from ..api.schemas import BathroomBrief, ModifyResponse, PlanResponse
from ..services.planner import create_plan
from ..settings import get_settings
from .intent import ModificationIntent, extract_intent_keywords, extract_intent_llm

LLM_TIMEOUT_SECONDS = 12.0

# Categories that imply another should give way, because they compete for the
# same role in the room. Purely structural; nothing here is a judgement call.
SUPERSEDES = {
    "smart_toilet": "toilet",
    "toilet": "smart_toilet",
    "smart_shower": "shower",
    "shower": "smart_shower",
}


def build_context(plan: PlanResponse) -> str:
    """A compact description of the current plan for the intent prompt."""
    lines = [
        f"Room: {plan.brief.room_width_ft} ft x {plan.brief.room_length_ft} ft.",
        f"Budget: {plan.brief.currency} {plan.brief.budget:,.0f}."
        if plan.brief.budget is not None
        else "Budget: not set.",
        f"Required categories: {', '.join(plan.brief.required_categories)}.",
    ]
    if plan.candidates:
        top = plan.candidates[0]
        lines.append(
            f"Current selection costs {plan.brief.currency} {top.total_price:,.0f} and contains: "
            + ", ".join(f"{p.name} ({p.category})" for p in top.products)
            + "."
        )
    else:
        lines.append("No feasible configuration is currently selected.")
    return "\n".join(lines)


async def interpret(message: str, plan: PlanResponse) -> tuple[ModificationIntent, str]:
    """Get a structured intent, preferring the LLM but never depending on it."""
    settings = get_settings()
    if settings.llm_available:
        try:
            intent = await asyncio.wait_for(
                extract_intent_llm(
                    message,
                    build_context(plan),
                    settings.gemini_api_key,
                    settings.llm_model,
                ),
                timeout=LLM_TIMEOUT_SECONDS,
            )
            if not intent.is_empty() or intent.question:
                return intent, "llm"
            # The model understood nothing actionable; the keyword parser may
            # still recognise a phrasing, so it is worth trying.
        except Exception:
            # Timeout, network failure, malformed JSON, schema violation — all
            # handled identically, because the fallback is genuinely capable.
            pass
    return extract_intent_keywords(message), "deterministic_keywords"


def apply_intent(brief: BathroomBrief, intent: ModificationIntent) -> tuple[BathroomBrief, list[str]]:
    """Apply a structured intent to the brief. Pure, deterministic, auditable.

    Returns the amended brief and a plain-language list of what changed, so the
    user can see exactly which of their words became which change.
    """
    changes: list[str] = []
    required = list(brief.required_categories)
    updates: dict[str, object] = {}

    for category in intent.add_categories:
        superseded = SUPERSEDES.get(category)
        if superseded and superseded in required:
            required.remove(superseded)
            changes.append(
                f"Replaced '{superseded}' with '{category}' — they fill the same role in the room."
            )
        if category not in required:
            required.append(category)
            changes.append(f"Added '{category}' to the required categories.")

    for category in intent.remove_categories:
        if category in required:
            required.remove(category)
            changes.append(f"Removed '{category}' from the required categories.")

    if required != brief.required_categories:
        updates["required_categories"] = required

    if intent.new_budget is not None and intent.budget_change in {"increase", "decrease"}:
        updates["budget"] = intent.new_budget
        changes.append(f"Set the budget to {brief.currency} {intent.new_budget:,.0f}.")
    elif intent.budget_change == "keep" and brief.budget is not None:
        changes.append(
            f"Held the budget at {brief.currency} {brief.budget:,.0f} as a hard limit."
        )

    weights = brief.weights
    preferences = brief.preferences
    if intent.priority_shift == "cheaper":
        weights = weights.model_copy(update={"budget": weights.budget * 3})
        changes.append("Shifted ranking weight toward budget fit.")
    elif intent.priority_shift == "premium":
        weights = weights.model_copy(update={"budget": max(weights.budget * 0.3, 0.1)})
        changes.append("Reduced the weight on cost so higher-tier products can rank.")
    elif intent.priority_shift == "water_efficiency":
        weights = weights.model_copy(update={"water_efficiency": weights.water_efficiency * 4})
        changes.append("Shifted ranking weight toward water efficiency.")
    elif intent.priority_shift == "smart_features":
        weights = weights.model_copy(update={"smart_feature": weights.smart_feature * 4})
        preferences = preferences.model_copy(update={"smart_feature_preference": "prefer"})
        changes.append("Shifted ranking weight toward smart features.")
    elif intent.priority_shift == "storage":
        weights = weights.model_copy(update={"preference": weights.preference * 3})
        preferences = preferences.model_copy(update={"storage_preference": "spacious"})
        changes.append("Shifted ranking weight toward storage capacity.")

    if weights is not brief.weights:
        updates["weights"] = weights
    if preferences is not brief.preferences:
        updates["preferences"] = preferences

    if intent.preferred_styles:
        merged = list(dict.fromkeys([*brief.preferred_styles, *intent.preferred_styles]))
        if merged != brief.preferred_styles:
            updates["preferred_styles"] = merged
            updates["preferences"] = preferences.model_copy(
                update={"preferred_styles": merged}
            )
            changes.append(f"Noted style preference: {', '.join(intent.preferred_styles)}.")

    if not changes:
        changes.append("No change was made — the request did not map to an actionable modification.")

    return brief.model_copy(update=updates), changes


async def modify_plan(message: str, plan: PlanResponse) -> ModifyResponse:
    """Interpret a message, apply it deterministically, and recompute the plan."""
    intent, source = await interpret(message, plan)

    if intent.question and intent.is_empty():
        # A question about the existing plan changes nothing. Recomputing would
        # be wasteful and could surprise the user by re-ranking under their feet.
        return ModifyResponse(
            project_id=plan.project_id,
            understood_as=intent.summary or "Answer a question about the current plan.",
            interpretation_source=source,
            applied_changes=["No change requested — this was a question about the current plan."],
            plan=plan,
        )

    amended, changes = apply_intent(plan.brief, intent)
    recomputed = create_plan(amended, plan.project_id)

    return ModifyResponse(
        project_id=plan.project_id,
        understood_as=intent.summary or "Applied the requested modification.",
        interpretation_source=source,
        applied_changes=changes,
        plan=recomputed,
    )
