"""A tiny, stable catalog used by engine behaviour tests.

Engine tests assert on ranking order, price arithmetic and substitution choices.
Pinning those assertions to the shipping catalog would mean every product added
to `catalog/products.json` breaks unrelated tests — and would quietly discourage
improving the catalog.

So behaviour is tested against this fixed four-product set, and the real catalog
is tested separately, for its own consistency, in `test_catalog.py`.

These are fixtures, not products. The names are deliberately generic.
"""

from backend.constraints import Product

FIXTURE_CATALOG_DATA = [
    {
        "id": "fx_vanity_compact",
        "name": "Fixture Compact Vanity",
        "category": "vanity",
        "price": 42000,
        "currency": "INR",
        "dimensions": {"width_in": 30, "depth_in": 20, "height_in": 34},
        "installation": {"type": "floor_mounted"},
        "compatibility_group": ["standard_bathroom"],
        "incompatible_with": [],
        "electrical_required": False,
        "smart": {"features": [], "konnect_compatible": False},
        "style": ["modern", "minimalist"],
    },
    {
        "id": "fx_toilet_standard",
        "name": "Fixture Standard Toilet",
        "category": "toilet",
        "price": 35000,
        "currency": "INR",
        "dimensions": {"width_in": 28, "depth_in": 29, "height_in": 30},
        "installation": {"type": "floor_mounted", "rough_in_in": 12},
        "compatibility_group": ["standard_bathroom"],
        "incompatible_with": [],
        "electrical_required": False,
        "smart": {"features": [], "konnect_compatible": False},
        "style": ["modern"],
    },
    {
        "id": "fx_smart_toilet",
        "name": "Fixture Smart Toilet",
        "category": "smart_toilet",
        "price": 125000,
        "currency": "INR",
        "dimensions": {"width_in": 28, "depth_in": 30, "height_in": 22},
        "installation": {"type": "floor_mounted", "rough_in_in": 12},
        "compatibility_group": ["standard_bathroom"],
        "incompatible_with": [],
        "electrical_required": True,
        "smart": {"features": ["heated_seat", "bidet"], "konnect_compatible": True},
        "style": ["modern"],
    },
    {
        "id": "fx_vanity_double",
        "name": "Fixture Double Vanity",
        "category": "vanity",
        "price": 88000,
        "currency": "INR",
        "dimensions": {"width_in": 72, "depth_in": 22, "height_in": 34},
        "installation": {"type": "floor_mounted"},
        "compatibility_group": ["standard_bathroom"],
        "incompatible_with": [],
        "electrical_required": False,
        "smart": {"features": [], "konnect_compatible": False},
        "style": ["modern"],
    },
]

PRODUCTS: dict[str, Product] = {
    entry["id"]: Product.model_validate(entry) for entry in FIXTURE_CATALOG_DATA
}
CATALOG_LIST: list[Product] = list(PRODUCTS.values())
