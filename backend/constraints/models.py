from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.layout.models import DoorSpec


class ProductDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width_in: float | None = Field(default=None, gt=0)
    depth_in: float | None = Field(default=None, gt=0)
    height_in: float | None = Field(default=None, gt=0)


class InstallationInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str | None = None
    rough_in_in: float | None = Field(default=None, gt=0)


class SmartInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    features: list[str] = Field(default_factory=list)
    konnect_compatible: bool | None = None


class ManufacturerClaim(BaseModel):
    """A claim the manufacturer makes, preserved with its own wording and caveats.

    Marketing figures ("up to 80%") are never folded into a computed annual
    total. They are surfaced verbatim and attributed. Computed totals use only
    measured flow and flush figures.
    """

    model_config = ConfigDict(extra="forbid")

    claim_type: Literal["up_to", "average", "certified"]
    value: float
    unit: Literal["percent", "gpm", "gpf"]
    comparison_baseline: str
    assumptions: str
    source_url: str


class WaterInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flow_rate_gpm: float | None = Field(default=None, gt=0)
    flush_volume_gal: float | None = Field(default=None, gt=0)
    watersense_certified: bool | None = None
    """Whether the manufacturer holds WaterSense certification for this SKU.
    Left None across the prototype catalog: certification is per-SKU and was not
    verifiable here. Do not confuse with `watersense_eligible`, which is computed."""

    watersense_eligible: bool | None = None
    """Computed by the catalog loader from the recorded flow/flush figure against
    the published WaterSense threshold. An eligibility calculation, not a
    certification claim. See docs/verified-facts.md section 1."""

    manufacturer_claim: ManufacturerClaim | None = None


class Product(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    category: str
    tier: Literal["essential", "standard", "premium", "luxury"] = "standard"

    price: float | None = Field(default=None, ge=0)
    currency: str = "INR"
    price_status: Literal["illustrative", "verified", "unknown"] = "illustrative"
    """Prototype prices are illustrative. No live KOHLER pricing feed was
    available to this project; see docs/verified-facts.md section 5."""

    verification_status: Literal["verified", "illustrative", "requires_verification"] = (
        "illustrative"
    )
    source: str | None = None
    kohler_reference_family: str | None = None
    """The real KOHLER product family whose class this record is modelled on.
    A taxonomy pointer for a future catalog swap — NOT a claim that this row is
    that SKU, nor that these dimensions or this price belong to it."""

    dimensions: ProductDimensions = Field(default_factory=ProductDimensions)
    installation: InstallationInfo = Field(default_factory=InstallationInfo)

    provides_interfaces: list[str] = Field(default_factory=list)
    """Mounting/connection interfaces this product offers to others."""

    requires_interfaces: list[str] = Field(default_factory=list)
    """Interfaces this product needs another product in the configuration to provide."""

    compatibility_group: list[str] = Field(default_factory=list)
    incompatible_with: list[str] = Field(default_factory=list)
    electrical_required: bool | None = None
    smart: SmartInfo = Field(default_factory=SmartInfo)
    water: WaterInfo = Field(default_factory=WaterInfo)
    style: list[str] = Field(default_factory=list)


class FixtureZone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width_ft: float | None = Field(default=None, gt=0)
    depth_ft: float | None = Field(default=None, gt=0)


class UserConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_categories: list[str] = Field(default_factory=list)
    required_styles: list[str] = Field(default_factory=list)
    max_product_depth_in: float | None = Field(default=None, gt=0)


class BathroomConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_length_ft: float | None = Field(default=None, gt=0)
    room_width_ft: float | None = Field(default=None, gt=0)
    ceiling_height_ft: float | None = Field(default=None, gt=0)
    budget: float | None = Field(default=None, ge=0)
    currency: str = "INR"
    required_categories: list[str] = Field(default_factory=list)
    fixture_zones: dict[str, FixtureZone] = Field(default_factory=dict)
    electrical_available: bool | None = None
    toilet_rough_in_in: float | None = Field(default=None, gt=0)
    door: DoorSpec | None = None
    """Doorway position. Consumes floor area and defines where circulation starts."""
    user_constraints: UserConstraints = Field(default_factory=UserConstraints)


class CheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    constraint: str
    passed: bool
    status: Literal["pass", "fail", "verification_required", "warning"]
    reason: str
    blocking: bool = True
    details: dict[str, Any] = Field(default_factory=dict)


class ConfigurationReport(BaseModel):
    """Three-state verdict on a configuration.

    The distinction that matters: an *unknown* is never converted into a pass,
    but it is also not the same thing as a proven failure. A toilet that does
    not fit is infeasible. A toilet whose rough-in nobody has measured yet is
    plannable-but-unverified, and saying so is more useful than refusing to
    plan. Those are separate states here, and the UI renders them differently.

    - ``feasible``  — every check passed. Nothing outstanding.
    - ``offerable`` — nothing is proven broken, so this may be shown to the
      user, carrying its verification requirements with it.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["feasible", "feasible_pending_verification", "infeasible"] = "feasible"
    feasible: bool
    offerable: bool = True
    checks: list[CheckResult] = Field(default_factory=list)
    blocking_failures: list[str] = Field(default_factory=list)
    verification_requirements: list[str] = Field(default_factory=list)
