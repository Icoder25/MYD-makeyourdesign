from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0.0, le=1.0, description="Normalized top-left x")
    y: float = Field(ge=0.0, le=1.0, description="Normalized top-left y")
    width: float = Field(ge=0.0, le=1.0, description="Normalized width")
    height: float = Field(ge=0.0, le=1.0, description="Normalized height")

    @model_validator(mode="after")
    def must_fit_image(self) -> "BoundingBox":
        if self.x + self.width > 1.0 or self.y + self.height > 1.0:
            raise ValueError("bounding box must fit within normalized image bounds")
        return self


ObservationStatus = Literal["observed", "estimated", "unknown", "requires_verification"]
ApproximateWallRegion = Literal["north", "south", "east", "west", "center", "unknown"]


class DetectedObject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[
        "toilet",
        "sink",
        "vanity",
        "shower",
        "bathtub",
        "door",
        "window",
        "mirror",
        "cabinet",
        "obstacle",
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: BoundingBox
    observation_status: ObservationStatus = "observed"
    approximate_wall_region: ApproximateWallRegion = "unknown"
    dimension_status: Literal["unknown", "estimated", "measured"] = "unknown"


class FixtureZone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zone_type: Literal[
        "wet_zone", "dry_vanity_zone", "toilet_zone", "circulation_clearance"
    ]
    relative_position: Literal[
        "left_wall",
        "right_wall",
        "back_wall",
        "center",
        "foreground_left",
        "foreground_right",
    ]
    bounding_box: BoundingBox


class AmbiguousObject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bounding_box: BoundingBox
    candidate_types: list[str]
    reason: str


class Occlusion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_object: str
    occluded_by: str
    estimated_occlusion_pct: float = Field(ge=0.0, le=100.0)


class UnverifiableItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["unknown"] = "unknown"
    verification_required: Literal[True] = True
    reason: str


class UnverifiableAttributes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exact_room_dimensions: UnverifiableItem
    wall_thickness: UnverifiableItem
    plumbing_location: UnverifiableItem
    toilet_rough_in: UnverifiableItem
    hidden_pipes: UnverifiableItem
    electrical_availability: UnverifiableItem
    structural_constraints: UnverifiableItem


class BathroomVisionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authoritative: Literal[False] = False
    overall_confidence: float = Field(ge=0.0, le=1.0)
    detected_objects: list[DetectedObject]
    approximate_fixture_zones: list[FixtureZone]
    ambiguous_objects: list[AmbiguousObject]
    occlusions: list[Occlusion]
    missing_information: list[str]
    unverifiable_attributes: UnverifiableAttributes
