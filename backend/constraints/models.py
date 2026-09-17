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


class WaterInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flow_rate_gpm: float | None = Field(default=None, gt=0)
    flush_volume_gal: float | None = Field(default=None, gt=0)
    watersense_certified: bool | None = None


class Product(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    category: str
    price: float | None = Field(default=None, ge=0)
    currency: str = "INR"
    dimensions: ProductDimensions = Field(default_factory=ProductDimensions)
    installation: InstallationInfo = Field(default_factory=InstallationInfo)
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
