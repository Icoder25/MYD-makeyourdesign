"""End-to-end API tests.

These exercise the pipeline the way the frontend and the demo will, including
the interaction the product is built around: a request that cannot be satisfied,
explained, offered alternatives, and recomputed after the user chooses.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.services.store import store

GOLDEN_BRIEF = {
    "room_width_ft": 6,
    "room_length_ft": 8,
    "budget": 250000,
    "door": {"wall": "south", "offset_in": 6, "width_in": 30},
    "electrical_available": True,
    "preferred_styles": ["modern", "minimalist"],
}

IMPOSSIBLE_BRIEF = {
    **GOLDEN_BRIEF,
    "required_categories": ["vanity", "basin", "faucet", "smart_toilet", "smart_shower", "bathtub"],
}


@pytest.fixture()
def client() -> TestClient:
    store.clear()
    return TestClient(create_app())


def test_health_reports_deterministic_planner_available_without_any_api_key(client) -> None:
    body = client.get("/api/v1/health").json()

    assert body["status"] == "ok"
    assert body["catalog_loaded"] is True
    assert body["deterministic_planner_available"] is True


def test_catalog_endpoint_ships_its_data_disclaimer(client) -> None:
    body = client.get("/api/v1/catalog").json()

    assert body["count"] >= 25
    assert "illustrative" in body["data_disclaimer"]
    assert "not KOHLER pricing" in body["data_disclaimer"]


def test_golden_path_returns_ranked_candidates(client) -> None:
    body = client.post("/api/v1/plan", json=GOLDEN_BRIEF).json()

    assert body["status"] == "ok"
    assert 1 <= len(body["candidates"]) <= 3
    for candidate in body["candidates"]:
        assert candidate["constraint_report"]["offerable"] is True
        assert candidate["total_price"] <= GOLDEN_BRIEF["budget"]
        assert candidate["remaining_budget"] >= 0


def test_every_candidate_carries_layout_water_and_explanation(client) -> None:
    body = client.post("/api/v1/plan", json=GOLDEN_BRIEF).json()

    candidate = body["candidates"][0]
    assert candidate["layout"]["placed"], "a candidate must carry solved geometry for the plan view"
    assert candidate["water_impact"]["status"] in {"calculated", "insufficient_data"}
    assert candidate["explanation"]
    assert candidate["explanation_source"] == "deterministic_template"


def test_response_states_who_computed_the_numbers(client) -> None:
    """The audit trail a judge asks for: no figure is attributed to the LLM."""
    body = client.post("/api/v1/plan", json=GOLDEN_BRIEF).json()

    computed_by = body["meta"]["computed_by"]
    assert "constraint_engine" in computed_by
    assert "layout_solver" in computed_by
    assert "sustainability_calculator" in computed_by
    assert "llm" not in computed_by


def test_candidates_offer_genuinely_different_trade_offs(client) -> None:
    body = client.post("/api/v1/plan", json=GOLDEN_BRIEF).json()

    labels = [candidate["label"] for candidate in body["candidates"]]
    assert len(set(labels)) == len(labels)
    product_sets = [
        frozenset(p["id"] for p in candidate["products"]) for candidate in body["candidates"]
    ]
    assert len(set(product_sets)) == len(product_sets)


def test_impossible_request_is_refused_with_a_structured_explanation(client) -> None:
    """The product's core interaction: say no, say why, and say what would help."""
    body = client.post("/api/v1/plan", json=IMPOSSIBLE_BRIEF).json()

    assert body["status"] == "no_fully_compliant_configuration"
    assert body["candidates"] == []

    conflict = body["conflict"]
    assert conflict["status"] == "NO_FULLY_COMPLIANT_CONFIGURATION"
    assert conflict["violated_constraints"]
    assert conflict["possible_relaxations"]
    assert any(item["constraint"] == "layout_fit" for item in conflict["violated_constraints"])


def test_conflict_offers_a_spatial_way_out_not_just_a_budget_one(client) -> None:
    body = client.post("/api/v1/plan", json=IMPOSSIBLE_BRIEF).json()

    constraints = {item["constraint"] for item in body["conflict"]["possible_relaxations"]}
    assert "layout_fit" in constraints or "category_requirements" in constraints


