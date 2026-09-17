"""Tests for the water-impact estimator.

These guard the line between calculation and claim. A sustainability number that
cannot say where it came from is worse than no number at all.
"""

from backend.constraints import Product
from backend.sustainability import UsageAssumptions, estimate_water_impact
from backend.sustainability.constants import (
    BASELINE_SHOWER_GPM,
    BASELINE_TOILET_GPF,
    DAYS_PER_YEAR,
    LITRES_PER_GALLON,
)


def product(**overrides) -> Product:
    base = {"id": "p", "name": "Product", "category": "toilet", "price": 1000}
    base.update(overrides)
    return Product.model_validate(base)


def test_toilet_arithmetic_matches_the_stated_formula() -> None:
    toilet = product(id="t", category="toilet", water={"flush_volume_gal": 1.28})
    usage = UsageAssumptions(household_size=3, flushes_per_person_per_day=4.0)

    result = estimate_water_impact([toilet], usage)

    expected = 1.28 * 4.0 * 3 * DAYS_PER_YEAR * LITRES_PER_GALLON
    assert result.status == "calculated"
    assert abs(result.configuration_annual_litres - expected) < 0.5


def test_baseline_uses_the_published_federal_standard() -> None:
    toilet = product(id="t", category="toilet", water={"flush_volume_gal": 1.28})
    usage = UsageAssumptions(household_size=1, flushes_per_person_per_day=5.0)

    result = estimate_water_impact([toilet], usage)

    expected_baseline = BASELINE_TOILET_GPF * 5.0 * 1 * DAYS_PER_YEAR * LITRES_PER_GALLON
    assert abs(result.baseline_annual_litres - expected_baseline) < 0.5
    assert "1.6 gpf" in result.baseline_description


def test_shower_arithmetic_matches_the_stated_formula() -> None:
    shower = product(id="s", category="shower", water={"flow_rate_gpm": 2.0})
    usage = UsageAssumptions(household_size=2, shower_minutes_per_person_per_day=5.0)

    result = estimate_water_impact([shower], usage)

    expected = 2.0 * 5.0 * 2 * DAYS_PER_YEAR * LITRES_PER_GALLON
    baseline = BASELINE_SHOWER_GPM * 5.0 * 2 * DAYS_PER_YEAR * LITRES_PER_GALLON
    assert abs(result.configuration_annual_litres - expected) < 0.5
    assert abs(result.baseline_annual_litres - baseline) < 0.5


def test_missing_flow_data_returns_insufficient_data_not_a_guess() -> None:
    silent = product(id="x", category="shower", water={})

    result = estimate_water_impact([silent])

    assert result.status == "insufficient_data"
    assert result.configuration_annual_litres is None
    assert result.fixtures[0].status == "insufficient_data"
    assert "Verify the manufacturer specification" in result.fixtures[0].note
    assert result.unquantified_products == ["Product"]


def test_partial_data_quantifies_what_it_can_and_names_what_it_cannot() -> None:
    known = product(id="t", name="Known Toilet", category="toilet", water={"flush_volume_gal": 1.28})
    unknown = product(id="s", name="Unknown Shower", category="shower", water={})

    result = estimate_water_impact([known, unknown])

    assert result.status == "calculated"
    assert result.configuration_annual_litres > 0
    assert result.unquantified_products == ["Unknown Shower"]


def test_non_water_products_are_excluded_rather_than_counted_as_zero() -> None:
    vanity = product(id="v", name="Vanity", category="vanity", water={})

    result = estimate_water_impact([vanity])

    assert result.status == "insufficient_data"
    assert result.fixtures[0].status == "not_a_water_fixture"
    assert result.unquantified_products == []


def test_every_calculated_fixture_shows_its_formula_and_specs() -> None:
    """A number the user cannot audit is not transparent."""
    toilet = product(id="t", category="toilet", water={"flush_volume_gal": 1.28})

    result = estimate_water_impact([toilet])

    fixture = result.fixtures[0]
    assert fixture.formula
    assert fixture.recorded_spec
    assert fixture.baseline_spec
    assert "gpf" in fixture.formula


def test_assumptions_and_disclaimer_always_travel_with_the_result() -> None:
    toilet = product(id="t", category="toilet", water={"flush_volume_gal": 1.28})

    result = estimate_water_impact([toilet])

    assert len(result.assumptions) >= 4
    assert any("EPA" in line for line in result.assumptions)
    assert any("Indian household usage patterns differ" in line for line in result.assumptions)
    assert "not a measurement" in result.disclaimer


def test_manufacturer_claim_is_surfaced_but_never_folded_into_the_total() -> None:
    """An 'up to 80%' marketing figure must not silently become a computed saving."""
    recirculating = product(
        id="r",
        category="smart_shower",
        water={
            "flow_rate_gpm": 2.5,
            "manufacturer_claim": {
                "claim_type": "up_to",
                "value": 80.0,
                "unit": "percent",
                "comparison_baseline": "a standard non-recirculating shower system",
                "assumptions": "Manufacturer states savings vary with shower duration.",
                "source_url": "https://example.com/spec",
            },
        },
    )
    usage = UsageAssumptions(household_size=1, shower_minutes_per_person_per_day=5.0)

    result = estimate_water_impact([recirculating], usage)

    assert len(result.manufacturer_claims) == 1
    assert result.manufacturer_claims[0].value == 80.0
    assert result.manufacturer_claims[0].source_url
    # The computed total uses the 2.5 gpm figure only. At baseline 2.5 gpm the
    # computed saving is zero, and the 80% claim has not leaked into it.
    assert result.annual_litres_saved == 0.0
    assert result.percent_saved == 0.0


def test_efficient_configuration_saves_against_baseline() -> None:
    efficient = [
        product(id="t", category="toilet", water={"flush_volume_gal": 1.28}),
        product(id="s", category="shower", water={"flow_rate_gpm": 1.75}),
    ]

    result = estimate_water_impact(efficient)

    assert result.annual_litres_saved > 0
    assert 0 < result.percent_saved < 100


def test_both_units_are_reported() -> None:
    toilet = product(id="t", category="toilet", water={"flush_volume_gal": 1.28})

    result = estimate_water_impact([toilet])

    assert result.configuration_annual_gallons is not None
    assert abs(
        result.configuration_annual_litres / LITRES_PER_GALLON
        - result.configuration_annual_gallons
    ) < 1.0


def test_household_size_scales_the_estimate_linearly() -> None:
    toilet = product(id="t", category="toilet", water={"flush_volume_gal": 1.28})

    one = estimate_water_impact([toilet], UsageAssumptions(household_size=1))
    four = estimate_water_impact([toilet], UsageAssumptions(household_size=4))

    assert abs(four.configuration_annual_litres - 4 * one.configuration_annual_litres) < 1.0
