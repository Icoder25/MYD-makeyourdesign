"""Tests for Phase 1: DesignPulse DesignState, ConstraintLedger, and Versioning.
"""

import pytest

from backend.api.schemas import BathroomBrief, CandidatePlan
from backend.catalog import get_catalog
from backend.constraints import BathroomConstraints, build_layout, validate_configuration
from backend.designpulse.models import (
    ConstraintLedger,
    DecisionRecord,
    DesignState,
    DesignStateDiff,
    VersionHistory,
    build_constraint_ledger,
    compute_design_state_diff,
    create_design_state_from_candidate,
)
from backend.recommendation.models import ScoreBreakdown, ScoringWeights
from backend.services.planner import brief_to_constraints, create_plan
from backend.services.store import store
from backend.sustainability.calculator import estimate_water_impact


def _sample_brief(budget: float = 250000.0) -> BathroomBrief:
    return BathroomBrief(
        room_width_ft=6.0,
        room_length_ft=8.0,
        ceiling_height_ft=8.0,
        budget=budget,
        required_categories=["vanity", "basin", "faucet", "toilet", "shower"],
        electrical_available=True,
        toilet_rough_in_in=12.0,
    )


def test_constraint_ledger_all_pass():
    brief = _sample_brief(budget=300000.0)
    plan_response = create_plan(brief, "test_proj_1")
    assert plan_response.status == "ok"
    candidate = plan_response.candidates[0]

    ledger = build_constraint_ledger(
        report=candidate.constraint_report,
        water=candidate.water_impact,
        budget_limit=brief.budget,
        total_price=candidate.total_price,
    )

    assert isinstance(ledger, ConstraintLedger)
    assert ledger.space.status == "pass"
    assert ledger.budget.status == "pass"
    assert ledger.compatibility.status == "pass"
    assert ledger.installation.status == "pass"
    assert ledger.is_feasible is True


def test_constraint_ledger_budget_overage():
    brief = _sample_brief(budget=50000.0)
    # Even if an offerable configuration is found or manually built with total > budget:
    catalog = {p.id: p for p in get_catalog()}
    selected = [
        catalog["vanity_48_premium"],
        catalog["basin_undermount_single_hole"],
        catalog["faucet_standard_single"],
        catalog["toilet_standard_one_piece"],
        catalog["shower_standard_efficient"],
    ]
    room = brief_to_constraints(brief)
    report = validate_configuration(selected, room)
    water = estimate_water_impact(selected, brief.usage)
    total_price = sum(p.price or 0 for p in selected)

    ledger = build_constraint_ledger(
        report=report,
        water=water,
        budget_limit=brief.budget,
        total_price=total_price,
    )

    assert ledger.budget.status == "fail"
    assert ledger.budget.blocking_count == 1
    assert ledger.is_feasible is False


def test_constraint_ledger_verification_preservation():
    # When rough-in is not measured, it must show as a warning in installation/verification, NOT fail
    brief = BathroomBrief(
        room_width_ft=6.0,
        room_length_ft=8.0,
        budget=250000.0,
        required_categories=["toilet"],
        toilet_rough_in_in=None,  # Unmeasured
    )
    plan_response = create_plan(brief, "test_proj_unverified")
    assert plan_response.status == "ok"
    candidate = plan_response.candidates[0]

    ledger = build_constraint_ledger(
        report=candidate.constraint_report,
        water=candidate.water_impact,
        budget_limit=brief.budget,
        total_price=candidate.total_price,
    )

    assert ledger.installation.status == "warning"
    assert ledger.verification.status == "warning"
    assert ledger.is_feasible is True
    assert ledger.has_pending_verifications is True


def test_design_state_creation_and_fields():
    brief = _sample_brief(budget=250000.0)
    plan_response = create_plan(brief, "test_proj_state")
    candidate = plan_response.candidates[0]

    state = create_design_state_from_candidate(
        candidate=candidate,
        brief=brief,
        project_id="test_proj_state",
        version_id="v1",
        version_number=1,
    )

    assert state.version_id == "v1"
    assert state.version_number == 1
    assert state.project_id == "test_proj_state"
    assert state.room_width_ft == 6.0
    assert state.room_length_ft == 8.0
    assert state.total_price == candidate.total_price
    assert state.remaining_budget == candidate.remaining_budget
    assert len(state.selected_products) == len(candidate.products)
    assert len(state.decision_records) == len(candidate.products)
    assert state.ledger.is_feasible is True

    # Test serialization
    dumped = state.model_dump()
    assert dumped["version_id"] == "v1"
    reloaded = DesignState.model_validate(dumped)
    assert reloaded.total_price == state.total_price


