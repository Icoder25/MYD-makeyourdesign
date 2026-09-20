"""Integration tests for Phase 3: DesignPulse API, State & History Integration.

Tests cover:
1. POST impact returns valid ImpactReport
2. Impact analysis does not mutate V1
3. POST tradeoff creates V2
4. V1 remains accessible after V2 creation
5. V2 becomes active
6. GET history returns V1 and V2
7. GET diff returns correct product changes
8. Price delta is deterministic
9. Invalid trade-off is rejected (404/422)
10. Unknown product is rejected (404)
11. LLM fallback still works (natural language requests without API key)
12. Golden scenario end-to-end round trip
13. Edge case error handling (unknown project, invalid category, etc.)
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.schemas import BathroomBrief
from backend.catalog import get_catalog
from backend.constraints import (
    BathroomConstraints,
    build_layout,
    validate_configuration,
)
from backend.designpulse import (
    DesignState,
    TradeoffOption,
    build_constraint_ledger,
    create_design_state_from_candidate,
)
from backend.main import create_app
from backend.services.planner import create_plan
from backend.services.store import store
from backend.sustainability.calculator import estimate_water_impact


@pytest.fixture
def client() -> TestClient:
    store.clear()
    return TestClient(create_app())


@pytest.fixture
def catalog_map():
    return {p.id: p for p in get_catalog()}


@pytest.fixture
def golden_project(client, catalog_map) -> str:
    """Setup a project with the exact golden V1 baseline state:

    6 × 8 ft bathroom, ₹250,000 budget.
    Vanity: 48" premium (₹76,000)
    Basin: undermount single hole (₹12,500)
    Faucet: standard single (₹14,500)
    Toilet: standard one piece (₹32,000)
    Shower: premium rainhead (₹62,000)
    Total: ₹197,000 (₹53,000 unspent)
    """
    project_id = "golden_api_proj"

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
        electrical_available=brief.electrical_available,
        toilet_rough_in_in=brief.toilet_rough_in_in,
    )

    layout = build_layout(selected, room)
    report = validate_configuration(selected, room, layout=layout)
    water = estimate_water_impact(selected, brief.usage)
    total_price = sum(p.price or 0.0 for p in selected)

    v1_state = DesignState(
        project_id=project_id,
        version_id="v1",
        version_number=1,
        room_width_ft=6.0,
        room_length_ft=8.0,
        ceiling_height_ft=8.0,
        electrical_available=True,
        toilet_rough_in_in=12.0,
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

    store.save_design_state(v1_state, set_active=True)
    return project_id


# ------------------------------------------------------------------------------
# 1 & 2. POST /impact: valid report and V1 immutability
# ------------------------------------------------------------------------------


def test_post_impact_returns_valid_report_and_preserves_v1(client, golden_project):
    """POST /impact returns structured ImpactReport without mutating V1."""
    v1_before = store.get_design_state(golden_project, "v1")
    assert v1_before is not None
    v1_price = v1_before.total_price
    v1_prods = [p.id for p in v1_before.selected_products]

    payload = {
        "category": "vanity",
        "action": "replace_product",
        "target_product_id": "vanity_60_double",
        "target_dimension": {"width_in": 60.0},
    }
    resp = client.post(f"/api/v1/plan/{golden_project}/impact", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Verify structured ImpactReport fields
    assert data["changed_category"] == "vanity"
    assert data["previous_product"]["id"] == "vanity_48_premium"
    assert data["new_product"]["id"] == "vanity_60_double"
    assert data["dimensional_delta"]["width_in"] == 12.0
    assert data["price_delta"] == 32000.0
    assert data["new_total_price"] == 197000.0 + 32000.0
    assert data["spatial_status"] == "pass"
    assert "vanity" in data["affected_categories"]
    assert "toilet" in data["unaffected_categories"]
    assert len(data["candidate_tradeoffs"]) >= 2

    # Verify V1 IMMUTABILITY: V1 in store is completely unmutated
    v1_after = store.get_design_state(golden_project, "v1")
    assert v1_after is not None
    assert v1_after.total_price == v1_price
    assert [p.id for p in v1_after.selected_products] == v1_prods
    assert v1_after.version_id == "v1"

    # Active version in store is still V1
    active = store.get_design_state(golden_project)
    assert active is not None
    assert active.version_id == "v1"


# ------------------------------------------------------------------------------
# 3, 4, 5. POST /tradeoff: creates V2, preserves V1, activates V2
# ------------------------------------------------------------------------------


def test_post_tradeoff_creates_v2_activates_it_and_preserves_v1(client, golden_project):
    """POST /tradeoff applies selected tradeoff, saving V2 and setting it active."""
    # 1. Run impact to get candidate tradeoffs
    impact_resp = client.post(
        f"/api/v1/plan/{golden_project}/impact",
        json={"category": "vanity", "target_product_id": "vanity_60_double"},
    )
    assert impact_resp.status_code == 200
    tradeoffs = impact_resp.json()["candidate_tradeoffs"]
    assert len(tradeoffs) >= 2

    # Pick the shower compensation trade-off
    comp_tradeoff = next(
        t for t in tradeoffs
        if any(s.get("add_id") == "shower_standard_efficient" for s in t["substitutions"])
    )

    # 2. Apply the tradeoff
    apply_resp = client.post(
        f"/api/v1/plan/{golden_project}/tradeoff",
        json={"tradeoff_id": comp_tradeoff["id"]},
    )
    assert apply_resp.status_code == 200
    apply_data = apply_resp.json()

    assert apply_data["project_id"] == golden_project
    assert apply_data["version_id"] == "v2"
    assert apply_data["version_number"] == 2

    v2_state = apply_data["v2"]
    assert v2_state["version_id"] == "v2"
    assert v2_state["parent_version_id"] == "v1"

    v2_products = {p["category"]: p["id"] for p in v2_state["selected_products"]}
    assert v2_products["vanity"] == "vanity_60_double"
    assert v2_products["shower"] == "shower_standard_efficient"
    assert v2_products["toilet"] == "toilet_standard_one_piece"

    # 3. Diff from V1 is returned directly
    diff = apply_data["diff"]
    assert diff["from_version"] == "v1"
    assert diff["to_version"] == "v2"
    assert diff["price_delta"] == -2000.0  # +32,000 vanity - 34,000 shower
    assert sorted(diff["modified_categories"]) == ["shower", "vanity"]

    # 4. V1 remains accessible in store
    v1_state = store.get_design_state(golden_project, "v1")
    assert v1_state is not None
    assert v1_state.version_id == "v1"
    assert v1_state.total_price == 197000.0

    # 5. V2 is the active state in store
    active = store.get_design_state(golden_project)
    assert active is not None
    assert active.version_id == "v2"
    assert active.total_price == 195000.0


# ------------------------------------------------------------------------------
# 6. GET /history: returns timeline of V1 and V2
# ------------------------------------------------------------------------------


def test_get_history_returns_timeline(client, golden_project):
    """GET /history returns available versions, active version, timestamps, and parentage."""
    # Create V2 via impact + tradeoff
    client.post(
        f"/api/v1/plan/{golden_project}/impact",
        json={"category": "vanity", "target_product_id": "vanity_60_double"},
    )
    last_impact = store.get_last_impact(golden_project)
    chosen_opt = last_impact.candidate_tradeoffs[0]

    client.post(
        f"/api/v1/plan/{golden_project}/tradeoff",
        json={"tradeoff_id": chosen_opt.id},
    )

    # Call history endpoint
    resp = client.get(f"/api/v1/plan/{golden_project}/history")
    assert resp.status_code == 200
    hist = resp.json()

    assert hist["project_id"] == golden_project
    assert hist["active_version_id"] == "v2"
    assert len(hist["versions"]) == 2

    v1_sum = hist["versions"][0]
    assert v1_sum["version_id"] == "v1"
    assert v1_sum["version_number"] == 1
    assert v1_sum["parent_version_id"] is None
    assert v1_sum["is_active"] is False
    assert v1_sum["total_price"] == 197000.0
    assert "T" in v1_sum["timestamp"]

    v2_sum = hist["versions"][1]
    assert v2_sum["version_id"] == "v2"
    assert v2_sum["version_number"] == 2
    assert v2_sum["parent_version_id"] == "v1"
    assert v2_sum["is_active"] is True
    assert "T" in v2_sum["timestamp"]


# ------------------------------------------------------------------------------
# 7 & 8. GET /diff: compares versions and computes deterministic price delta
# ------------------------------------------------------------------------------


def test_get_diff_computes_exact_deltas(client, golden_project):
    """GET /diff compares two versions with exact product changes and price delta."""
    # Generate V2 with shower compensation
    client.post(
        f"/api/v1/plan/{golden_project}/impact",
        json={"category": "vanity", "target_product_id": "vanity_60_double"},
    )
    last_impact = store.get_last_impact(golden_project)
    comp_tradeoff = next(
        t for t in last_impact.candidate_tradeoffs
        if any(s.get("add_id") == "shower_standard_efficient" for s in t.substitutions)
    )
    client.post(
        f"/api/v1/plan/{golden_project}/tradeoff",
        json={"tradeoff_id": comp_tradeoff.id},
    )

    # Call diff endpoint with query parameters
    resp = client.get(f"/api/v1/plan/{golden_project}/diff?from_version=v1&to_version=v2")
    assert resp.status_code == 200
    diff = resp.json()

    assert diff["from_version"] == "v1"
    assert diff["to_version"] == "v2"
    assert diff["price_delta"] == -2000.0
    assert sorted(diff["modified_categories"]) == ["shower", "vanity"]

    added_ids = [p["id"] for p in diff["added_products"]]
    removed_ids = [p["id"] for p in diff["removed_products"]]
    assert "vanity_60_double" in added_ids
    assert "shower_standard_efficient" in added_ids
    assert "vanity_48_premium" in removed_ids
    assert "shower_premium_rainhead" in removed_ids


# ------------------------------------------------------------------------------
# 9. Invalid trade-off is rejected
# ------------------------------------------------------------------------------


def test_invalid_tradeoff_is_rejected(client, golden_project):
    """Applying an unknown or infeasible tradeoff returns 404 or 422."""
    # 1. Unknown tradeoff ID -> 404
    resp = client.post(
        f"/api/v1/plan/{golden_project}/tradeoff",
        json={"tradeoff_id": "nonexistent_tradeoff_xyz"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()

    # 2. Infeasible trade-off passed directly -> 422
    infeasible_option = TradeoffOption(
        id="infeasible_test_opt",
        title="Impossible Option",
        description="Cannot be built",
        strategy="compact_alternative",
        substitutions=[],
        price_delta=0.0,
        resulting_total_price=999999.0,
        resulting_is_feasible=False,
        spatial_summary="Overlaps wall",
        decision_rationale="Infeasible test",
    )
    resp_infeasible = client.post(
        f"/api/v1/plan/{golden_project}/tradeoff",
        json={"tradeoff_id": infeasible_option.id, "tradeoff": infeasible_option.model_dump()},
    )
    assert resp_infeasible.status_code == 422
    assert "infeasible" in resp_infeasible.json()["detail"].lower()


# ------------------------------------------------------------------------------
# 10. Unknown product is rejected
# ------------------------------------------------------------------------------


def test_unknown_product_is_rejected(client, golden_project):
    """Specifying an unknown product ID in modification returns 404."""
    resp = client.post(
        f"/api/v1/plan/{golden_project}/impact",
        json={
            "category": "vanity",
            "action": "replace_product",
            "target_product_id": "vanity_ghost_sku_999",
        },
    )
    assert resp.status_code == 404
    assert "not found in catalog" in resp.json()["detail"].lower()


# ------------------------------------------------------------------------------
# 11. LLM Fallback: Natural language requests work without LLM API key
# ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "phrase",
    [
        "Increase the vanity to 60 inches.",
        "Make the vanity 60 inches.",
        "Client wants a larger vanity.",
        "Vanity 60 inch",
    ],
)
def test_natural_language_phrasings_work_via_deterministic_fallback(
    client, golden_project, phrase
):
    """Natural-language requests map to 60" vanity via deterministic intent fallback."""
    resp = client.post(
        f"/api/v1/plan/{golden_project}/impact",
        json={"message": phrase},
    )
    assert resp.status_code == 200
    report = resp.json()

    assert report["changed_category"] == "vanity"
    assert report["previous_product"]["id"] == "vanity_48_premium"
    assert report["new_product"]["id"] == "vanity_60_double"
    assert report["dimensional_delta"]["width_in"] == 12.0
    assert report["price_delta"] == 32000.0
    assert len(report["candidate_tradeoffs"]) >= 2


