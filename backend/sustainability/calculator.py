"""Transparent water-impact estimation.

Three things are kept strictly separate here, because conflating them is how
sustainability numbers become dishonest:

1. **Verified product specification** — the flow or flush figure recorded in the
   catalog. Only these drive arithmetic.
2. **Assumption** — how often a fixture is used. Published planning benchmarks,
   adjustable, and reported alongside every result.
3. **Calculation** — the arithmetic combining the two.

A manufacturer's "up to X%" marketing claim is a fourth thing entirely. It is
surfaced verbatim with its source and caveats, and is deliberately *never* folded
into the computed annual total.

When a fixture records no flow figure, the result says `insufficient_data` for
that fixture rather than substituting a plausible number.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.constraints.models import ManufacturerClaim, Product

from .constants import (
    ASSUMPTION_SOURCES,
    BASELINE_DESCRIPTION,
    BASELINE_FAUCET_GPM,
    BASELINE_SHOWER_GPM,
    BASELINE_TOILET_GPF,
    DAYS_PER_YEAR,
    DEFAULT_FAUCET_MINUTES_PER_PERSON_PER_DAY,
    DEFAULT_FLUSHES_PER_PERSON_PER_DAY,
    DEFAULT_HOUSEHOLD_SIZE,
    DEFAULT_SHOWER_MINUTES_PER_PERSON_PER_DAY,
    DISCLAIMER,
    LITRES_PER_GALLON,
    REGIONAL_LIMITATION,
    WATER_FIXTURE_CATEGORIES,
)

FLUSH_CATEGORIES = frozenset({"toilet", "smart_toilet"})
SHOWER_CATEGORIES = frozenset({"shower", "smart_shower"})
FAUCET_CATEGORIES = frozenset({"faucet"})


class UsageAssumptions(BaseModel):
    """How often fixtures are used. Planning benchmarks, not observations."""

    model_config = ConfigDict(extra="forbid")

    household_size: int = Field(default=DEFAULT_HOUSEHOLD_SIZE, ge=1, le=20)
    flushes_per_person_per_day: float = Field(
        default=DEFAULT_FLUSHES_PER_PERSON_PER_DAY, ge=0, le=30
    )
    shower_minutes_per_person_per_day: float = Field(
        default=DEFAULT_SHOWER_MINUTES_PER_PERSON_PER_DAY, ge=0, le=120
    )
    faucet_minutes_per_person_per_day: float = Field(
        default=DEFAULT_FAUCET_MINUTES_PER_PERSON_PER_DAY, ge=0, le=120
    )

    def describe(self) -> list[str]:
        return [
            f"Household size: {self.household_size} people.",
            f"Toilet: {self.flushes_per_person_per_day:g} flushes per person per day. "
            f"{ASSUMPTION_SOURCES['flushes_per_person_per_day']}",
            f"Shower: {self.shower_minutes_per_person_per_day:g} minutes per person per day. "
            f"{ASSUMPTION_SOURCES['shower_minutes_per_person_per_day']}",
            f"Basin faucet: {self.faucet_minutes_per_person_per_day:g} minutes per person per day. "
            f"{ASSUMPTION_SOURCES['faucet_minutes_per_person_per_day']}",
            REGIONAL_LIMITATION,
        ]


class FixtureWaterEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    product_name: str
    category: str
    status: Literal["calculated", "insufficient_data", "not_a_water_fixture"]
    recorded_spec: str | None = None
    baseline_spec: str | None = None
    annual_litres: float | None = None
    baseline_annual_litres: float | None = None
    annual_litres_saved: float | None = None
    formula: str | None = None
    note: str | None = None


class WaterImpactEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["calculated", "insufficient_data"]
    assumptions: list[str]
    baseline_description: str = BASELINE_DESCRIPTION
    fixtures: list[FixtureWaterEstimate]

    configuration_annual_litres: float | None = None
    baseline_annual_litres: float | None = None
    annual_litres_saved: float | None = None
    percent_saved: float | None = None

    configuration_annual_gallons: float | None = None
    baseline_annual_gallons: float | None = None

    manufacturer_claims: list[ManufacturerClaim] = Field(default_factory=list)
    unquantified_products: list[str] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 1)


def _estimate_fixture(product: Product, usage: UsageAssumptions) -> FixtureWaterEstimate:
    people = usage.household_size

    if product.category not in WATER_FIXTURE_CATEGORIES:
        return FixtureWaterEstimate(
            product_id=product.id,
            product_name=product.name,
            category=product.category,
            status="not_a_water_fixture",
            note="This product does not consume water directly.",
        )

    if product.category in FLUSH_CATEGORIES:
        recorded = product.water.flush_volume_gal
        if recorded is None:
            return FixtureWaterEstimate(
                product_id=product.id,
                product_name=product.name,
                category=product.category,
                status="insufficient_data",
                note=(
                    "No flush volume is recorded for this product, so its water use cannot "
                    "be calculated. Verify the manufacturer specification."
                ),
            )
        events = usage.flushes_per_person_per_day * people
        annual = recorded * events * DAYS_PER_YEAR * LITRES_PER_GALLON
        baseline = BASELINE_TOILET_GPF * events * DAYS_PER_YEAR * LITRES_PER_GALLON
        return FixtureWaterEstimate(
            product_id=product.id,
            product_name=product.name,
            category=product.category,
            status="calculated",
            recorded_spec=f"{recorded:g} gallons per flush",
            baseline_spec=f"{BASELINE_TOILET_GPF:g} gallons per flush (federal maximum)",
            annual_litres=_round(annual),
            baseline_annual_litres=_round(baseline),
            annual_litres_saved=_round(baseline - annual),
            formula=(
                f"{recorded:g} gpf x {usage.flushes_per_person_per_day:g} flushes/person/day "
                f"x {people} people x {DAYS_PER_YEAR} days x {LITRES_PER_GALLON:g} L/gal"
            ),
        )

    minutes = (
        usage.shower_minutes_per_person_per_day
        if product.category in SHOWER_CATEGORIES
        else usage.faucet_minutes_per_person_per_day
    ) * people
    baseline_rate = (
        BASELINE_SHOWER_GPM if product.category in SHOWER_CATEGORIES else BASELINE_FAUCET_GPM
    )
    label = "shower" if product.category in SHOWER_CATEGORIES else "faucet"

    recorded = product.water.flow_rate_gpm
    if recorded is None:
        return FixtureWaterEstimate(
            product_id=product.id,
            product_name=product.name,
            category=product.category,
            status="insufficient_data",
            note=(
                "No flow rate is recorded for this product, so its water use cannot be "
                "calculated. Verify the manufacturer specification."
            ),
        )

    annual = recorded * minutes * DAYS_PER_YEAR * LITRES_PER_GALLON
    baseline = baseline_rate * minutes * DAYS_PER_YEAR * LITRES_PER_GALLON
    return FixtureWaterEstimate(
        product_id=product.id,
        product_name=product.name,
        category=product.category,
        status="calculated",
        recorded_spec=f"{recorded:g} gallons per minute",
        baseline_spec=f"{baseline_rate:g} gallons per minute (federal maximum)",
        annual_litres=_round(annual),
        baseline_annual_litres=_round(baseline),
        annual_litres_saved=_round(baseline - annual),
        formula=(
            f"{recorded:g} gpm x {minutes / people:g} {label}-minutes/person/day "
            f"x {people} people x {DAYS_PER_YEAR} days x {LITRES_PER_GALLON:g} L/gal"
        ),
    )


def estimate_water_impact(
    products: list[Product], usage: UsageAssumptions | None = None
) -> WaterImpactEstimate:
    """Estimate annual water use for a configuration against the regulatory baseline."""
    usage = usage or UsageAssumptions()
    fixtures = [_estimate_fixture(product, usage) for product in products]

    calculated = [f for f in fixtures if f.status == "calculated"]
    unquantified = [f.product_name for f in fixtures if f.status == "insufficient_data"]

    claims = [
        product.water.manufacturer_claim
        for product in products
        if product.water.manufacturer_claim is not None
    ]

    if not calculated:
        return WaterImpactEstimate(
            status="insufficient_data",
            assumptions=usage.describe(),
            fixtures=fixtures,
            manufacturer_claims=claims,
            unquantified_products=unquantified,
        )

    total = sum(f.annual_litres or 0 for f in calculated)
    baseline_total = sum(f.baseline_annual_litres or 0 for f in calculated)
    saved = baseline_total - total
    percent = (saved / baseline_total * 100) if baseline_total else None

    return WaterImpactEstimate(
        status="calculated",
        assumptions=usage.describe(),
        fixtures=fixtures,
        configuration_annual_litres=_round(total),
        baseline_annual_litres=_round(baseline_total),
        annual_litres_saved=_round(saved),
        percent_saved=_round(percent),
        configuration_annual_gallons=_round(total / LITRES_PER_GALLON),
        baseline_annual_gallons=_round(baseline_total / LITRES_PER_GALLON),
        manufacturer_claims=claims,
        unquantified_products=unquantified,
    )