def test_design_state_diff_between_v1_and_v2():
    brief = _sample_brief(budget=250000.0)
    catalog = {p.id: p for p in get_catalog()}

    # V1: 48" vanity, single basin, single faucet, standard toilet, premium shower
    v1_products = [
        catalog["vanity_48_premium"],  # 76,000
        catalog["basin_undermount_single_hole"],  # 12,500
        catalog["faucet_standard_single"],  # 14,500
        catalog["toilet_standard_one_piece"],  # 32,000
        catalog["shower_premium_rainhead"],  # 62,000
    ]
    room_v1 = brief_to_constraints(brief)
    report_v1 = validate_configuration(v1_products, room_v1)
    water_v1 = estimate_water_impact(v1_products, brief.usage)
    layout_v1 = build_layout(v1_products, room_v1)
    total_v1 = sum(p.price or 0 for p in v1_products)

    state_v1 = DesignState(
        project_id="diff_test_proj",
        version_id="v1",
        version_number=1,
        room_width_ft=6.0,
        room_length_ft=8.0,
        selected_products=v1_products,
        total_price=total_v1,
        budget_limit=brief.budget,
        remaining_budget=brief.budget - total_v1,
        layout=layout_v1,
        constraint_report=report_v1,
        water_impact=water_v1,
        ledger=build_constraint_ledger(report_v1, water_v1, brief.budget, total_v1),
        decision_records=[],
    )

    # V2: Upgrade vanity to 60" double (+32,000), swap shower to standard efficient (-34,000)
    v2_products = [
        catalog["vanity_60_double"],  # 108,000 (+32,000)
        catalog["basin_undermount_single_hole"],  # 12,500
        catalog["faucet_standard_single"],  # 14,500
        catalog["toilet_standard_one_piece"],  # 32,000
        catalog["shower_standard_efficient"],  # 28,000 (-34,000)
    ]
    report_v2 = validate_configuration(v2_products, room_v1)
    water_v2 = estimate_water_impact(v2_products, brief.usage)
    layout_v2 = build_layout(v2_products, room_v1)
    total_v2 = sum(p.price or 0 for p in v2_products)

    state_v2 = DesignState(
        project_id="diff_test_proj",
        version_id="v2",
        version_number=2,
        parent_version_id="v1",
        room_width_ft=6.0,
        room_length_ft=8.0,
        selected_products=v2_products,
        total_price=total_v2,
        budget_limit=brief.budget,
        remaining_budget=brief.budget - total_v2,
        layout=layout_v2,
        constraint_report=report_v2,
        water_impact=water_v2,
        ledger=build_constraint_ledger(report_v2, water_v2, brief.budget, total_v2),
        decision_records=[
            DecisionRecord(
                category="vanity",
                action="designer_change",
                product_id="vanity_60_double",
                product_name=catalog["vanity_60_double"].name,
                rationale="Client requested 60 inch vanity.",
            ),
            DecisionRecord(
                category="shower",
                action="tradeoff_accepted",
                product_id="shower_standard_efficient",
                product_name=catalog["shower_standard_efficient"].name,
                rationale="Compensated shower tier to remain within ₹250,000 budget.",
            ),
        ],
    )

    diff = compute_design_state_diff(state_v1, state_v2)

    assert isinstance(diff, DesignStateDiff)
    assert diff.from_version == "v1"
    assert diff.to_version == "v2"
    assert [p.id for p in diff.added_products] == ["vanity_60_double", "shower_standard_efficient"]
    assert [p.id for p in diff.removed_products] == ["vanity_48_premium", "shower_premium_rainhead"]
    assert sorted(diff.modified_categories) == ["shower", "vanity"]
    # Total V1 = 76000 + 12500 + 14500 + 32000 + 62000 = 197,000
    # Total V2 = 108000 + 12500 + 14500 + 32000 + 28000 = 195,000
    # Price delta = -2,000 (net savings of 2,000!)
    assert diff.price_delta == -2000.0
    assert diff.remaining_budget_delta == 2000.0


def test_version_history_lifecycle():
    history = VersionHistory(project_id="test_history_proj")
    assert history.active_version_id is None

    # Add v1
    brief = _sample_brief(budget=250000.0)
    plan_response = create_plan(brief, "test_history_proj")
    state_v1 = create_design_state_from_candidate(
        candidate=plan_response.candidates[0],
        brief=brief,
        project_id="test_history_proj",
        version_id="v1",
        version_number=1,
    )
    history.add_version(state_v1)
    assert history.active_version_id == "v1"
    assert history.get_active() == state_v1
    assert history.next_version_id() == "v2"

    # Add v2
    state_v2 = state_v1.model_copy(
        update={
            "version_id": "v2",
            "version_number": 2,
            "parent_version_id": "v1",
            "total_price": state_v1.total_price + 10000.0,
        }
    )
    history.add_version(state_v2)
    assert history.active_version_id == "v2"
    assert history.get_version("v1") == state_v1
    assert history.get_version("v2") == state_v2

    diff = history.diff("v1", "v2")
    assert diff.price_delta == 10000.0


def test_project_store_integrates_version_history():
    store.clear()
    brief = _sample_brief(budget=250000.0)
    project_id = store.new_id()

    plan_response = create_plan(brief, project_id)
    store.save(plan_response)

    # Automatically created V1 in VersionHistory
    history = store.get_history(project_id)
    assert history is not None
    assert history.active_version_id == "v1"

    v1_state = store.get_design_state(project_id)
    assert v1_state is not None
    assert v1_state.version_id == "v1"
    assert v1_state.total_price == plan_response.candidates[0].total_price

    # Add V2 directly
    v2_state = v1_state.model_copy(
        update={
            "version_id": "v2",
            "version_number": 2,
            "parent_version_id": "v1",
            "total_price": v1_state.total_price + 5000,
        }
    )
    store.save_design_state(v2_state)

    active = store.get_design_state(project_id)
    assert active is not None
    assert active.version_id == "v2"
    assert store.get_design_state(project_id, "v1").version_id == "v1"
