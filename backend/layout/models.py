"""Geometry contracts for the deterministic layout solver.

Coordinate system: origin at the bottom-left corner of the room, x runs along
the room width, y runs along the room length, all units inches.

    y = length
    ^
    |  north wall
    |
    |  west          east
    |
    +--- south wall -----> x = width
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Wall = Literal["south", "north", "west", "east"]


class Rect(BaseModel):
    """Axis-aligned rectangle in room coordinates (inches)."""

    model_config = ConfigDict(extra="forbid")

    x_in: float
    y_in: float
    width_in: float = Field(gt=0)
    depth_in: float = Field(gt=0)

    @property
    def x2(self) -> float:
        return self.x_in + self.width_in

    @property
    def y2(self) -> float:
        return self.y_in + self.depth_in

    def overlaps(self, other: "Rect", tolerance: float = 1e-6) -> bool:
        """True when the two rectangles share interior area."""
        return (
            self.x_in < other.x2 - tolerance
            and other.x_in < self.x2 - tolerance
            and self.y_in < other.y2 - tolerance
            and other.y_in < self.y2 - tolerance
        )

    def within(self, width_in: float, depth_in: float, tolerance: float = 1e-6) -> bool:
        return (
            self.x_in >= -tolerance
            and self.y_in >= -tolerance
            and self.x2 <= width_in + tolerance
            and self.y2 <= depth_in + tolerance
        )


class DoorSpec(BaseModel):
    """Where the door is and how much floor its swing consumes."""

    model_config = ConfigDict(extra="forbid")

    wall: Wall = "south"
    offset_in: float = Field(default=6.0, ge=0)
    """Distance from the wall's start corner to the door's near edge."""

    width_in: float = Field(default=30.0, gt=0)
    swing: Literal["inward", "outward", "sliding"] = "inward"


class PlacedFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    product_name: str
    category: str
    wall: Wall
    footprint: Rect
    clearance: Rect
    """Clear floor the fixture needs in front of it to be usable."""

    clearance_source: str


class UnplacedFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    product_name: str
    category: str
    reason: str
    status: Literal["fail", "verification_required"]
    required_span_in: float | None = None
    required_depth_in: float | None = None


class DerivedZone(BaseModel):
    """A fixture zone the solver computed from room geometry.

    This is a *derivation* from the user's stated room dimensions plus published
    clearance rules — not an assumption, and not a measurement taken from a
    photograph.
    """

    model_config = ConfigDict(extra="forbid")

    category: str
    width_ft: float
    depth_ft: float
    derived_from: str


class RoomLayout(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_width_in: float
    room_length_in: float
    door: DoorSpec | None = None
    door_swing: Rect | None = None
    placed: list[PlacedFixture] = Field(default_factory=list)
    unplaced: list[UnplacedFixture] = Field(default_factory=list)
    derived_zones: list[DerivedZone] = Field(default_factory=list)
    circulation_ok: bool = True
    circulation_notes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @property
    def solved(self) -> bool:
        """Every fixture found a legal position and the room stays navigable."""
        return not self.unplaced and self.circulation_ok

    def zones_as_constraint_input(self) -> dict[str, dict[str, float]]:
        """Shape the derived zones the way BathroomConstraints.fixture_zones wants."""
        return {
            zone.category: {"width_ft": zone.width_ft, "depth_ft": zone.depth_ft}
            for zone in self.derived_zones
        }
