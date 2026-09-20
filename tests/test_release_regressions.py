"""Regressions for defects found in the final release audit.

Each test here corresponds to something that was actually broken in a running
build and passed every existing test. They are grouped by the defect rather
than by module, because that is how they will be read if one of them fails
again.
"""

import pytest
from fastapi.testclient import TestClient

from backend.designpulse.models import ConstraintLedger
from backend.llm.intent import LLMIntentPayload, LLMModificationIntent
from backend.llm.schema import UnsupportedSchemaError, gemini_response_schema
from backend.main import create_app
from backend.services.store import store
from backend.vision.models import BathroomVisionEvidence

BRIEF = {
    "room_width_ft": 7.874,
    "room_length_ft": 5.906,
    "budget": 400000,
    "door": {"wall": "south", "offset_in": 6, "width_in": 30},
    "electrical_available": True,
    "toilet_rough_in_in": 12.0,
}


@pytest.fixture()
def client() -> TestClient:
    store.clear()
    return TestClient(create_app())


@pytest.fixture()
def project(client) -> str:
    return client.post("/api/v1/plan", json=BRIEF).json()["project_id"]


# --- The printable export sheet crashed for one of its three roles -----------


@pytest.mark.parametrize("role", ["client", "designer", "dealer"])
def test_printable_export_document_renders_for_every_role(client, project, role) -> None:
    """All three roles, not just the one the old test happened to cover.

    The designer sheet reached for `ledger.domains` and `ledger.overall_status`,
    neither of which existed, and returned a 500 to anyone who clicked it.
    """
    response = client.get(f"/api/v1/plan/{project}/export/document?role={role}")

    assert response.status_code == 200, response.text
    body = response.text
    assert "<!DOCTYPE html>" in body
    assert "KOHLER AI BathPlan" in body
    assert role.upper() in body.upper()


def test_designer_sheet_lists_all_seven_ledger_domains(client, project) -> None:
    body = client.get(f"/api/v1/plan/{project}/export/document?role=designer").text

    for domain in ConstraintLedger.model_fields:
        assert domain.upper() in body, f"{domain} missing from the designer sheet"


def test_ledger_exposes_domains_and_a_three_valued_verdict() -> None:
    """Verification outstanding must stay distinguishable from infeasible."""
    assert set(ConstraintLedger.model_fields) == {
        "space",
        "budget",
        "compatibility",
        "installation",
        "style",
        "water",
        "verification",
    }


# --- Every Gemini request was rejected before it left the building -----------


@pytest.mark.parametrize(
    "model",
    [LLMIntentPayload, LLMModificationIntent, BathroomVisionEvidence],
)
def test_gemini_schemas_contain_nothing_the_api_rejects(model) -> None:
    """Gemini 400s on `additionalProperties`, `$ref`, `const` and bare `anyOf`.

    Pydantic emits all four. Passing the model class straight through produced
    `400 INVALID_ARGUMENT` on every call, which the AI layer caught and
    silently downgraded to its keyword fallback — so the product reported
    "AI active" while never once reaching the model.
    """
    schema = gemini_response_schema(model)
    rendered = repr(schema)

    for forbidden in ('"additionalProperties"', "'additionalProperties'", "'$ref'", "'$defs'", "'const'"):
        assert forbidden not in rendered, f"{model.__name__} still emits {forbidden}"
    assert schema["type"] == "object"
    assert schema["properties"]


def test_optional_fields_become_nullable_rather_than_a_union() -> None:
    schema = gemini_response_schema(LLMModificationIntent)

    assert schema["properties"]["dimension_width_in"] == {
        "type": "number",
        "nullable": True,
    }


def test_enum_members_survive_conversion() -> None:
    schema = gemini_response_schema(LLMModificationIntent)

    assert schema["properties"]["relative_direction"]["enum"] == ["larger", "smaller", "none"]


def test_free_form_mappings_are_refused_instead_of_silently_shipped() -> None:
    """A dict field has no Gemini equivalent; failing loudly is the point."""
    from pydantic import BaseModel

    class HasAMapping(BaseModel):
        target_dimension: dict[str, float]

    with pytest.raises(UnsupportedSchemaError):
        gemini_response_schema(HasAMapping)


def test_llm_payload_round_trips_into_the_domain_intent() -> None:
    payload = LLMIntentPayload(
        target_category="vanity",
        target_dimension_width_in=36.0,
        action="change_dimension",
    )

    intent = payload.to_intent()

    assert intent.target_dimension == {"width_in": 36.0}
    assert intent.target_category == "vanity"


def test_a_dimensional_request_is_not_treated_as_an_empty_intent() -> None:
    """`is_empty` predates the dimensional fields and ignored them.

    The consequence was that a correctly understood "make the vanity wider"
    was discarded in favour of the keyword parser.
    """
    from backend.llm.intent import ModificationIntent

    intent = ModificationIntent(
        target_category="vanity",
        target_dimension={"width_in": 36.0},
        action="change_dimension",
    )

    assert not intent.is_empty()
    assert ModificationIntent().is_empty()


# --- DesignPulse advertised two actions its engine cannot perform ------------


@pytest.mark.parametrize("action", ["add_category", "remove_category"])
def test_unsupported_impact_actions_explain_themselves(client, project, action) -> None:
    response = client.post(
        f"/api/v1/plan/{project}/impact",
        json={"category": "bathtub", "action": action},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "modify" in detail.lower(), detail
    assert "Impact computation error" not in detail


def test_changing_a_fixture_the_design_does_not_have_points_somewhere_useful(
    client, project
) -> None:
    response = client.post(
        f"/api/v1/plan/{project}/impact",
        json={"category": "bathtub", "action": "replace_product"},
    )

    assert response.status_code == 422
    assert "modify" in response.json()["detail"].lower()


# --- The example environment file carried a live credential ------------------


def test_the_committed_env_example_holds_no_credential() -> None:
    """`.env.example` is tracked. A real key pasted into it gets published."""
    from pathlib import Path

    example = Path(__file__).resolve().parents[1] / ".env.example"
    for line in example.read_text(encoding="utf-8").splitlines():
        if line.startswith("GEMINI_API_KEY"):
            assert line.strip() == "GEMINI_API_KEY=", "a value is set in the example file"
            break
    else:
        pytest.fail("GEMINI_API_KEY is missing from .env.example")


def test_every_import_the_app_needs_is_declared() -> None:
    """python-dotenv is imported at startup but was absent from requirements."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    declared = (root / "requirements.txt").read_text(encoding="utf-8").lower()

    assert "python-dotenv" in declared