# ------------------------------------------------------------------------------
# 12. Full Golden Scenario Round-Trip
# ------------------------------------------------------------------------------


def test_golden_scenario_complete_round_trip(client, golden_project):
    """GOLDEN PATH COMPLETE ROUND-TRIP:

    V1 (48" vanity)
        ↓
    POST /impact ('Increase the vanity to 60 inches.')
        ↓
    ImpactReport (12" delta, +₹32,000, trade-offs)
        ↓
    select trade-off (shower compensation)
        ↓
    POST /tradeoff
        ↓
    V2 (60" vanity + compensated shower)
        ↓
    GET /history (V1 + V2)
        ↓
    GET /diff (V1 → V2 diff)
    """
    # 1. Verify V1 Baseline
    v1_state = store.get_design_state(golden_project)
    assert v1_state.version_id == "v1"
    assert v1_state.get_product("vanity").dimensions.width_in == 48.0
    assert v1_state.total_price == 197000.0

    # 2. Run POST /impact with natural language
    impact_resp = client.post(
        f"/api/v1/plan/{golden_project}/impact",
        json={"message": "Increase the vanity to 60 inches."},
    )
    assert impact_resp.status_code == 200
    report = impact_resp.json()
    assert report["changed_category"] == "vanity"
    assert report["dimensional_delta"]["width_in"] == 12.0
    assert report["price_delta"] == 32000.0

    # 3. Select trade-off
    shower_tradeoff = next(
        t for t in report["candidate_tradeoffs"]
        if any(s.get("add_id") == "shower_standard_efficient" for s in t["substitutions"])
    )

    # 4. POST /tradeoff
    tradeoff_resp = client.post(
        f"/api/v1/plan/{golden_project}/tradeoff",
        json={"tradeoff_id": shower_tradeoff["id"]},
    )
    assert tradeoff_resp.status_code == 200
    v2_data = tradeoff_resp.json()

    assert v2_data["version_id"] == "v2"
    v2_prod_map = {p["category"]: p for p in v2_data["v2"]["selected_products"]}
    assert v2_prod_map["vanity"]["id"] == "vanity_60_double"
    assert v2_prod_map["vanity"]["dimensions"]["width_in"] == 60.0
    assert v2_prod_map["shower"]["id"] == "shower_standard_efficient"
    assert v2_data["v2"]["total_price"] == 195000.0

    # 5. GET /history
    hist_resp = client.get(f"/api/v1/plan/{golden_project}/history")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert history["active_version_id"] == "v2"
    version_ids = [v["version_id"] for v in history["versions"]]
    assert version_ids == ["v1", "v2"]

    # 6. GET /diff
    diff_resp = client.get(f"/api/v1/plan/{golden_project}/diff?from_version=v1&to_version=v2")
    assert diff_resp.status_code == 200
    diff = diff_resp.json()
    assert diff["from_version"] == "v1"
    assert diff["to_version"] == "v2"
    assert diff["price_delta"] == -2000.0
    assert sorted(diff["modified_categories"]) == ["shower", "vanity"]


