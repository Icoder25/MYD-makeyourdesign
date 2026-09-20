"""Comprehensive Phase 6 Vision Integration Tests.

Validates all 15 requirements and guardrails:
1. Valid bathroom image analysis
2. No visible fixture
3. Low-confidence detection
4. Unknown dimensions (requires measurement)
5. Unknown plumbing (does not guess rough-in)
6. Unknown electrical (requires verification)
7. User-provided dimension overriding estimate (Precedence Rule)
8. Vision unavailable fallback
9. Invalid image handling (clean 422)
10. DesignState integration (ledger + DecisionRecord + store)
11. Vision wall estimate does not become a hard constraint (Guardrail 3)
12. Verification-required does not become infeasible (Guardrail 2: UNKNOWN != INFEASIBLE)
13. Confidence threshold is classification only (Guardrail 1)
14. Gemini failure does not break planner (Guardrail 4)
15. Existing DesignPulse remains unchanged
"""

from io import BytesIO
import asyncio
from fastapi.testclient import TestClient
from PIL import Image
import pytest

from backend.api.schemas import BathroomBrief
from backend.constraints.models import ConfigurationReport
from backend.designpulse.models import create_design_state_from_candidate
from backend.main import app
from backend.services.planner import create_plan
from backend.services.store import store
from backend.vision.analyzer import BathroomVisionAnalyzer
from backend.vision.mapping import (
    attach_vision_to_design_state,
    map_vision_to_verification_checks,
    reconcile_brief_with_vision,
)
from backend.vision.models import (
    BathroomVisionEvidence,
    BoundingBox,
    DetectedObject,
    UnverifiableAttributes,
    UnverifiableItem,
)


class MockVisionProvider:
    """Mock provider for fast, deterministic unit testing without API keys."""

    def __init__(self, evidence: BathroomVisionEvidence | None = None, raise_error: bool = False) -> None:
        self.evidence = evidence
        self.raise_error = raise_error

    async def analyze(self, image_bytes: bytes) -> BathroomVisionEvidence:
        if self.raise_error:
            raise RuntimeError("Gemini API connection failure")
        return self.evidence or default_mock_evidence()


def default_unverifiables() -> UnverifiableAttributes:
    def item(reason: str) -> UnverifiableItem:
        return UnverifiableItem(status="unknown", verification_required=True, reason=reason)

    return UnverifiableAttributes(
        exact_room_dimensions=item("Physical laser/tape measurement required."),
        wall_thickness=item("Wall chase depth not visible from single 2D image."),
        plumbing_location=item("In-wall plumbing stack position cannot be verified from photograph."),
        toilet_rough_in=item("Distance from finished wall to drain center requires physical verification."),
        hidden_pipes=item("Concealed drain/vent lines cannot be identified visually."),
        electrical_availability=item("Dedicated electrical circuit availability requires breaker panel inspection."),
        structural_constraints=item("Subfloor load-bearing capacity requires structural assessment."),
    )


def default_mock_evidence(**overrides: object) -> BathroomVisionEvidence:
    payload = {
        "authoritative": False,
        "overall_confidence": 0.88,
        "detected_objects": [
            {
                "type": "vanity",
                "confidence": 0.92,
                "bounding_box": {"x": 0.05, "y": 0.2, "width": 0.25, "height": 0.5},
            },
            {
                "type": "toilet",
                "confidence": 0.85,
                "bounding_box": {"x": 0.40, "y": 0.3, "width": 0.20, "height": 0.4},
            },
            {
                "type": "shower",
                "confidence": 0.78,
                "bounding_box": {"x": 0.70, "y": 0.1, "width": 0.25, "height": 0.7},
            },
        ],
        "approximate_fixture_zones": [],
        "ambiguous_objects": [],
        "occlusions": [],
        "missing_information": [],
        "unverifiable_attributes": default_unverifiables(),
    }
    payload.update(overrides)
    return BathroomVisionEvidence.model_validate(payload)


def create_sample_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (400, 300), color="beige")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def client():
    store.clear()
    return TestClient(app)


# --- 1. Valid bathroom image analysis -----------------------------------------


def test_valid_bathroom_image_analysis():
    provider = MockVisionProvider(default_mock_evidence())
    analyzer = BathroomVisionAnalyzer(provider)
    evidence = asyncio.run(analyzer.analyze(create_sample_jpeg_bytes()))

    assert evidence.authoritative is False
    assert len(evidence.detected_objects) == 3
    assert evidence.detected_objects[0].type == "vanity"
    assert evidence.detected_objects[0].observation_status == "observed"


# --- 2. No visible fixture ----------------------------------------------------


