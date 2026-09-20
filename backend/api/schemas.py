"""Request and response contracts for the planning API.

One convention runs through every response: anything numeric says who computed
it. `computed_by` is not decoration — it is the answer to "how do I know the
language model did not invent this", and it is checked by tests.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.constraints.models import ConfigurationReport, Product
from backend.designpulse.impact_engine import ImpactReport, TradeoffOption
from backend.designpulse.models import DesignState, DesignStateDiff
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


# --- DesignPulse API Contracts ------------------------------------------------


class ImpactRequest(BaseModel):
    """Request for running DesignPulse change impact analysis."""

    model_config = ConfigDict(extra="forbid")

    category: str | None = None
    action: Literal["replace_product", "change_dimension", "add_category", "remove_category"] = (
        "replace_product"
    )
    target_product_id: str | None = None
    target_dimension: dict[str, float] | None = None
    message: str | None = None


class TradeoffApplyRequest(BaseModel):
    """Request to apply a chosen trade-off and construct a new active DesignState."""

    model_config = ConfigDict(extra="forbid")

    tradeoff_id: str
    tradeoff: TradeoffOption | None = None
    modification: ImpactRequest | None = None


class TradeoffApplyResponse(BaseModel):
    """Response containing the newly activated V2 DesignState and diff from V1."""

    model_config = ConfigDict(extra="forbid")

    project_id: str
    version_id: str
    version_number: int
    v2: DesignState
    diff: DesignStateDiff


class VersionSummary(BaseModel):
    """Metadata summary of a specific design version in a project's timeline."""

    model_config = ConfigDict(extra="forbid")

    version_id: str
    version_number: int
    parent_version_id: str | None = None
    timestamp: str
    total_price: float
    currency: str = "INR"
    is_active: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectHistoryResponse(BaseModel):
    """The timeline of design versions for a project."""

    model_config = ConfigDict(extra="forbid")

    project_id: str
    active_version_id: str
    versions: list[VersionSummary]


# --- Inspiration & Style Preset API Contracts --------------------------------


class InspirationStylePreset(BaseModel):
    """Curated architectural style preset."""

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    tagline: str
    description: str
    primary_materials: list[str]
    hardware_finishes: list[str]
    palette_tones: list[str]  # Hex color codes for aesthetic representation
    recommended_families: list[str]
    style_keywords: list[str]
    mood_imagery_keywords: list[str]


class InspirationPresetsResponse(BaseModel):
    """List of all curated KOHLER style directions."""

    model_config = ConfigDict(extra="forbid")

    presets: list[InspirationStylePreset]


class InspirationRequest(BaseModel):
    """Request to match or apply an inspiration preset to a project."""

    model_config = ConfigDict(extra="forbid")

    preset_id: str | None = None
    query: str | None = None


class InspirationApplyResponse(BaseModel):
    """Response when an inspiration preset is applied to a project brief."""

    model_config = ConfigDict(extra="forbid")

    project_id: str
    preset: InspirationStylePreset
    applied_styles: list[str]
    plan: PlanResponse
    state: DesignState


# --- Role-Separated Export Package Contracts ----------------------------------

from backend.export.generator import (  # noqa: E402
    ClientExportData,
    ClientProductItem,
    DealerBOMItem,
    DealerExportData,
    DesignerClearanceItem,
    DesignerExportData,
    ExportPackageResponse,
)