# ------------------------------------------------------------------------------
# 13. API Error handling checks
# ------------------------------------------------------------------------------


def test_api_error_handling_unknown_project(client):
    """Endpoints return 404 for unknown project id."""
    assert client.post("/api/v1/plan/unknown_123/impact", json={"category": "vanity"}).status_code == 404
    assert client.post("/api/v1/plan/unknown_123/tradeoff", json={"tradeoff_id": "opt1"}).status_code == 404
    assert client.get("/api/v1/plan/unknown_123/history").status_code == 404
    assert client.get("/api/v1/plan/unknown_123/diff").status_code == 404


def test_api_error_handling_invalid_input(client, golden_project):
    """Endpoints return 422 for malformed or missing requests."""
    # Empty request
    assert client.post(f"/api/v1/plan/{golden_project}/impact", json={}).status_code == 422
    # Invalid category
    assert client.post(
        f"/api/v1/plan/{golden_project}/impact",
        json={"category": "unsupported_cat_xyz"},
    ).status_code == 422
    # Category not in current room
    assert client.post(
        f"/api/v1/plan/{golden_project}/impact",
        json={"category": "bathtub"},
    ).status_code == 422
    # Unknown version in diff
    assert client.get(
        f"/api/v1/plan/{golden_project}/diff?from_version=v1&to_version=v99"
    ).status_code == 404
