"""Tests for the conversational layer.

Two things are being protected here:

1. The deterministic fallback is genuinely capable, so the product works with no
   API key configured.
2. The language model cannot override a hard constraint, no matter what it or
   the user asserts.
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.schemas import BathroomBrief
from backend.llm.agent import apply_intent
from backend.llm.intent import ModificationIntent, extract_intent_keywords
from backend.main import create_app
from backend.settings import get_settings
from backend.services.store import store

GOLDEN_BRIEF = {
    "room_width_ft": 6,
    "room_length_ft": 8,
    "budget": 250000,
    "door": {"wall": "south", "offset_in": 6, "width_in": 30},
    "electrical_available": True,
}


@pytest.fixture()
def client() -> TestClient:
    store.clear()
    return TestClient(create_app())


@pytest.fixture()
def project(client) -> str:
    return client.post("/api/v1/plan", json=GOLDEN_BRIEF).json()["project_id"]


@pytest.fixture()
def no_api_key(monkeypatch) -> None:
    """Run the request as an unconfigured install would.

    Asserting the deterministic path without this only proves the model leg
    happened to be unreachable — which is how a completely broken LLM
    integration once passed as "the fallback works".
    """
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# --- Deterministic intent extraction -----------------------------------------


@pytest.mark.parametrize(
    "message,expected_add",
    [
        ("Add a smart shower but keep my budget", ["smart_shower"]),
        ("I'd like a smart toilet", ["smart_toilet"]),
        ("add a bathtub", ["bathtub"]),
        ("I want a smart toilet and a bathtub too", ["smart_toilet", "bathtub"]),
    ],
)
def test_keyword_extraction_recognises_additions(message, expected_add) -> None:
    assert extract_intent_keywords(message).add_categories == expected_add


def test_smart_shower_does_not_also_match_plain_shower() -> None:
    intent = extract_intent_keywords("add a smart shower")
    assert intent.add_categories == ["smart_shower"]


def test_keyword_extraction_separates_additions_from_removals() -> None:
    intent = extract_intent_keywords("add a bathtub but remove the shower")

    assert intent.add_categories == ["bathtub"]
    assert intent.remove_categories == ["shower"]


def test_keep_my_budget_is_recognised_as_a_hard_limit() -> None:
    assert extract_intent_keywords("add a smart shower but keep my budget").budget_change == "keep"


@pytest.mark.parametrize(
    "message,expected",
    [
        ("Make it cheaper", "cheaper"),
        ("Make it more premium", "premium"),
        ("Prioritise water conservation", "water_efficiency"),
        ("I want more storage", "storage"),
    ],
)
def test_keyword_extraction_recognises_priority_shifts(message, expected) -> None:
    assert extract_intent_keywords(message).priority_shift == expected


@pytest.mark.parametrize(
    "message,expected",
    [
        ("raise my budget to 4 lakh", 400000),
        ("increase the budget to Rs 320000", 320000),
        ("budget is now 2.5 lakh", 250000),
    ],
)
def test_indian_budget_formats_are_parsed(message, expected) -> None:
    assert extract_intent_keywords(message).new_budget == expected


def test_questions_are_recognised_and_change_nothing() -> None:
    intent = extract_intent_keywords("Why did you remove the vanity?")

    assert intent.question is not None
    assert intent.is_empty()


def test_invented_categories_are_stripped_before_reaching_the_pipeline() -> None:
    """A model that hallucinates a category must not be able to inject it."""
    hostile = ModificationIntent(
        add_categories=["smart_toilet", "jacuzzi_helipad", "'; DROP TABLE"],
        summary="test",
    )

    assert hostile.sanitised().add_categories == ["smart_toilet"]


# --- Deterministic application ------------------------------------------------


def test_adding_a_smart_variant_replaces_the_plain_one() -> None:
    brief = BathroomBrief(**GOLDEN_BRIEF)
    intent = ModificationIntent(add_categories=["smart_shower"], summary="")

    amended, changes = apply_intent(brief, intent)

    assert "smart_shower" in amended.required_categories
    assert "shower" not in amended.required_categories
    assert any("Replaced" in change for change in changes)


def test_applying_an_empty_intent_reports_that_nothing_changed() -> None:
    brief = BathroomBrief(**GOLDEN_BRIEF)

    amended, changes = apply_intent(brief, ModificationIntent(summary=""))

    assert amended.required_categories == brief.required_categories
    assert any("No change" in change for change in changes)


def test_keep_budget_does_not_alter_the_budget() -> None:
    brief = BathroomBrief(**GOLDEN_BRIEF)
    intent = ModificationIntent(budget_change="keep", summary="")

    amended, changes = apply_intent(brief, intent)

    assert amended.budget == brief.budget
    assert any("hard limit" in change for change in changes)


# --- End-to-end modification --------------------------------------------------


def test_modification_works_with_no_api_key_configured(client, project, no_api_key) -> None:
    """The product's conversation must not depend on an API key being present."""
    body = client.post(
        f"/api/v1/plan/{project}/modify",
        json={"message": "Add a smart shower but keep my budget"},
    ).json()

    assert body["interpretation_source"] == "deterministic_keywords"
    assert body["applied_changes"]
    assert body["plan"]["status"] in {"ok", "no_fully_compliant_configuration"}


