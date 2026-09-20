from io import BytesIO

from PIL import Image, ImageOps

from .models import BathroomVisionEvidence
from .provider import VisionProvider

MAX_IMAGE_DIMENSION = 1536


class BathroomVisionAnalyzer:
    def __init__(self, provider: VisionProvider) -> None:
        self.provider = provider

    async def analyze(self, image_bytes: bytes) -> BathroomVisionEvidence:
        prepared_image = preprocess_image(image_bytes)
        evidence = await self.provider.analyze(prepared_image)
        evidence = BathroomVisionEvidence.model_validate(evidence)

        # Post-process detected objects to apply classification heuristic and advisory regions
        processed_objects = []
        for obj in evidence.detected_objects:
            # GUARDRAIL 1: 0.7 is strictly an application-level classification heuristic, NOT physical verification
            status = "observed" if obj.confidence >= 0.7 else "estimated"

            # GUARDRAIL 3: Approximate wall region is purely advisory, never a hard layout constraint
            center_x = obj.bounding_box.x + (obj.bounding_box.width / 2.0)
            if center_x < 0.35:
                region = "west"
            elif center_x > 0.65:
                region = "east"
            else:
                region = "north"

            processed_objects.append(
                obj.model_copy(
                    update={
                        "observation_status": status,
                        "approximate_wall_region": region,
                        "dimension_status": "unknown",  # Physical dimensions require measurement
                    }
                )
            )

        return evidence.model_copy(
            update={
                "authoritative": False,
                "detected_objects": processed_objects,
                "overall_confidence": calculate_overall_confidence(evidence),
            }
        )


def preprocess_image(image_bytes: bytes) -> bytes:
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="JPEG", quality=90, optimize=True)
            return output.getvalue()
    except (OSError, ValueError) as exc:
        raise ValueError("uploaded file is not a valid image") from exc


def calculate_overall_confidence(evidence: BathroomVisionEvidence) -> float:
    confidences = [item.confidence for item in evidence.detected_objects]
    mean_confidence = sum(confidences) / len(confidences) if confidences else 0.05
    score = mean_confidence - (0.10 * len(evidence.occlusions)) - (0.15 * len(evidence.ambiguous_objects))
    return round(max(0.05, min(0.98, score)), 4)
