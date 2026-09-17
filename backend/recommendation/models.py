from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.constraints import CheckResult, ConfigurationReport, Product


class ScoringWeights(BaseModel):
    """Configurable weights for each scoring dimension. Not hard-coded: callers
    may supply their own instance to `recommend()`. Weights need not sum to 1;
    they are normalized at scoring time."""

    model_config = ConfigDict(extra="forbid")

    spatial: float = Field(default=1.0, ge=0)
    budget: float = Field(default=1.0, ge=0)
    preference: float = Field(default=1.0, ge=0)
    water_efficiency: float = Field(default=1.0, ge=0)
    style: float = Field(default=1.0, ge=0)
    smart_feature: float = Field(default=1.0, ge=0)

    def as_dict(self) -> dict[str, float]:
        return {
            "spatial": self.spatial,
            "budget": self.budget,
            "preference": self.preference,
            "water_efficiency": self.water_efficiency,
            "style": self.style,
            "smart_feature": self.smart_feature,
        }


class PreferenceProfile(BaseModel):
    """Soft, non-blocking user preferences used only for ranking. These never
    exclude a configuration; hard requirements belong in BathroomConstraints."""

    model_config = ConfigDict(extra="forbid")

    preferred_styles: list[str] = Field(default_factory=list)
    preferred_smart_features: list[str] = Field(default_factory=list)
    smart_feature_preference: Literal["prefer", "avoid", "neutral"] = "neutral"
    storage_preference: Literal["compact", "spacious", "neutral"] = "neutral"


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spatial: float
    budget: float
    preference: float
    water_efficiency: float
    style: float
    smart_feature: float
    weights: ScoringWeights
    total: float


class CandidateConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = None
    products: list[Product]
    total_price: float
    currency: str
    remaining_budget: float | None
    constraint_report: ConfigurationReport
    score: ScoreBreakdown
    strengths: list[str] = Field(default_factory=list)
    trade_offs: list[str] = Field(default_factory=list)
    installation_warnings: list[str] = Field(default_factory=list)
    verification_requirements: list[str] = Field(default_factory=list)


class ConstraintViolationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    constraint: str
    status: str
    occurrences: int
    example_reasons: list[str]


class ClosestAlternative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    products: list[Product]
    total_price: float
    currency: str
    constraint_report: ConfigurationReport
    violations: list[CheckResult]


class RelaxationSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    constraint: str
    description: str
    product_ids: list[str] = Field(default_factory=list)


class NoCompliantConfigurationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["NO_FULLY_COMPLIANT_CONFIGURATION"] = "NO_FULLY_COMPLIANT_CONFIGURATION"
    violated_constraints: list[ConstraintViolationSummary]
    closest_alternatives: list[ClosestAlternative]
    possible_relaxations: list[RelaxationSuggestion]


class RecommendationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "no_fully_compliant_configuration"]
    candidates: list[CandidateConfiguration] = Field(default_factory=list)
    no_compliant_configuration: NoCompliantConfigurationResult | None = None


class TradeoffOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["substitute", "remove"]
    category: str
    removed_product_id: str | None
    added_product_id: str | None
    price_delta: float
    resulting_total_price: float
    resulting_report: ConfigurationReport
    description: str


class TradeoffResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "no_option_found"]
    preserved_categories: list[str]
    options: list[TradeoffOption] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
