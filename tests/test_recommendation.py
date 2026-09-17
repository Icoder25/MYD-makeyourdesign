from backend.constraints import BathroomConstraints, Product
from backend.recommendation import (
    PreferenceProfile,
    ScoringWeights,
    propose_budget_reduction,
    recommend,
)

from tests.fixtures import CATALOG_LIST, PRODUCTS  # noqa: E402


def room(**overrides: object) -> BathroomConstraints:
    values = {
        "room_length_ft": 8,
        "room_width_ft": 6,
        "budget": 100000,
        "currency": "INR",
        "required_categories": ["vanity", "toilet"],
        "fixture_zones": {
            "vanity": {"width_ft": 3, "depth_ft": 2},
            "toilet": {"width_ft": 3, "depth_ft": 3},
            "smart_toilet": {"width_ft": 3, "depth_ft": 3},
        },
        "electrical_available": False,
        "toilet_rough_in_in": 12,
    }
    values.update(overrides)
    return BathroomConstraints.model_validate(values)


def product_ids(candidate) -> set[str]:
    return {product.id for product in candidate.products}


def test_generates_multiple_valid_candidates_and_never_ranks_invalid_above_valid() -> None:
    generous_room = room(budget=400000, electrical_available=True)
    result = recommend(CATALOG_LIST, generous_room)

    assert result.status == "ok"
    assert 1 <= len(result.candidates) <= 3
    for candidate in result.candidates:
        assert candidate.constraint_report.feasible is True
        assert "fx_vanity_double" not in product_ids(candidate)


def test_returns_approximately_three_candidates_when_more_are_valid() -> None:
    spacious_room = room(
        budget=400000,
        electrical_available=True,
        fixture_zones={
            "vanity": {"width_ft": 7, "depth_ft": 2},
            "toilet": {"width_ft": 3, "depth_ft": 3},
            "smart_toilet": {"width_ft": 3, "depth_ft": 3},
        },
    )
    result = recommend(CATALOG_LIST, spacious_room, max_candidates=3)

    assert result.status == "ok"
    assert len(result.candidates) == 3
    for candidate in result.candidates:
        assert candidate.constraint_report.feasible is True
        assert candidate.total_price > 0
        assert candidate.remaining_budget == spacious_room.budget - candidate.total_price


def test_candidate_contains_all_required_fields() -> None:
    result = recommend(CATALOG_LIST, room())

    assert result.status == "ok"
    candidate = result.candidates[0]
    assert candidate.products
    assert candidate.total_price > 0
    assert candidate.remaining_budget is not None
    assert candidate.constraint_report.feasible is True
    assert 0 <= candidate.score.total <= 1
    assert isinstance(candidate.strengths, list)
    assert isinstance(candidate.trade_offs, list)
    assert isinstance(candidate.installation_warnings, list)
    assert isinstance(candidate.verification_requirements, list)


def test_water_efficiency_unknown_is_neutral_and_flagged_for_verification() -> None:
    """The fixture toilets record no flush volume, so efficiency stays unknown."""
    result = recommend(CATALOG_LIST, room(budget=200000))

    assert result.status == "ok"
    candidate = result.candidates[0]
    assert candidate.score.water_efficiency == 0.5
    assert any(
        "No flow or flush figure is recorded" in note
        for note in candidate.verification_requirements
    )


def test_products_that_do_not_use_water_are_excluded_from_the_water_score() -> None:
    """A vanity has no flow rate; averaging it in would flatten the dimension."""
    from backend.recommendation.engine import _water_efficiency_score

    vanity_only = [PRODUCTS["fx_vanity_compact"]]
    score, notes = _water_efficiency_score(vanity_only)
    assert score == 0.5
    assert notes == []


def test_configurable_weights_can_change_ranking_order() -> None:
    """Weights are real inputs, not decoration: changing them changes the winner."""
    smart_room = room(budget=400000, electrical_available=True)
    dominant = ScoringWeights(
        spatial=0.1, budget=0.1, preference=0.1, water_efficiency=0.1, style=0.1, smart_feature=10
    )

    prefers_smart = recommend(
        CATALOG_LIST, smart_room, preference=PreferenceProfile(smart_feature_preference="prefer"),
        weights=dominant,
    )
    avoids_smart = recommend(
        CATALOG_LIST, smart_room, preference=PreferenceProfile(smart_feature_preference="avoid"),
        weights=dominant,
    )

    top_when_preferred = prefers_smart.candidates[0]
    top_when_avoided = avoids_smart.candidates[0]

    assert product_ids(top_when_preferred) != product_ids(top_when_avoided)
    assert any(p.smart.features for p in top_when_preferred.products)
    assert not any(p.smart.features for p in top_when_avoided.products)


