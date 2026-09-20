"""Tests for Phase 2: DesignPulse Dependency Graph, Change Impact Engine, and Golden Scenario.
"""

import pytest

from backend.api.schemas import BathroomBrief
from backend.catalog import get_catalog
from backend.constraints import (
    BathroomConstraints,
    build_layout,
    validate_configuration,
)
from backend.designpulse import (
    BathroomDependencyGraph,
    ChangeImpactEngine,
    DependencyClass,
    DesignModification,
    DesignState,
    ImpactReport,
    TradeoffOption,
    apply_tradeoff,
    build_constraint_ledger,
    compute_design_state_diff,
    create_design_state_from_candidate,
    dependency_graph,
    impact_engine,
)
from backend.services.planner import create_plan
from backend.sustainability.calculator import estimate_water_impact


@pytest.fixture
def catalog_map():
    return {p.id: p for p in get_catalog()}


@pytest.fixture
def golden_v1_state(catalog_map):
    """Initial baseline V1 state:

    6 × 8 ft bathroom, ₹250,000 budget.
    Vanity: 48" premium (₹76,000)
    Basin: undermount single hole (₹12,500)
    Faucet: standard single (₹14,500)
    Toilet: standard one piece (₹32,000)
    Shower: premium rainhead (₹62,000)
    Total: ₹197,000 (₹53,000 unspent)
    """
    brief = BathroomBrief(
        room_width_ft=6.0,
        room_length_ft=8.0,
        ceiling_height_ft=8.0,
        budget=250000.0,
        required_categories=["vanity", "basin", "faucet", "toilet", "shower"],
        electrical_available=True,
        toilet_rough_in_in=12.0,
    )

    selected = [
        catalog_map["vanity_48_premium"],
        catalog_map["basin_undermount_single_hole"],
        catalog_map["faucet_standard_single"],
        catalog_map["toilet_standard_one_piece"],
        catalog_map["shower_premium_rainhead"],
    ]

    room = BathroomConstraints(
        room_width_ft=brief.room_width_ft,
        room_length_ft=brief.room_length_ft,
        ceiling_height_ft=brief.ceiling_height_ft,
        budget=brief.budget,
        required_categories=[p.category for p in selected],
    )

    layout = build_layout(selected, room)
    report = validate_configuration(selected, room, layout=layout)
    water = estimate_water_impact(selected, brief.usage)
    total_price = sum(p.price or 0.0 for p in selected)

    return DesignState(
        project_id="golden_demo_proj",
        version_id="v1",
        version_number=1,
        room_width_ft=6.0,
        room_length_ft=8.0,
        selected_products=selected,
        total_price=total_price,
        budget_limit=brief.budget,
        remaining_budget=brief.budget - total_price,
        layout=layout,
        constraint_report=report,
        water_impact=water,
        ledger=build_constraint_ledger(report, water, brief.budget, total_price),
        decision_records=[],
    )


def test_dependency_graph_classes_and_query():
    """Verify dependency graph distinguishes hard constraints, heuristics, and verifications."""
    deps = dependency_graph.get_dependencies_for_category("vanity")
    targets = {d.target: d.dependency_class for d in deps}

    # Hard constraints
    assert targets["space"] == DependencyClass.HARD_CONSTRAINT
    assert targets["budget"] == DependencyClass.HARD_CONSTRAINT
    assert targets["basin"] == DependencyClass.HARD_CONSTRAINT

    # Model specific requirement
    assert targets["faucet"] == DependencyClass.MODEL_SPECIFIC_REQUIREMENT

    # Design heuristic
    assert targets["storage"] == DependencyClass.DESIGN_HEURISTIC

    # Unknown / requires verification
    assert targets["installation"] == DependencyClass.UNKNOWN_VERIFICATION


def test_affected_and_unaffected_partitioning():
    """Verify affected vs unaffected partitioning when vanity is changed."""
    all_categories = ["vanity", "basin", "faucet", "toilet", "shower", "storage"]
    affected, unaffected = dependency_graph.partition_affected_categories(
        changed_category="vanity",
        all_present_categories=all_categories,
    )

    # Directly related or heuristic targets
    assert "vanity" in affected
    assert "basin" in affected
    assert "faucet" in affected
    assert "storage" in affected

    # Unrelated fixtures
    assert "toilet" in unaffected
    assert "shower" in unaffected


def test_golden_scenario_vanity_48_to_60_impact(golden_v1_state, catalog_map):
    """GOLDEN TEST:

    Designer modifies: 48" vanity -> 60" vanity.
    ImpactReport must contain:
    - exact change
    - dimensional delta (+12" width)
    - budget delta (+₹32,000)
    - affected categories
    - unaffected categories
    - spatial result (IRC compliant)
    - compatibility result
    - budget result
    - at least 2 trade-off candidates
    """
    v1_original_price = golden_v1_state.total_price
    v1_original_products = [p.id for p in golden_v1_state.selected_products]

    modification = DesignModification(
        category="vanity",
        action="replace_product",
        target_product_id="vanity_60_double",
        target_dimension={"width_in": 60.0},
        natural_language_request="Increase vanity to 60 inches",
    )

    report = impact_engine.compute_impact(golden_v1_state, modification)

    assert isinstance(report, ImpactReport)
    assert report.changed_category == "vanity"
    assert report.previous_product.id == "vanity_48_premium"
    assert report.new_product.id == "vanity_60_double"

    # 1. Dimensional Delta
    assert report.dimensional_delta["width_in"] == 12.0
    assert report.dimensional_delta["depth_in"] == 0.0

    # 2. Price & Budget Delta
    # vanity_48: 76,000 -> vanity_60: 108,000 (+32,000)
    assert report.price_delta == 32000.0
    assert report.new_total_price == 197000.0 + 32000.0  # 229,000
    assert report.budget_status == "pass"  # 229,000 <= 250,000

    # 3. Spatial & Compatibility Results
    assert report.spatial_status == "pass"
    assert report.compatibility_status == "pass"

    # 4. Affected vs Unaffected
    assert "vanity" in report.affected_categories
    assert "toilet" in report.unaffected_categories
    assert "shower" in report.unaffected_categories

    # 5. Dependency Evaluations
    eval_targets = {e.target: e for e in report.dependency_evaluations}
    assert "space" in eval_targets
    assert "budget" in eval_targets
    assert "faucet" in eval_targets
    assert "toilet" in eval_targets
    assert eval_targets["toilet"].status == "unaffected"
    assert eval_targets["shower"].status == "unaffected"

    # 6. At least 2 Trade-off Candidates
    assert len(report.candidate_tradeoffs) >= 2
    strategies = {t.strategy for t in report.candidate_tradeoffs}
    assert "stretch_budget" in strategies or "compensate_budget" in strategies

    # 7. V1 IMMUTABILITY: Ensure V1 state was not mutated in memory
    assert golden_v1_state.total_price == v1_original_price
    assert [p.id for p in golden_v1_state.selected_products] == v1_original_products
    assert golden_v1_state.version_id == "v1"


