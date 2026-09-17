import json
from pathlib import Path

from backend.constraints import BathroomConstraints, Product
from backend.recommendation import (
    PreferenceProfile,
    ScoringWeights,
    propose_budget_reduction,
    recommend,
)

CATALOG = json.loads(
    (Path(__file__).parents[1] / "catalog" / "products.json").read_text(encoding="utf-8")
)
PRODUCTS = {item["id"]: Product.model_validate(item) for item in CATALOG}
CATALOG_LIST = list(PRODUCTS.values())


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
        assert "kohler_oversized_vanity_001" not in product_ids(candidate)


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
    result = recommend(CATALOG_LIST, room(budget=200000))

    assert result.status == "ok"
    candidate = result.candidates[0]
    assert candidate.score.water_efficiency == 0.5
    assert any("Water-efficiency data is not available" in note for note in candidate.verification_requirements)


def test_configurable_weights_can_change_ranking_order() -> None:
    smart_room = room(budget=400000, electrical_available=True)
    preference = PreferenceProfile(smart_feature_preference="prefer")

    equal_weights_result = recommend(CATALOG_LIST, smart_room, preference=preference, weights=ScoringWeights())
    equal_ranking = [product_ids(c) for c in equal_weights_result.candidates]

    budget_heavy_result = recommend(
        CATALOG_LIST,
        smart_room,
        preference=preference,
        weights=ScoringWeights(spatial=0.1, budget=10, preference=0.1, water_efficiency=0.1, style=0.1, smart_feature=0.1),
    )
    budget_heavy_ranking = [product_ids(c) for c in budget_heavy_result.candidates]

    assert equal_ranking[0] != budget_heavy_ranking[0]
    assert {"kohler_vanity_001", "kohler_toilet_001"} == budget_heavy_ranking[0]
    assert {"kohler_vanity_001", "kohler_smart_toilet_001"} == equal_ranking[0]


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
    incompatible_toilet = PRODUCTS["kohler_toilet_001"].model_copy(
        update={"incompatible_with": ["kohler_vanity_001"], "id": "kohler_toilet_incompatible"}
    )
    catalog = [PRODUCTS["kohler_vanity_001"], incompatible_toilet]
    single_option_room = room(required_categories=["vanity", "toilet"])

    result = recommend(catalog, single_option_room)

    assert result.status == "no_fully_compliant_configuration"
    assert any(v.constraint == "compatibility" for v in result.no_compliant_configuration.violated_constraints)


def test_tradeoff_engine_keeps_smart_features_while_reducing_budget() -> None:
    generous_room = room(budget=250000, electrical_available=True)
    current_products = [PRODUCTS["kohler_oversized_vanity_001"], PRODUCTS["kohler_smart_toilet_001"]]

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
    assert best_option.removed_product_id == "kohler_oversized_vanity_001"
    assert best_option.added_product_id == "kohler_vanity_001"
    assert best_option.price_delta < 0
    assert best_option.resulting_report.feasible is True
    assert best_option.category == "vanity"


def test_tradeoff_engine_reports_no_option_when_nothing_cheaper_exists() -> None:
    generous_room = room(budget=250000, electrical_available=True)
    current_products = [PRODUCTS["kohler_vanity_001"], PRODUCTS["kohler_toilet_001"]]

    result = propose_budget_reduction(
        current_products,
        CATALOG_LIST,
        generous_room,
        preserve_categories=["vanity", "toilet"],
    )

    assert result.status == "no_option_found"
    assert result.options == []
