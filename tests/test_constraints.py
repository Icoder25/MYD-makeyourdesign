import json
from pathlib import Path

from backend.constraints import BathroomConstraints, Product, validate_configuration


CATALOG = json.loads(
    (Path(__file__).parents[1] / "catalog" / "products.json").read_text(encoding="utf-8")
)
PRODUCTS = {item["id"]: Product.model_validate(item) for item in CATALOG}


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


def configuration(*product_ids: str, **room_overrides: object):
    return validate_configuration([PRODUCTS[product_id] for product_id in product_ids], room(**room_overrides))


def check(report, constraint: str):
    return next(item for item in report.checks if item.constraint == constraint)


def test_valid_small_bathroom_is_feasible() -> None:
    report = configuration("kohler_vanity_001", "kohler_toilet_001")

    assert report.feasible is True
    assert all(item.status in {"pass", "warning"} for item in report.checks)


def test_oversized_vanity_fails_spatial_fit_and_zone_fit() -> None:
    report = configuration(
        "kohler_oversized_vanity_001",
        "kohler_toilet_001",
        room_width_ft=5,
    )

    assert report.feasible is False
    assert check(report, "spatial_fit").status == "fail"
    assert check(report, "fixture_zone_fit").status == "fail"


def test_budget_failure_is_structured() -> None:
    report = configuration(
        "kohler_vanity_001",
        "kohler_toilet_001",
        budget=50000,
    )

    budget_check = check(report, "budget")
    assert report.feasible is False
    assert budget_check.passed is False
    assert budget_check.status == "fail"
    assert "exceeds budget by 27000" in budget_check.reason


def test_smart_product_with_missing_power_confirmation_requires_verification() -> None:
    report = configuration(
        "kohler_vanity_001",
        "kohler_smart_toilet_001",
        electrical_available=None,
    )

    electrical_check = check(report, "electrical")
    assert report.feasible is False
    assert electrical_check.passed is False
    assert electrical_check.status == "verification_required"


def test_unknown_rough_in_is_not_a_pass() -> None:
    report = configuration(
        "kohler_vanity_001",
        "kohler_toilet_001",
        toilet_rough_in_in=None,
    )

    installation_check = check(report, "installation")
    assert report.feasible is False
    assert installation_check.passed is False
    assert installation_check.status == "verification_required"


def test_explicitly_incompatible_product_combination_fails() -> None:
    incompatible_toilet = PRODUCTS["kohler_toilet_001"].model_copy(
        update={"incompatible_with": ["kohler_vanity_001"]}
    )
    report = validate_configuration(
        [PRODUCTS["kohler_vanity_001"], incompatible_toilet],
        room(),
    )

    compatibility_check = check(report, "compatibility")
    assert report.feasible is False
    assert compatibility_check.status == "fail"
    assert "incompatible" in compatibility_check.reason


def test_multiple_valid_products_can_be_validated_independently() -> None:
    standard = configuration("kohler_vanity_001", "kohler_toilet_001")
    smart = configuration(
        "kohler_vanity_001",
        "kohler_smart_toilet_001",
        budget=200000,
        electrical_available=True,
    )

    assert standard.feasible is True
    assert smart.feasible is True
    assert check(smart, "electrical").status == "pass"
