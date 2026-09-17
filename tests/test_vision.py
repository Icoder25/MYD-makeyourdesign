from io import BytesIO
import asyncio

import pytest
from PIL import Image
from pydantic import ValidationError

from backend.vision.analyzer import BathroomVisionAnalyzer, calculate_overall_confidence, preprocess_image
from backend.vision.models import BathroomVisionEvidence


class FakeProvider:
    def __init__(self, evidence: BathroomVisionEvidence) -> None:
        self.evidence = evidence
        self.received_image: bytes | None = None

    async def analyze(self, image_bytes: bytes) -> BathroomVisionEvidence:
        self.received_image = image_bytes
        return self.evidence


def unverifiable_attributes() -> dict:
    item = {
        "status": "unknown",
        "verification_required": True,
        "reason": "Not observable from one image.",
    }
    return {
        "exact_room_dimensions": item,
        "wall_thickness": item,
        "plumbing_location": item,
        "toilet_rough_in": item,
        "hidden_pipes": item,
        "electrical_availability": item,
        "structural_constraints": item,
    }


def evidence_payload(**overrides: object) -> dict:
    payload = {
        "authoritative": False,
        "overall_confidence": 0.99,
        "detected_objects": [
            {
                "type": "vanity",
                "confidence": 0.9,
                "bounding_box": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4},
            }
        ],
        "approximate_fixture_zones": [],
        "ambiguous_objects": [],
        "occlusions": [],
        "missing_information": [],
        "unverifiable_attributes": unverifiable_attributes(),
    }
    payload.update(overrides)
    return payload


def test_analyzer_transposes_and_resizes_image_and_recomputes_confidence() -> None:
    image = Image.new("RGB", (3000, 2000), "white")
    source = BytesIO()
    image.save(source, format="PNG")
    provider = FakeProvider(BathroomVisionEvidence.model_validate(evidence_payload()))

    result = asyncio.run(BathroomVisionAnalyzer(provider).analyze(source.getvalue()))

    assert result.authoritative is False
    assert result.overall_confidence == 0.9
    assert provider.received_image is not None
    with Image.open(BytesIO(provider.received_image)) as prepared:
        assert max(prepared.size) <= 1536


def test_confidence_penalizes_occlusions_and_ambiguities() -> None:
    evidence = BathroomVisionEvidence.model_validate(
        evidence_payload(
            ambiguous_objects=[
                {
                    "bounding_box": {"x": 0.0, "y": 0.0, "width": 0.1, "height": 0.1},
                    "candidate_types": ["obstacle"],
                    "reason": "Partially hidden.",
                }
            ],
            occlusions=[
                {
                    "target_object": "shower",
                    "occluded_by": "glass",
                    "estimated_occlusion_pct": 40,
                }
            ],
        )
    )
    assert calculate_overall_confidence(evidence) == 0.65


def test_schema_rejects_authoritative_vision_and_out_of_bounds_boxes() -> None:
    with pytest.raises(ValidationError):
        BathroomVisionEvidence.model_validate(evidence_payload(authoritative=True))
    with pytest.raises(ValidationError):
        BathroomVisionEvidence.model_validate(
            evidence_payload(
                detected_objects=[
                    {
                        "type": "toilet",
                        "confidence": 0.8,
                        "bounding_box": {"x": 0.8, "y": 0.1, "width": 0.4, "height": 0.2},
                    }
                ]
            )
        )


def test_invalid_upload_is_rejected() -> None:
    with pytest.raises(ValueError, match="valid image"):
        preprocess_image(b"not-an-image")
