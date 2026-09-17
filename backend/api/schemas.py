"""Request and response contracts for the planning API.

One convention runs through every response: anything numeric says who computed
it. `computed_by` is not decoration — it is the answer to "how do I know the
language model did not invent this", and it is checked by tests.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.constraints.models import ConfigurationReport, Product
from backend.layout.models import DoorSpec, RoomLayout
from backend.recommendation.models import (
    NoCompliantConfigurationResult,
    PreferenceProfile,
    ScoreBreakdown,
    ScoringWeights,
)
from backend.sustainability.calculator import UsageAssumptions, WaterImpactEstimate

DEFAULT_REQUIRED_CATEGORIES = ["vanity", "basin", "faucet", "toilet", "shower"]


class BathroomBrief(BaseModel):
    """Everything the user tells us about their bathroom and what they want."""

    model_config = ConfigDict(extra="forbid")

    room_width_ft: float | None = Field(default=None, gt=0, le=60)
    room_length_ft: float | None = Field(default=None, gt=0, le=60)
    ceiling_height_ft: float | None = Field(default=None, gt=0, le=20)
    door: DoorSpec | None = None

    budget: float | None = Field(default=None, ge=0)
    currency: str = "INR"

    required_categories: list[str] = Field(
        default_factory=lambda: list(DEFAULT_REQUIRED_CATEGORIES),
        min_length=1,
        description=(
            "At least one fixture must be requested. An empty list would otherwise "
            "produce a technically valid empty configuration — no products, zero cost — "
            "which is not an answer to anything."
        ),
    )
    preferred_styles: list[str] = Field(default_factory=list)

    # Facts the user may or may not know. Unknown stays unknown — these are
    # explicitly tri-state rather than defaulting to a convenient assumption.
    electrical_available: bool | None = None
    toilet_rough_in_in: float | None = Field(default=None, gt=0)

    preferences: PreferenceProfile = Field(default_factory=PreferenceProfile)
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    usage: UsageAssumptions = Field(default_factory=UsageAssumptions)

    max_candidates: int = Field(default=3, ge=1, le=5)


class CandidatePlan(BaseModel):
    """One configuration, with everything needed to display and defend it."""

    model_config = ConfigDict(extra="forbid")

    label: str | None
    products: list[Product]
    total_price: float
    currency: str
    remaining_budget: float | None

    constraint_report: ConfigurationReport
    score: ScoreBreakdown
    layout: RoomLayout
    water_impact: WaterImpactEstimate

    strengths: list[str]
    trade_offs: list[str]
    installation_warnings: list[str]
    verification_requirements: list[str]
    explanation: str | None = None
    explanation_source: Literal["deterministic_template", "llm"] = "deterministic_template"


class PlanMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    computed_by: list[str]
    catalog_size: int
    configurations_evaluated: int
    llm_available: bool
    vision_available: bool
    notes: list[str] = Field(default_factory=list)


class PlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str
    status: Literal["ok", "no_fully_compliant_configuration"]
    brief: BathroomBrief
    candidates: list[CandidatePlan] = Field(default_factory=list)
    conflict: NoCompliantConfigurationResult | None = None
    meta: PlanMeta


class ResolveRequest(BaseModel):
    """The user's choice of which constraint to relax, applied deterministically."""

    model_config = ConfigDict(extra="forbid")

    relaxation: Literal[
        "increase_budget",
        "drop_category",
        "allow_lower_tier",
        "confirm_electrical",
        "confirm_rough_in",
        "enlarge_room",
    ]
    budget: float | None = Field(default=None, ge=0)
    category: str | None = None
    room_width_ft: float | None = Field(default=None, gt=0, le=60)
    room_length_ft: float | None = Field(default=None, gt=0, le=60)
    toilet_rough_in_in: float | None = Field(default=None, gt=0)


class ModifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)


class ModifyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str
    understood_as: str
    interpretation_source: Literal["llm", "deterministic_keywords"]
    applied_changes: list[str]
    plan: PlanResponse


class CatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    categories: list[str]
    products: list[Product]
    data_disclaimer: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    catalog_loaded: bool
    catalog_size: int
    vision_available: bool
    llm_available: bool
    deterministic_planner_available: Literal[True] = True