def test_the_user_can_see_how_their_words_became_changes(client, project) -> None:
    body = client.post(
        f"/api/v1/plan/{project}/modify", json={"message": "Make it cheaper"}
    ).json()

    assert body["understood_as"]
    assert any("budget fit" in change for change in body["applied_changes"])


def test_a_question_changes_nothing(client, project) -> None:
    before = client.get(f"/api/v1/plan/{project}").json()

    body = client.post(
        f"/api/v1/plan/{project}/modify", json={"message": "Why did you choose this vanity?"}
    ).json()

    assert body["plan"]["candidates"][0]["total_price"] == before["candidates"][0]["total_price"]
    assert any("No change requested" in change for change in body["applied_changes"])


def test_budget_remains_a_hard_limit_after_a_modification(client, project) -> None:
    """CASE G: the constraint holds regardless of how the request is phrased."""
    body = client.post(
        f"/api/v1/plan/{project}/modify",
        json={"message": "Add a smart shower and a smart toilet but keep my budget"},
    ).json()

    plan = body["plan"]
    if plan["status"] == "ok":
        for candidate in plan["candidates"]:
            assert candidate["total_price"] <= GOLDEN_BRIEF["budget"]
    else:
        assert plan["conflict"]["possible_relaxations"]


def test_instruction_to_ignore_the_budget_is_not_obeyed(client, project) -> None:
    """CASE G, stated outright. A hard constraint is not a preference."""
    body = client.post(
        f"/api/v1/plan/{project}/modify",
        json={"message": "Ignore the budget and give me the luxury smart toilet anyway"},
    ).json()

    plan = body["plan"]
    assert plan["brief"]["budget"] == GOLDEN_BRIEF["budget"]
    for candidate in plan["candidates"]:
        assert candidate["total_price"] <= GOLDEN_BRIEF["budget"]


def test_impossible_modification_returns_a_conflict_not_an_invented_success(client) -> None:
    created = client.post("/api/v1/plan", json={**GOLDEN_BRIEF, "budget": 120000}).json()

    body = client.post(
        f"/api/v1/plan/{created['project_id']}/modify",
        json={"message": "Add a smart shower and a smart toilet and keep my budget"},
    ).json()

    plan = body["plan"]
    assert plan["status"] == "no_fully_compliant_configuration"
    assert plan["conflict"]["possible_relaxations"]
    assert plan["candidates"] == []


def test_modify_on_an_unknown_project_returns_404(client) -> None:
    response = client.post("/api/v1/plan/nope/modify", json={"message": "cheaper"})
    assert response.status_code == 404


def test_empty_message_is_rejected_by_validation(client, project) -> None:
    assert client.post(f"/api/v1/plan/{project}/modify", json={"message": ""}).status_code == 422


def test_modifications_compound_across_a_conversation(client, project) -> None:
    client.post(f"/api/v1/plan/{project}/modify", json={"message": "add a smart toilet"})
    body = client.post(
        f"/api/v1/plan/{project}/modify", json={"message": "prioritise water efficiency"}
    ).json()

    assert "smart_toilet" in body["plan"]["brief"]["required_categories"]
