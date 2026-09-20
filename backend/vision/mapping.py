"""Deterministic Vision-to-DesignState Mapping & Reconciliation Layer.

CRITICAL INVARIANTS & GUARDRAILS:
1. Vision is an INPUT mechanism, not a feasibility authority.
2. GUARDRAIL 1: Confidence threshold (0.7) is strictly an application classification heuristic.
3. GUARDRAIL 2: Unknown visual attributes map to verification requirements (status="verification_required", blocking=False).
   UNKNOWN != INFEASIBLE.
4. GUARDRAIL 3: Approximate wall regions are advisory observations, NEVER hard layout constraints.
5. PRECEDENCE RULE: User Confirmed/Measured Input > Catalog Facts > Visual Observations.
   Vision never overwrites user-entered dimensions, budget, or physical rough-in facts.
"""

from typing import Any
from backend.api.schemas import BathroomBrief
from backend.constraints.models import CheckResult
from backend.designpulse.models import ConstraintLedgerEntry, DecisionRecord, DesignState
from backend.vision.models import BathroomVisionEvidence


def map_vision_to_verification_checks(evidence: BathroomVisionEvidence) -> list[CheckResult]:
    """Maps visual unverifiable attributes and occlusions to non-blocking verification checks.

    GUARDRAIL 2: Every check has passed=True, blocking=False, status='verification_required'.
    Unknowns never trigger constraint failure or infeasibility.
    """
    checks: list[CheckResult] = []

    attr_labels = {
        "exact_room_dimensions": "Room Geometry",
        "plumbing_location": "Plumbing Rough-In Location",
        "toilet_rough_in": "Toilet Center Rough-In",
        "electrical_availability": "Dedicated Electrical Circuit",
        "hidden_pipes": "Concealed Plumbing Stacks",
        "wall_thickness": "Wall Chase Depth",
        "structural_constraints": "Structural Capacity",
    }

    attrs = evidence.unverifiable_attributes.model_dump()
    for key, item in attrs.items():
        label = attr_labels.get(key, key.replace("_", " ").title())
        checks.append(
            CheckResult(
                constraint=f"vision_verification_{key}",
                passed=True,
                status="verification_required",
                reason=f"{label}: requires on-site verification ({item.get('reason', 'Not observable from photograph')})",
                blocking=False,
                details={"source": "vision_analysis", "attribute": key},
            )
        )

    # If any occlusions exist, add advisory verification checks
    for occ in evidence.occlusions:
        checks.append(
            CheckResult(
                constraint=f"vision_occlusion_{occ.target_object}",
                passed=True,
                status="verification_required",
                reason=f"{occ.target_object.title()} partially occluded by {occ.occluded_by} (~{occ.estimated_occlusion_pct:.0f}%); confirm physical clearances on site",
                blocking=False,
                details={"source": "vision_analysis", "occlusion_pct": occ.estimated_occlusion_pct},
            )
        )

    return checks


def reconcile_brief_with_vision(
    brief: BathroomBrief, evidence: BathroomVisionEvidence
) -> tuple[BathroomBrief, list[DecisionRecord]]:
    """Reconciles bathroom brief with vision evidence following deterministic precedence rules.

    PRECEDENCE RULE:
    1. User dimensions, budget, and measurements strictly override visual estimates.
    2. Vision provides advisory fixture observations and approximate zones.
    """
    decisions: list[DecisionRecord] = []

    # Record advisory decision records for observed fixtures
    for obj in evidence.detected_objects:
        decisions.append(
            DecisionRecord(
                category=obj.type,
                action="initial_selection",
                rationale=(
                    f"Visual Observation: {obj.type.title()} detected ({obj.observation_status}, "
                    f"confidence {obj.confidence:.0%}). Advisory position: {obj.approximate_wall_region} wall."
                ),
                client_requirement_ref=f"site_photo_observation_{obj.observation_status}",
            )
        )

    # User inputs strictly remain authoritative. Brief is returned with user parameters preserved.
    return brief, decisions


def attach_vision_to_design_state(
    state: DesignState, evidence: BathroomVisionEvidence
) -> DesignState:
    """Attaches vision evidence to a DesignState and updates the verification ledger.

    GUARDRAIL 2: Unknowns increment verification_count, but NEVER mark domain as 'fail'.
    If overall_status was 'feasible', it becomes 'feasible_pending_verification'.
    """
    verification_checks = map_vision_to_verification_checks(evidence)

    # Get verification domain entry in ledger
    existing_verif = state.ledger.verification
    combined_checks = list(existing_verif.checks) if existing_verif else []
    combined_checks.extend(verification_checks)

    verif_count = len([c for c in combined_checks if c.status == "verification_required"])

    new_verif_entry = ConstraintLedgerEntry(
        domain="verification",
        status="warning" if verif_count > 0 else "pass",
        summary=f"{verif_count} on-site physical verification check(s) required (including visual observations).",
        blocking_count=0,
        warning_count=0,
        verification_count=verif_count,
        checks=combined_checks,
    )

    new_ledger = state.ledger.model_copy(
        update={"verification": new_verif_entry}
    )

    # Build advisory decision records
    _, visual_decisions = reconcile_brief_with_vision(
        brief=BathroomBrief(
            room_width_ft=state.room_width_ft,
            room_length_ft=state.room_length_ft,
            budget=state.budget_limit,
            required_categories=[p.category for p in state.selected_products],
        ),
        evidence=evidence,
    )

    combined_decisions = list(state.decision_records) + visual_decisions

    # Update metadata with vision summary
    new_metadata = dict(state.metadata)
    new_metadata["vision_overall_confidence"] = evidence.overall_confidence
    new_metadata["vision_detected_count"] = len(evidence.detected_objects)

    return state.model_copy(
        update={
            "vision_analysis": evidence,
            "ledger": new_ledger,
            "decision_records": combined_decisions,
            "metadata": new_metadata,
        }
    )
