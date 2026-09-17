"""Catalog loading, derived-field computation, and consistency validation.

The catalog is data, not code. It is designed to be replaced wholesale by an
authorised live KOHLER product feed without any engine change: swap the JSON,
keep the schema, and every downstream module keeps working.

This module is also where the one derived water field is computed. Nothing in
the JSON file claims WaterSense eligibility; eligibility is calculated here from
the recorded flow/flush figure against the published threshold, so the claim can
never drift away from the number it is based on.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

from backend.constraints.models import Product

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = REPO_ROOT / "catalog" / "products.json"

# Published WaterSense maximums. See docs/verified-facts.md section 1.
WATERSENSE_MAX_FLUSH_GAL = 1.28
WATERSENSE_MAX_FAUCET_GPM = 1.5
WATERSENSE_MAX_SHOWER_GPM = 2.0

FLUSH_CATEGORIES = frozenset({"toilet", "smart_toilet"})
FAUCET_CATEGORIES = frozenset({"faucet"})
SHOWER_CATEGORIES = frozenset({"shower", "smart_shower"})

KNOWN_CATEGORIES = frozenset(
    {
        "toilet",
        "smart_toilet",
        "vanity",
        "basin",
        "faucet",
        "shower",
        "smart_shower",
        "bathtub",
        "storage",
    }
)


class CatalogError(RuntimeError):
    """The catalog file is missing, malformed, or internally inconsistent."""


def compute_watersense_eligibility(product: Product) -> bool | None:
    """Is this product's recorded flow/flush within the WaterSense maximum?

    Returns None when the relevant figure is absent. An unrecorded flow rate is
    not evidence of inefficiency, and it is certainly not evidence of
    efficiency — it stays unknown.

    This is an eligibility calculation against a published threshold. It is not
    a claim that the manufacturer has certified this SKU; that stays in
    ``water.watersense_certified``, which the prototype catalog leaves unset.
    """
    water = product.water
    if product.category in FLUSH_CATEGORIES:
        if water.flush_volume_gal is None:
            return None
        return water.flush_volume_gal <= WATERSENSE_MAX_FLUSH_GAL
    if product.category in FAUCET_CATEGORIES:
        if water.flow_rate_gpm is None:
            return None
        return water.flow_rate_gpm <= WATERSENSE_MAX_FAUCET_GPM
    if product.category in SHOWER_CATEGORIES:
        if water.flow_rate_gpm is None:
            return None
        return water.flow_rate_gpm <= WATERSENSE_MAX_SHOWER_GPM
    return None


def _apply_derived_fields(product: Product) -> Product:
    eligible = compute_watersense_eligibility(product)
    if eligible == product.water.watersense_eligible:
        return product
    water = product.water.model_copy(update={"watersense_eligible": eligible})
    return product.model_copy(update={"water": water})


def validate_catalog(products: list[Product]) -> list[str]:
    """Return every consistency problem found. Empty list means the catalog is sound."""
    issues: list[str] = []
    seen_ids: set[str] = set()
    provided: set[str] = set()

    for product in products:
        if product.id in seen_ids:
            issues.append(f"Duplicate product id: {product.id}")
        seen_ids.add(product.id)
        provided.update(product.provides_interfaces)

        if product.category not in KNOWN_CATEGORIES:
            issues.append(f"{product.id}: unknown category '{product.category}'")

        if product.price is None:
            issues.append(f"{product.id}: no price recorded")
        elif product.price_status == "verified" and not product.source:
            issues.append(f"{product.id}: price marked verified but no source recorded")

        dims = product.dimensions
        if product.category in {
            "toilet",
            "smart_toilet",
            "vanity",
            "basin",
            "shower",
            "smart_shower",
            "bathtub",
            "storage",
        } and (dims.width_in is None or dims.depth_in is None):
            issues.append(f"{product.id}: floor-standing product is missing width or depth")

        if product.smart.features and product.electrical_required is None:
            issues.append(
                f"{product.id}: declares smart features but leaves electrical_required unknown"
            )

        claim = product.water.manufacturer_claim
        if claim is not None and not claim.source_url:
            issues.append(f"{product.id}: manufacturer claim carries no source URL")

        if product.water.watersense_certified is True and not product.source:
            issues.append(
                f"{product.id}: asserts WaterSense certification without a source to back it"
            )

    for product in products:
        unsatisfiable = [
            interface for interface in product.requires_interfaces if interface not in provided
        ]
        if unsatisfiable:
            issues.append(
                f"{product.id}: requires {unsatisfiable} which no product in the catalog provides"
            )

    return issues


def load_catalog(path: str | os.PathLike[str] | None = None) -> list[Product]:
    """Read, validate and return the product catalog."""
    catalog_path = Path(path) if path else Path(os.getenv("CATALOG_PATH") or DEFAULT_CATALOG_PATH)
    if not catalog_path.is_absolute():
        catalog_path = REPO_ROOT / catalog_path

    try:
        raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogError(f"Catalog file not found at {catalog_path}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogError(f"Catalog file at {catalog_path} is not valid JSON: {exc}") from exc

    if not isinstance(raw, list):
        raise CatalogError("Catalog file must contain a JSON array of products")

    products = [_apply_derived_fields(Product.model_validate(entry)) for entry in raw]

    issues = validate_catalog(products)
    if issues:
        raise CatalogError("Catalog failed validation:\n  - " + "\n  - ".join(issues))
    return products


@lru_cache(maxsize=1)
def get_catalog() -> tuple[Product, ...]:
    """Process-wide cached catalog. Immutable so callers cannot corrupt it."""
    return tuple(load_catalog())


def categories_in_catalog(products: list[Product] | tuple[Product, ...]) -> set[str]:
    return {product.category for product in products}