def test_golden_scenario_budget_overage_impact(golden_v1_state, catalog_map):
    """Test impact report when modification pushes total over budget ceiling."""
    # Set tight budget: ₹210,000 (V1 costs ₹197,000)
    tight_v1 = golden_v1_state.model_copy(
        update={
            "budget_limit": 210000.0,
            "remaining_budget": 210000.0 - golden_v1_state.total_price,  # 13,000
        }
    )

    modification = DesignModification(
        category="vanity",
        target_product_id="vanity_60_double",
    )

    report = impact_engine.compute_impact(tight_v1, modification)

    # 197,000 + 32,000 = 229,000, which exceeds 210,000 by 19,000
    assert report.new_total_price == 229000.0
    assert report.budget_status == "fail"
    assert report.budget_delta == 19000.0

    # Must produce a budget compensating trade-off
    compensating_options = [
        t for t in report.candidate_tradeoffs if t.strategy == "compensate_budget"
    ]
    assert len(compensating_options) >= 1
    best_comp = compensating_options[0]
    # Replaces shower_premium_rainhead (62k) with shower_standard_efficient (28k) -> saves 34k
    # 229,000 - 34,000 = 195,000 <= 210,000
    assert best_comp.resulting_total_price <= 210000.0
    assert best_comp.resulting_is_feasible is True


def test_tradeoff_application_constructs_v2(golden_v1_state, catalog_map):
    """TRADE-OFF TEST:

    Select Trade-off: Keep 60" vanity + replace premium shower with standard efficient shower.
    Expected:
    - V1 remains completely unchanged.
    - V2 is constructed with:
      * 60" vanity
      * standard shower
      * recalculated layout and clearances
      * recalculated total price and budget
      * decision records appended
      * diff between V1 and V2 accurately calculated
    """
    v1_snapshot_total = golden_v1_state.total_price
    v1_snapshot_products = list(golden_v1_state.selected_products)

    # 1. Generate impact report
    modification = DesignModification(
        category="vanity",
        target_product_id="vanity_60_double",
    )
    report = impact_engine.compute_impact(golden_v1_state, modification)

    # 2. Pick the shower compensation trade-off (shower_standard_efficient)
    compensating_tradeoff = next(
        t
        for t in report.candidate_tradeoffs
        if any(s.get("add_id") == "shower_standard_efficient" for s in t.substitutions)
    )

    # 3. Apply tradeoff to build V2
    v2_state = apply_tradeoff(
        current_state=golden_v1_state,
        tradeoff=compensating_tradeoff,
        new_version_id="v2",
    )

    # 4. Verify V1 was NOT mutated
    assert golden_v1_state.version_id == "v1"
    assert golden_v1_state.total_price == v1_snapshot_total
    assert golden_v1_state.selected_products == v1_snapshot_products

    # 5. Verify V2 state integrity
    assert v2_state.version_id == "v2"
    assert v2_state.version_number == 2
    assert v2_state.parent_version_id == "v1"

    v2_products = {p.category: p for p in v2_state.selected_products}
    assert v2_products["vanity"].id == "vanity_60_double"
    assert v2_products["vanity"].dimensions.width_in == 60.0
    assert v2_products["shower"].id == "shower_standard_efficient"
    assert v2_products["toilet"].id == "toilet_standard_one_piece"  # Unaffected!

    # Net price: 197,000 + 32,000 (vanity) - 34,000 (shower) = 195,000
    assert v2_state.total_price == 195000.0
    assert v2_state.remaining_budget == 250000.0 - 195000.0  # 55,000

    # Layout is solved and feasible
    assert v2_state.layout.solved is True
    assert v2_state.ledger.is_feasible is True

    # Decision records contain trade-off rationale
    decision_rationales = [d.rationale for d in v2_state.decision_records]
    assert any("Compensated shower tier" in r for r in decision_rationales)

    # 6. Diff between V1 and V2
    diff = compute_design_state_diff(golden_v1_state, v2_state)
    assert diff.from_version == "v1"
    assert diff.to_version == "v2"
    assert diff.price_delta == -2000.0
    assert sorted(diff.modified_categories) == ["shower", "vanity"]
    assert [p.id for p in diff.added_products] == ["vanity_60_double", "shower_standard_efficient"]
    assert [p.id for p in diff.removed_products] == ["vanity_48_premium", "shower_premium_rainhead"]