def test_user_chooses_the_trade_off_and_the_plan_is_recomputed(client) -> None:
    created = client.post("/api/v1/plan", json=IMPOSSIBLE_BRIEF).json()
    assert created["status"] == "no_fully_compliant_configuration"

    resolved = client.post(
        f"/api/v1/plan/{created['project_id']}/resolve",
        json={"relaxation": "drop_category", "category": "bathtub"},
    ).json()

    assert resolved["status"] == "ok"
    assert resolved["candidates"]
    assert resolved["project_id"] == created["project_id"]
    assert "bathtub" not in resolved["brief"]["required_categories"]


def test_increasing_the_budget_resolves_a_budget_conflict(client) -> None:
    tight = {
        **GOLDEN_BRIEF,
        "budget": 180000,
        "required_categories": ["vanity", "basin", "faucet", "smart_toilet", "smart_shower"],
    }
    created = client.post("/api/v1/plan", json=tight).json()
    assert created["status"] == "no_fully_compliant_configuration"

    resolved = client.post(
        f"/api/v1/plan/{created['project_id']}/resolve",
        json={"relaxation": "increase_budget", "budget": 300000},
    ).json()

    assert resolved["status"] == "ok"
    assert all(c["total_price"] <= 300000 for c in resolved["candidates"])


def test_resolve_refuses_to_lower_a_budget_silently(client) -> None:
    created = client.post("/api/v1/plan", json=GOLDEN_BRIEF).json()

    response = client.post(
        f"/api/v1/plan/{created['project_id']}/resolve",
        json={"relaxation": "increase_budget", "budget": 1000},
    )

    assert response.status_code == 422


def test_resolve_rejects_dropping_a_category_that_is_not_required(client) -> None:
    created = client.post("/api/v1/plan", json=GOLDEN_BRIEF).json()

    response = client.post(
        f"/api/v1/plan/{created['project_id']}/resolve",
        json={"relaxation": "drop_category", "category": "helipad"},
    )

    assert response.status_code == 422


def test_confirming_electrical_availability_clears_that_verification(client) -> None:
    unknown_power = {**GOLDEN_BRIEF, "electrical_available": None,
                     "required_categories": ["vanity", "basin", "faucet", "smart_toilet"]}
    created = client.post("/api/v1/plan", json=unknown_power).json()
    assert created["status"] == "ok"
    assert any(
        "Electrical availability is unknown" in note
        for note in created["candidates"][0]["verification_requirements"]
    )

    resolved = client.post(
        f"/api/v1/plan/{created['project_id']}/resolve",
        json={"relaxation": "confirm_electrical"},
    ).json()

    assert not any(
        "Electrical availability is unknown" in note
        for note in resolved["candidates"][0]["verification_requirements"]
    )


def test_missing_dimensions_do_not_crash_and_are_reported(client) -> None:
    """CASE D: no dimensions. The system must degrade, not fail."""
    body = client.post("/api/v1/plan", json={"budget": 250000}).json()

    assert body["status"] in {"ok", "no_fully_compliant_configuration"}
    assert any("Room dimensions were not supplied" in note for note in body["meta"]["notes"])


def test_unknown_project_id_returns_404(client) -> None:
    assert client.get("/api/v1/plan/does-not-exist").status_code == 404
    assert (
        client.post(
            "/api/v1/plan/does-not-exist/resolve",
            json={"relaxation": "confirm_electrical"},
        ).status_code
        == 404
    )


def test_absurd_input_is_rejected_by_validation_not_by_a_crash(client) -> None:
    assert client.post("/api/v1/plan", json={"room_width_ft": -5}).status_code == 422
    assert client.post("/api/v1/plan", json={"room_width_ft": 9999}).status_code == 422
    assert client.post("/api/v1/plan", json={"budget": -1}).status_code == 422


def test_plan_can_be_retrieved_after_creation(client) -> None:
    created = client.post("/api/v1/plan", json=GOLDEN_BRIEF).json()

    fetched = client.get(f"/api/v1/plan/{created['project_id']}").json()

    assert fetched["project_id"] == created["project_id"]
    assert len(fetched["candidates"]) == len(created["candidates"])
