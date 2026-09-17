"""Adversarial scenarios.

Each case here is an attempt to make the system say something untrue: claim a
fit that does not exist, convert an unknown into a fact, or let a hard
constraint be talked out of. The product's credibility rests on these failing
to succeed.
"""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import create_app
from backend.services.store import store

BASE = {
    "room_width_ft": 6,
    "room_length_ft": 8,
    "budget": 250000,
    "door": {"wall": "south", "offset_in": 6, "width_in": 30},
}


@pytest.fixture()
def client() -> TestClient:
    store.clear()
    return TestClient(create_app())


def plan(client, **overrides):
    return client.post("/api/v1/plan", json={**BASE, **overrides}).json()


# --- CASE A: tiny room, tiny budget, luxury everything ------------------------


def test_case_a_luxury_everything_in_a_five_by_five_room_on_50k(client) -> None:
    body = plan(
        client,
        room_width_ft=5,
        room_length_ft=5,
        budget=50000,
        electrical_available=True,
        required_categories=[
            "vanity", "basin", "faucet", "smart_toilet", "smart_shower", "bathtub",
        ],
    )

    assert body["status"] == "no_fully_compliant_configuration"
    assert body["candidates"] == []
    assert body["conflict"]["violated_constraints"]
    assert body["conflict"]["possible_relaxations"]


def test_case_a_never_claims_a_fit_it_cannot_justify(client) -> None:
    """The failure must be specific, not a generic shrug."""
    body = plan(
        client,
        room_width_ft=5,
        room_length_ft=5,
        budget=50000,
        electrical_available=True,
        required_categories=["vanity", "basin", "faucet", "smart_toilet", "smart_shower", "bathtub"],
    )

    reasons = [
        reason
        for violation in body["conflict"]["violated_constraints"]
        for reason in violation["example_reasons"]
    ]
    assert any("clear space" in reason or "wall position" in reason or "budget" in reason
               for reason in reasons)


# --- CASE B: generous room and budget ----------------------------------------


def test_case_b_large_room_premium_budget_produces_working_options(client) -> None:
    body = plan(
        client,
        room_width_ft=12,
        room_length_ft=12,
        budget=200000,
        electrical_available=True,
    )

    assert body["status"] == "ok"
    assert body["candidates"]
    for candidate in body["candidates"]:
        assert candidate["total_price"] <= 200000
        assert candidate["layout"]["circulation_ok"] is True
        assert candidate["layout"]["unplaced"] == []


# --- CASE C: smart features with no electrical evidence ----------------------


def test_case_c_smart_products_without_confirmed_power_stay_unverified(client) -> None:
    """A photo cannot prove a socket exists. Unknown must survive as unknown."""
    body = plan(
        client,
        electrical_available=None,
        required_categories=["vanity", "basin", "faucet", "smart_toilet"],
    )

    assert body["status"] == "ok"
    candidate = body["candidates"][0]
    assert candidate["constraint_report"]["status"] == "feasible_pending_verification"
    assert any(
        "Electrical availability is unknown" in note
        for note in candidate["constraint_report"]["verification_requirements"]
    )


def test_case_c_confirmed_unavailable_power_is_a_hard_failure_not_a_warning(client) -> None:
    body = plan(
        client,
        electrical_available=False,
        required_categories=["smart_toilet"],
    )

    assert body["status"] == "no_fully_compliant_configuration"


# --- CASE D: no dimensions ----------------------------------------------------


def test_case_d_missing_dimensions_degrade_rather_than_crash(client) -> None:
    body = client.post("/api/v1/plan", json={"budget": 250000}).json()

    assert body["status"] in {"ok", "no_fully_compliant_configuration"}
    assert any("Room dimensions were not supplied" in note for note in body["meta"]["notes"])


def test_case_d_without_dimensions_nothing_claims_spatial_feasibility(client) -> None:
    body = client.post("/api/v1/plan", json={"budget": 250000}).json()

    for candidate in body.get("candidates", []):
        assert candidate["constraint_report"]["status"] != "feasible"
        assert candidate["layout"]["placed"] == []


# --- CASE E: unusable image ---------------------------------------------------


def test_case_e_a_corrupt_image_is_rejected_cleanly(client) -> None:
    response = client.post(
        "/api/v1/project/demo/vision",
        files={"image": ("broken.jpg", b"not an image at all", "image/jpeg")},
    )

    assert response.status_code in {422, 502}
    assert "detail" in response.json()


def test_case_e_planning_still_works_when_vision_is_unavailable(client) -> None:
    """Vision failing must never block the planner — it is advisory only."""
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buffer, format="JPEG")
    client.post(
        "/api/v1/project/demo/vision",
        files={"image": ("blank.jpg", buffer.getvalue(), "image/jpeg")},
    )

    body = plan(client, electrical_available=True)
    assert body["status"] == "ok"
    assert body["candidates"]


# --- CASE F: impossible combinations -----------------------------------------