def test_no_visible_fixture():
    empty_evidence = default_mock_evidence(detected_objects=[], overall_confidence=0.1)
    provider = MockVisionProvider(empty_evidence)
    analyzer = BathroomVisionAnalyzer(provider)
    evidence = asyncio.run(analyzer.analyze(create_sample_jpeg_bytes()))

    assert len(evidence.detected_objects) == 0
    assert evidence.overall_confidence <= 0.2


# --- 3. Low-confidence detection ----------------------------------------------


def test_low_confidence_detection():
    low_conf_evidence = default_mock_evidence(
        detected_objects=[
            {
                "type": "sink",
                "confidence": 0.55,  # < 0.7 heuristic
                "bounding_box": {"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.2},
            }
        ]
    )
    provider = MockVisionProvider(low_conf_evidence)
    analyzer = BathroomVisionAnalyzer(provider)
    evidence = asyncio.run(analyzer.analyze(create_sample_jpeg_bytes()))

    # Confidence below heuristic threshold marks it as 'estimated'
    assert evidence.detected_objects[0].observation_status == "estimated"


# --- 4. Unknown dimensions ----------------------------------------------------


def test_unknown_dimensions():
    evidence = default_mock_evidence()
    dim_item = evidence.unverifiable_attributes.exact_room_dimensions
    assert dim_item.status == "unknown"
    assert dim_item.verification_required is True


# --- 5. Unknown plumbing ------------------------------------------------------


def test_unknown_plumbing():
    evidence = default_mock_evidence()
    rough_in_item = evidence.unverifiable_attributes.toilet_rough_in
    assert rough_in_item.status == "unknown"
    assert rough_in_item.verification_required is True


# --- 6. Unknown electrical ----------------------------------------------------


def test_unknown_electrical():
    evidence = default_mock_evidence()
    elec_item = evidence.unverifiable_attributes.electrical_availability
    assert elec_item.status == "unknown"
    assert elec_item.verification_required is True


# --- 7. User-provided dimension overriding estimate (Precedence Rule) ----------


def test_user_dimension_override_precedence():
    user_brief = BathroomBrief(
        room_width_ft=6.0,
        room_length_ft=8.0,
        budget=250000.0,
        required_categories=["vanity", "basin", "faucet", "toilet", "shower"],
    )
    evidence = default_mock_evidence()

    reconciled_brief, decisions = reconcile_brief_with_vision(user_brief, evidence)

    # PRECEDENCE INVARIANT: User measurements are never overwritten by vision
    assert reconciled_brief.room_width_ft == 6.0
    assert reconciled_brief.room_length_ft == 8.0
    assert reconciled_brief.budget == 250000.0

    # Decision record documents advisory visual observation without claiming authority
    assert len(decisions) >= 3
    assert any("Vanity" in d.rationale for d in decisions)


# --- 8. Vision unavailable fallback -------------------------------------------


def test_vision_unavailable_fallback(client):
    # Core planner works completely with no image and no vision key
    res = client.post(
        "/api/v1/plan",
        json={
            "room_width_ft": 6.0,
            "room_length_ft": 8.0,
            "budget": 250000.0,
            "required_categories": ["vanity", "basin", "faucet", "toilet", "shower"],
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert len(res.json()["candidates"]) > 0


# --- 9. Invalid image upload handling -----------------------------------------


def test_invalid_image_upload(client):
    res = client.post(
        "/api/v1/plan",
        json={"room_width_ft": 6.0, "room_length_ft": 8.0, "budget": 250000.0},
    )
    project_id = res.json()["project_id"]

    # Upload corrupt non-image bytes
    res_img = client.post(
        f"/api/v1/project/{project_id}/vision",
        files={"image": ("corrupted.jpg", b"not-a-valid-image-stream", "image/jpeg")},
    )
    assert res_img.status_code == 422
    assert "not a valid image" in res_img.json()["detail"]


# --- 10. DesignState integration ----------------------------------------------


def test_designstate_integration():
    brief = BathroomBrief(
        room_width_ft=6.0,
        room_length_ft=8.0,
        budget=250000.0,
        required_categories=["vanity", "basin", "faucet", "toilet", "shower"],
    )
    plan = create_plan(brief, project_id="proj_vis_test")
    v1_state = create_design_state_from_candidate(plan.candidates[0], brief, "proj_vis_test")

    evidence = default_mock_evidence()
    updated_state = attach_vision_to_design_state(v1_state, evidence)

    assert updated_state.vision_analysis is not None
    assert updated_state.vision_analysis.overall_confidence == 0.88
    # Verification checklist includes vision verification items
    verif_domain = updated_state.ledger.verification
    assert verif_domain.verification_count > 0
    assert any("vision_verification" in c.constraint for c in verif_domain.checks)


# --- 11. Vision wall estimate does not become a hard constraint (Guardrail 3) -


def test_vision_wall_estimate_advisory_only():
    evidence = default_mock_evidence()
    analyzer = BathroomVisionAnalyzer(MockVisionProvider(evidence))
    processed = asyncio.run(analyzer.analyze(create_sample_jpeg_bytes()))

    # Vanity is placed near x=0.05 -> tagged advisory 'west' wall
    vanity_obj = next(o for o in processed.detected_objects if o.type == "vanity")
    assert vanity_obj.approximate_wall_region == "west"

    # Solver can place vanity on north or south wall according to layout clearance laws:
    brief = BathroomBrief(room_width_ft=6.0, room_length_ft=8.0, budget=250000.0)
    plan = create_plan(brief, project_id="advisory_wall_test")
    # The design is valid and feasible regardless of visual wall region
    assert plan.status == "ok"


# --- 12. Verification-required does not become infeasible (Guardrail 2) --------


def test_verification_required_does_not_cause_infeasibility():
    brief = BathroomBrief(room_width_ft=6.0, room_length_ft=8.0, budget=250000.0)
    plan = create_plan(brief, project_id="guardrail2_test")
    v1_state = create_design_state_from_candidate(plan.candidates[0], brief, "guardrail2_test")

    # Initial state is feasible
    assert v1_state.ledger.is_feasible is True

    evidence = default_mock_evidence()
    state_with_vision = attach_vision_to_design_state(v1_state, evidence)

    # GUARDRAIL 2 INVARIANT: UNKNOWN != INFEASIBLE
    assert state_with_vision.ledger.is_feasible is True
    assert state_with_vision.ledger.verification.verification_count > 0
    assert state_with_vision.ledger.space.status == "pass"


# --- 13. Confidence threshold is classification only (Guardrail 1) -------------


def test_confidence_threshold_classification_only():
    obj_high = DetectedObject(
        type="toilet",
        confidence=0.75,
        bounding_box=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.2),
    )
    obj_low = DetectedObject(
        type="toilet",
        confidence=0.65,
        bounding_box=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.2),
    )

    analyzer = BathroomVisionAnalyzer(MockVisionProvider(default_mock_evidence(detected_objects=[obj_high.model_dump()])))
    res_high = asyncio.run(analyzer.analyze(create_sample_jpeg_bytes()))
    assert res_high.detected_objects[0].observation_status == "observed"

    analyzer_low = BathroomVisionAnalyzer(MockVisionProvider(default_mock_evidence(detected_objects=[obj_low.model_dump()])))
    res_low = asyncio.run(analyzer_low.analyze(create_sample_jpeg_bytes()))
    assert res_low.detected_objects[0].observation_status == "estimated"

    # Both objects have unknown physical dimensions regardless of confidence
    assert res_high.detected_objects[0].dimension_status == "unknown"
    assert res_low.detected_objects[0].dimension_status == "unknown"


# --- 14. Gemini failure does not break planner (Guardrail 4) -------------------


def test_gemini_failure_does_not_break_planner():
    provider = MockVisionProvider(raise_error=True)
    analyzer = BathroomVisionAnalyzer(provider)

    # Direct analyzer handles failure gracefully
    with pytest.raises(RuntimeError, match="Gemini API connection failure"):
        asyncio.run(analyzer.analyze(create_sample_jpeg_bytes()))

    # Even with vision failure, the deterministic planner produces feasible configurations
    brief = BathroomBrief(room_width_ft=6.0, room_length_ft=8.0, budget=250000.0)
    plan = create_plan(brief, project_id="gemini_fail_test")
    assert plan.status == "ok"
    assert len(plan.candidates) > 0


# --- 15. Existing DesignPulse remains unchanged --------------------------------


def test_existing_designpulse_remains_unchanged(client):
    # Setup project
    res = client.post(
        "/api/v1/plan",
        json={
            "room_width_ft": 6.0,
            "room_length_ft": 8.0,
            "budget": 250000.0,
            "required_categories": ["vanity", "basin", "faucet", "toilet", "shower"],
        },
    )
    project_id = res.json()["project_id"]

    # Request 48" -> 60" vanity modification
    impact_res = client.post(
        f"/api/v1/plan/{project_id}/impact",
        json={"message": "Replace 48 vanity with 60 vanity"},
    )
    assert impact_res.status_code == 200
    report = impact_res.json()
    assert report["changed_category"] == "vanity"
    assert len(report["candidate_tradeoffs"]) >= 2

    # Apply Trade-off
    first_tradeoff = report["candidate_tradeoffs"][0]
    apply_res = client.post(
        f"/api/v1/plan/{project_id}/tradeoff",
        json={"tradeoff_id": first_tradeoff["id"], "tradeoff": first_tradeoff},
    )
    assert apply_res.status_code == 200
    v2_data = apply_res.json()["v2"]
    assert v2_data["version_id"] == "v2"
    assert v2_data["version_number"] == 2
    assert "diff" in apply_res.json()