def test_budget_score_rewards_using_the_budget_not_underspending() -> None:
    """A Rs 76,000 plan is not a better answer to a Rs 2.5 lakh brief."""
    generous = room(budget=400000, electrical_available=True)
    budget_dominant = ScoringWeights(
        spatial=0.1, budget=10, preference=0.1, water_efficiency=0.1, style=0.1, smart_feature=0.1
    )
    result = recommend(CATALOG_LIST, generous, weights=budget_dominant)

    assert result.status == "ok"
    winner = result.candidates[0]
    cheapest = min(c.total_price for c in result.candidates)
    assert winner.total_price > cheapest
    assert winner.total_price <= generous.budget


def test_over_budget_can_never_be_rescued_by_a_high_score() -> None:
    from backend.recommendation.engine import _budget_score

    assert _budget_score(500000, 400000) == 0.0
    assert _budget_score(340000, 400000) > _budget_score(80000, 400000)


def test_zero_compliant_configurations_returns_structured_no_compliant_result() -> None:
    tight_room = room(budget=10000, electrical_available=False)
    result = recommend(CATALOG_LIST, tight_room)

    assert result.status == "no_fully_compliant_configuration"
    report = result.no_compliant_configuration
    assert report is not None
    assert report.status == "NO_FULLY_COMPLIANT_CONFIGURATION"
    assert any(v.constraint == "budget" for v in report.violated_constraints)
    assert 1 <= len(report.closest_alternatives) <= 3
    assert any("budget" in suggestion.description.lower() for suggestion in report.possible_relaxations)


def test_missing_catalog_category_is_reported_as_violated_constraint() -> None:
    impossible_room = room(required_categories=["vanity", "toilet", "bathtub"])
    result = recommend(CATALOG_LIST, impossible_room)

    assert result.status == "no_fully_compliant_configuration"
    report = result.no_compliant_configuration
    assert any(v.constraint == "category_requirements" for v in report.violated_constraints)
    assert any("bathtub" in suggestion.description for suggestion in report.possible_relaxations)
    assert report.closest_alternatives == []


def test_incompatible_product_combination_never_becomes_a_candidate() -> None:
    incompatible_toilet = PRODUCTS["fx_toilet_standard"].model_copy(
        update={"incompatible_with": ["fx_vanity_compact"], "id": "fx_toilet_incompatible"}
    )
    catalog = [PRODUCTS["fx_vanity_compact"], incompatible_toilet]
    single_option_room = room(required_categories=["vanity", "toilet"])

    result = recommend(catalog, single_option_room)

    assert result.status == "no_fully_compliant_configuration"
    assert any(v.constraint == "compatibility" for v in result.no_compliant_configuration.violated_constraints)


def test_tradeoff_engine_keeps_smart_features_while_reducing_budget() -> None:
    generous_room = room(budget=250000, electrical_available=True)
    current_products = [PRODUCTS["fx_vanity_double"], PRODUCTS["fx_smart_toilet"]]

    result = propose_budget_reduction(
        current_products,
        CATALOG_LIST,
        generous_room,
        preserve_categories=["smart_toilet"],
    )

    assert result.status == "ok"
    assert result.preserved_categories == ["smart_toilet"]
    best_option = result.options[0]
    assert best_option.action == "substitute"
    assert best_option.removed_product_id == "fx_vanity_double"
    assert best_option.added_product_id == "fx_vanity_compact"
    assert best_option.price_delta < 0
    assert best_option.resulting_report.feasible is True
    assert best_option.category == "vanity"


def test_tradeoff_engine_reports_no_option_when_nothing_cheaper_exists() -> None:
    generous_room = room(budget=250000, electrical_available=True)
    current_products = [PRODUCTS["fx_vanity_compact"], PRODUCTS["fx_toilet_standard"]]

    result = propose_budget_reduction(
        current_products,
        CATALOG_LIST,
        generous_room,
        preserve_categories=["vanity", "toilet"],
    )

    assert result.status == "no_option_found"
    assert result.options == []
