"""Consistency tests for the shipping catalog.

These guard the data-integrity rules the product rests on: no fabricated
provenance, no efficiency claim that outruns the number behind it, and no
product whose required connection nothing can satisfy.
"""

import pytest

from backend.catalog import (
    CatalogError,
    compute_watersense_eligibility,
    load_catalog,
    validate_catalog,
)
from backend.catalog.loader import (
    WATERSENSE_MAX_FAUCET_GPM,
    WATERSENSE_MAX_FLUSH_GAL,
    WATERSENSE_MAX_SHOWER_GPM,
)
from backend.constraints import Product

CATALOG = load_catalog()


def test_catalog_loads_and_passes_its_own_validation() -> None:
    assert validate_catalog(CATALOG) == []


def test_catalog_is_curated_not_exhaustive() -> None:
    """Scope control: a small, well-described catalog beats a large vague one."""
    assert 25 <= len(CATALOG) <= 45


def test_catalog_covers_every_category_the_demo_needs() -> None:
    categories = {product.category for product in CATALOG}
    assert {"toilet", "smart_toilet", "vanity", "basin", "faucet", "shower", "smart_shower"} <= categories


def test_every_product_id_is_unique() -> None:
    ids = [product.id for product in CATALOG]
    assert len(ids) == len(set(ids))


def test_no_price_is_presented_as_verified_kohler_pricing() -> None:
    """No live KOHLER price feed existed for this project. Nothing may claim otherwise."""
    for product in CATALOG:
        assert product.price_status == "illustrative", product.id


def test_no_product_claims_watersense_certification() -> None:
    """Eligibility is computed. Certification is a per-SKU fact we did not verify."""
    for product in CATALOG:
        assert product.water.watersense_certified is None, product.id


def test_watersense_eligibility_matches_the_recorded_flow_figure() -> None:
    """The derived flag can never drift away from the number it is derived from."""
    thresholds = {
        "toilet": ("flush_volume_gal", WATERSENSE_MAX_FLUSH_GAL),
        "smart_toilet": ("flush_volume_gal", WATERSENSE_MAX_FLUSH_GAL),
        "faucet": ("flow_rate_gpm", WATERSENSE_MAX_FAUCET_GPM),
        "shower": ("flow_rate_gpm", WATERSENSE_MAX_SHOWER_GPM),
        "smart_shower": ("flow_rate_gpm", WATERSENSE_MAX_SHOWER_GPM),
    }
    for product in CATALOG:
        if product.category not in thresholds:
            assert product.water.watersense_eligible is None, product.id
            continue
        field, limit = thresholds[product.category]
        value = getattr(product.water, field)
        if value is None:
            assert product.water.watersense_eligible is None, product.id
        else:
            assert product.water.watersense_eligible is (value <= limit), product.id


def test_unknown_flow_data_stays_unknown_rather_than_becoming_efficient() -> None:
    silent = Product.model_validate(
        {"id": "x", "name": "Unspecified Toilet", "category": "toilet"}
    )
    assert compute_watersense_eligibility(silent) is None


def test_manufacturer_claims_carry_source_baseline_and_assumptions() -> None:
    claims = [p for p in CATALOG if p.water.manufacturer_claim is not None]
    assert claims, "the catalog should exercise the manufacturer-claim path"
    for product in claims:
        claim = product.water.manufacturer_claim
        assert claim.source_url.startswith("http"), product.id
        assert claim.comparison_baseline, product.id
        assert claim.assumptions, product.id


def test_every_required_interface_can_be_satisfied_by_some_product() -> None:
    provided = {i for product in CATALOG for i in product.provides_interfaces}
    for product in CATALOG:
        for interface in product.requires_interfaces:
            assert interface in provided, f"{product.id} requires unsatisfiable {interface}"


def test_every_smart_product_declares_its_electrical_requirement() -> None:
    for product in CATALOG:
        if product.smart.features:
            assert product.electrical_required is not None, product.id


def test_every_floor_standing_product_has_dimensions_for_the_solver() -> None:
    floor_standing = {
        "toilet", "smart_toilet", "vanity", "basin", "shower", "smart_shower", "bathtub", "storage",
    }
    for product in CATALOG:
        if product.category in floor_standing:
            assert product.dimensions.width_in is not None, product.id
            assert product.dimensions.depth_in is not None, product.id


def test_validation_rejects_a_product_requiring_an_impossible_interface() -> None:
    broken = [
        Product.model_validate(
            {
                "id": "broken_faucet",
                "name": "Faucet Needing A Nonexistent Mount",
                "category": "faucet",
                "price": 100,
                "requires_interfaces": ["faucet_mount_does_not_exist"],
            }
        )
    ]
    issues = validate_catalog(broken)
    assert any("faucet_mount_does_not_exist" in issue for issue in issues)


def test_validation_rejects_duplicate_ids() -> None:
    entry = {"id": "dupe", "name": "Dupe", "category": "vanity", "price": 1}
    issues = validate_catalog([Product.model_validate(entry), Product.model_validate(entry)])
    assert any("Duplicate product id" in issue for issue in issues)


def test_validation_rejects_a_smart_product_with_unknown_power_needs() -> None:
    sneaky = Product.model_validate(
        {
            "id": "sneaky",
            "name": "Smart Thing With No Power Story",
            "category": "smart_toilet",
            "price": 1000,
            "dimensions": {"width_in": 28, "depth_in": 29},
            "smart": {"features": ["bidet_wash"]},
        }
    )
    issues = validate_catalog([sneaky])
    assert any("electrical_required" in issue for issue in issues)


def test_missing_catalog_file_raises_a_clear_error() -> None:
    with pytest.raises(CatalogError, match="not found"):
        load_catalog("catalog/does_not_exist.json")
