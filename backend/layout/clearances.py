"""Fixture clearance rules.

Every figure here traces to a published plumbing-code requirement. These are the
numbers that make "does it fit?" a real question rather than a bounding-box
comparison against the room rectangle.

Sources (IRC 2021/2024, Chapter 27 — Plumbing Fixtures):
- Water closet: 21 in clear space in front; 15 in from the centerline to any
  side wall, partition, or adjacent fixture (hence a 30 in minimum span).
- Lavatory: not closer than 15 in from its centerline to any side wall,
  partition or vanity.
- Shower: minimum 30 in x 30 in interior dimension.

Clearances are measured from finished surfaces, not framing. All values are
inches.

IMPORTANT: these are US residential-code figures. Indian local codes differ and
the product surfaces this as a stated limitation rather than silently implying
local-code compliance. The engine uses them as *planning* minimums.
"""

from dataclasses import dataclass

# Categories that physically occupy floor area and therefore need placing.
# A faucet or showerhead mounts onto another fixture and consumes no floor.
FOOTPRINT_CATEGORIES = frozenset(
    {"toilet", "smart_toilet", "vanity", "basin", "shower", "smart_shower", "bathtub", "storage"}
)

# Minimum clear width a person needs to move through the room.
CIRCULATION_WIDTH_IN = 24.0

# Grid resolution used by the circulation reachability check.
GRID_CELL_IN = 3.0


@dataclass(frozen=True)
class ClearanceRule:
    """Space that must stay clear around a fixture for it to be usable."""

    front_in: float
    """Clear depth required directly in front of the fixture."""

    min_span_in: float
    """Minimum wall run the fixture must occupy, including side clearance."""

    min_interior_in: float = 0.0
    """Minimum interior dimension of the product itself (showers only)."""

    source: str = ""


CLEARANCE_RULES: dict[str, ClearanceRule] = {
    "toilet": ClearanceRule(
        front_in=21.0,
        min_span_in=30.0,
        source="IRC 2021/2024 Ch.27 — 21 in front clearance; 15 in centerline to side wall",
    ),
    "smart_toilet": ClearanceRule(
        front_in=21.0,
        min_span_in=30.0,
        source="IRC 2021/2024 Ch.27 — 21 in front clearance; 15 in centerline to side wall",
    ),
    "vanity": ClearanceRule(
        front_in=21.0,
        min_span_in=30.0,
        source="IRC 2021/2024 Ch.27 — lavatory 15 in centerline to side wall; 21 in front clearance",
    ),
    "basin": ClearanceRule(
        front_in=21.0,
        min_span_in=30.0,
        source="IRC 2021/2024 Ch.27 — lavatory 15 in centerline to side wall; 21 in front clearance",
    ),
    "shower": ClearanceRule(
        front_in=24.0,
        min_span_in=30.0,
        min_interior_in=30.0,
        source="IRC 2021/2024 Ch.27 — 30 in x 30 in minimum shower interior; entry clearance",
    ),
    "smart_shower": ClearanceRule(
        front_in=24.0,
        min_span_in=30.0,
        min_interior_in=30.0,
        source="IRC 2021/2024 Ch.27 — 30 in x 30 in minimum shower interior; entry clearance",
    ),
    "bathtub": ClearanceRule(
        front_in=21.0,
        min_span_in=30.0,
        source="IRC 2021/2024 Ch.27 — bathing fixture access clearance",
    ),
    "storage": ClearanceRule(
        front_in=18.0,
        min_span_in=12.0,
        source="Planning guidance — access clearance for storage units (not code-derived)",
    ),
}

DEFAULT_RULE = ClearanceRule(
    front_in=21.0,
    min_span_in=24.0,
    source="Default planning clearance applied to an uncategorised fixture",
)


def rule_for(category: str) -> ClearanceRule:
    return CLEARANCE_RULES.get(category, DEFAULT_RULE)


def needs_floor_space(category: str) -> bool:
    return category in FOOTPRINT_CATEGORIES


# Placement priority. The most plumbing-constrained fixture is placed first
# because it has the fewest valid positions; the most flexible is placed last.
PLACEMENT_PRIORITY: dict[str, int] = {
    "toilet": 0,
    "smart_toilet": 0,
    "bathtub": 1,
    "shower": 2,
    "smart_shower": 2,
    "vanity": 3,
    "basin": 4,
    "storage": 5,
}


def placement_rank(category: str) -> int:
    return PLACEMENT_PRIORITY.get(category, 9)