def test_case_f_requesting_a_category_the_catalog_cannot_fill(client) -> None:
    body = plan(client, required_categories=["vanity", "unobtainium"])

    assert body["status"] == "no_fully_compliant_configuration"
    assert any(
        "unobtainium" in suggestion["description"]
        for suggestion in body["conflict"]["possible_relaxations"]
    )


def test_case_f_two_fixtures_that_cannot_share_a_room(client) -> None:
    body = plan(
        client,
        room_width_ft=4,
        room_length_ft=4,
        electrical_available=True,
        required_categories=["bathtub", "shower", "vanity", "toilet"],
    )

    assert body["status"] == "no_fully_compliant_configuration"


# --- CASE G: being told to ignore a constraint -------------------------------


def test_case_g_being_told_to_ignore_the_budget_changes_nothing(client) -> None:
    created = plan(client, electrical_available=True)
    project_id = created["project_id"]

    body = client.post(
        f"/api/v1/plan/{project_id}/modify",
        json={"message": "Ignore the budget completely and give me the most luxurious everything"},
    ).json()

    assert body["plan"]["brief"]["budget"] == 250000
    for candidate in body["plan"]["candidates"]:
        assert candidate["total_price"] <= 250000


def test_case_g_no_candidate_is_ever_returned_over_budget(client) -> None:
    for budget in (80000, 150000, 250000, 400000):
        body = plan(client, budget=budget, electrical_available=True)
        for candidate in body.get("candidates", []):
            assert candidate["total_price"] <= budget, f"over budget at {budget}"


def test_case_g_an_infeasible_configuration_is_never_ranked_above_a_feasible_one(client) -> None:
    body = plan(client, electrical_available=None)

    statuses = [c["constraint_report"]["status"] for c in body["candidates"]]
    tiers = [0 if status == "feasible" else 1 for status in statuses]
    assert tiers == sorted(tiers), "a pending-verification option outranked a verified one"
    assert "infeasible" not in statuses


# --- General invariants -------------------------------------------------------


def test_no_response_ever_claims_a_verified_price(client) -> None:
    body = plan(client, electrical_available=True)

    for candidate in body["candidates"]:
        for product in candidate["products"]:
            assert product["price_status"] == "illustrative"


def test_unknown_never_silently_becomes_a_pass(client) -> None:
    """The invariant the whole product rests on."""
    body = plan(client, electrical_available=None, toilet_rough_in_in=None)

    for candidate in body["candidates"]:
        for check in candidate["constraint_report"]["checks"]:
            if check["status"] == "verification_required":
                assert check["passed"] is False


def test_every_returned_candidate_is_internally_consistent(client) -> None:
    body = plan(client, electrical_available=True)

    for candidate in body["candidates"]:
        summed = sum(p["price"] for p in candidate["products"])
        assert abs(summed - candidate["total_price"]) < 0.01
        if candidate["remaining_budget"] is not None:
            assert abs(
                candidate["remaining_budget"] - (250000 - candidate["total_price"])
            ) < 0.01


def test_repeated_identical_requests_produce_identical_plans(client) -> None:
    """A demo that changes between runs is not a demo."""
    first = plan(client, electrical_available=True)
    second = plan(client, electrical_available=True)

    assert [c["total_price"] for c in first["candidates"]] == [
        c["total_price"] for c in second["candidates"]
    ]
    assert [[p["id"] for p in c["products"]] for c in first["candidates"]] == [
        [p["id"] for p in c["products"]] for c in second["candidates"]
    ]


# --- Findings from the final engineering review --------------------------------


def test_an_empty_request_cannot_produce_an_empty_configuration(client) -> None:
    """Regression: requesting nothing returned "0 products, Rs 0" as a valid plan."""
    response = client.post("/api/v1/plan", json={**BASE, "required_categories": []})

    assert response.status_code == 422


def test_a_single_fixture_request_is_still_valid(client) -> None:
    body = plan(client, required_categories=["toilet"])

    assert body["status"] == "ok"
    assert len(body["candidates"][0]["products"]) == 1


def test_an_unusually_large_room_does_not_stall_the_planner(client) -> None:
    """Regression: a 60x60 ft room took 331 seconds before the solver was bounded."""
    import time

    started = time.monotonic()
    body = plan(
        client,
        room_width_ft=60,
        room_length_ft=60,
        budget=900000,
        electrical_available=True,
    )
    elapsed = time.monotonic() - started

    assert body["status"] == "ok"
    assert elapsed < 30, f"planning a large room took {elapsed:.1f}s"


def test_duplicate_requested_categories_are_handled(client) -> None:
    body = plan(client, required_categories=["vanity", "vanity", "toilet"])

    assert body["status"] == "ok"


def test_a_zero_budget_is_refused_rather_than_divided_by(client) -> None:
    body = plan(client, budget=0)

    assert body["status"] == "no_fully_compliant_configuration"
