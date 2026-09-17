"""Deterministic bathroom layout solver.

This module answers a question no language model is allowed to answer in this
system: *given a room of these dimensions, can these fixtures physically coexist
with the clearances a plumbing code requires?*

It is pure arithmetic and geometry. No LLM, no randomness, no network. The same
input always produces the same layout.

Algorithm
---------
1. Fixtures that consume floor area are sorted by placement priority — the most
   plumbing-constrained first, because it has the fewest legal positions.
2. Each fixture is offered every wall in turn, and every 1-inch offset along
   that wall, and takes the first position where:
     - its footprint and its required front clearance both fit inside the room,
     - its footprint overlaps no other footprint and no other fixture's
       clearance,
     - its clearance overlaps no other footprint,
     - neither overlaps the door swing.
   Two fixtures' *clearance* zones may overlap each other. That is how real
   bathrooms work: you stand in the same floor area to use the basin and to
   reach the toilet. Clearance-into-footprint is what makes a fixture unusable,
   and that is what is forbidden.
3. A 3-inch grid flood-fill from the doorway confirms that every placed
   fixture's clearance is actually reachable — this catches the layout that
   satisfies every individual rule but walls someone out of the shower.
4. Placed geometry is converted into per-category fixture zones that the
   constraint engine consumes, and into coordinates the 2D plan renders.

First-fit rather than optimal packing is deliberate. An optimal packer would be
slower, harder to explain, and would produce layouts that change unpredictably
when a product changes by an inch. A judge can follow this one by hand.
"""

from collections.abc import Iterable, Sequence

from .clearances import (
    CIRCULATION_WIDTH_IN,
    GRID_CELL_IN,
    needs_floor_space,
    placement_rank,
    rule_for,
)
from .models import (
    DerivedZone,
    DoorSpec,
    PlacedFixture,
    Rect,
    RoomLayout,
    UnplacedFixture,
    Wall,
)

OFFSET_STEP_IN = 1.0
WALL_ORDER: tuple[Wall, ...] = ("south", "north", "west", "east")


class FixtureRequest:
    """A product the solver is being asked to place."""

    def __init__(
        self,
        product_id: str,
        product_name: str,
        category: str,
        width_in: float | None,
        depth_in: float | None,
    ) -> None:
        self.product_id = product_id
        self.product_name = product_name
        self.category = category
        self.width_in = width_in
        self.depth_in = depth_in


def _wall_run(wall: Wall, room_w: float, room_l: float) -> float:
    """Length of usable wall to slide a fixture along."""
    return room_w if wall in ("south", "north") else room_l


def _rects_for(
    wall: Wall,
    offset: float,
    width: float,
    depth: float,
    front: float,
    room_w: float,
    room_l: float,
) -> tuple[Rect, Rect]:
    """Footprint and front-clearance rectangles for a fixture on a wall."""
    if wall == "south":
        footprint = Rect(x_in=offset, y_in=0.0, width_in=width, depth_in=depth)
        clearance = Rect(x_in=offset, y_in=depth, width_in=width, depth_in=front)
    elif wall == "north":
        footprint = Rect(x_in=offset, y_in=room_l - depth, width_in=width, depth_in=depth)
        clearance = Rect(x_in=offset, y_in=room_l - depth - front, width_in=width, depth_in=front)
    elif wall == "west":
        footprint = Rect(x_in=0.0, y_in=offset, width_in=depth, depth_in=width)
        clearance = Rect(x_in=depth, y_in=offset, width_in=front, depth_in=width)
    else:  # east
        footprint = Rect(x_in=room_w - depth, y_in=offset, width_in=depth, depth_in=width)
        clearance = Rect(x_in=room_w - depth - front, y_in=offset, width_in=front, depth_in=width)
    return footprint, clearance


def _door_swing_rect(door: DoorSpec, room_w: float, room_l: float) -> Rect | None:
    """Floor area a door needs to open. Sliding and outward doors need none."""
    if door.swing != "inward":
        return None
    depth = door.width_in  # a hinged door sweeps a quarter-circle of radius = its width
    if door.wall == "south":
        return Rect(x_in=door.offset_in, y_in=0.0, width_in=door.width_in, depth_in=depth)
    if door.wall == "north":
        return Rect(
            x_in=door.offset_in, y_in=max(0.0, room_l - depth), width_in=door.width_in, depth_in=depth
        )
    if door.wall == "west":
        return Rect(x_in=0.0, y_in=door.offset_in, width_in=depth, depth_in=door.width_in)
    return Rect(x_in=max(0.0, room_w - depth), y_in=door.offset_in, width_in=depth, depth_in=door.width_in)


MAX_SCAN_POSITIONS = 160
"""Positions tried along a single wall.

A 1-inch step is the right resolution for a real bathroom. For an unusually
large room it becomes thousands of positions per wall with no useful gain in
precision -- a 60ft wall does not need 720 candidate offsets to find a legal
spot. The step therefore widens with the wall, keeping cost bounded while
staying at 1 inch for any room a person would actually be planning.
"""


def _scan_step(run: float) -> float:
    return max(OFFSET_STEP_IN, run / MAX_SCAN_POSITIONS)


def _find_position(
    request: FixtureRequest,
    room_w: float,
    room_l: float,
    placed: Sequence[PlacedFixture],
    door_swing: Rect | None,
) -> PlacedFixture | None:
    rule = rule_for(request.category)
    width = request.width_in
    depth = request.depth_in
    assert width is not None and depth is not None  # guarded by caller

    span = max(width, rule.min_span_in)
    side_pad = (span - width) / 2.0

    occupied_footprints = [item.footprint for item in placed]
    occupied_clearances = [item.clearance for item in placed]

    for wall in WALL_ORDER:
        run = _wall_run(wall, room_w, room_l)
        if span > run:
            continue
        offset = 0.0
        limit = run - span
        step = _scan_step(run)
        while offset <= limit + 1e-9:
            footprint, clearance = _rects_for(
                wall, offset + side_pad, width, depth, rule.front_in, room_w, room_l
            )
            if not footprint.within(room_w, room_l) or not clearance.within(room_w, room_l):
                offset += step
                continue

            # Footprints never overlap anything. Clearance may overlap another
            # clearance, but never another fixture's footprint.
            blocked = any(footprint.overlaps(other) for other in occupied_footprints)
            blocked = blocked or any(footprint.overlaps(other) for other in occupied_clearances)
            blocked = blocked or any(clearance.overlaps(other) for other in occupied_footprints)
            if door_swing is not None:
                blocked = blocked or footprint.overlaps(door_swing) or clearance.overlaps(door_swing)

            if not blocked:
                return PlacedFixture(
                    product_id=request.product_id,
                    product_name=request.product_name,
                    category=request.category,
                    wall=wall,
                    footprint=footprint,
                    clearance=clearance,
                    clearance_source=rule.source,
                )
            offset += step
    return None


MAX_GRID_CELLS = 3600
"""Upper bound on flood-fill cells, so a large room cannot stall the solver."""


def _check_circulation(layout: RoomLayout) -> tuple[bool, list[str]]:
    """Flood-fill the free floor from the doorway; confirm every fixture is reachable.

    A layout can satisfy every individual clearance rule and still be unusable
    because a fixture ends up behind another one. This catches that.

    The grid is deliberately coarse and bounded: it answers "can a person get
    there", not "what is the exact free area". Cell size grows with the room so
    the cost stays flat, and the arithmetic runs on plain floats rather than
    constructing a model object per cell -- at a few thousand cells per solve,
    and hundreds of solves per plan, allocation is the whole cost.
    """
    notes: list[str] = []
    if not layout.placed:
        return True, notes

    cell = GRID_CELL_IN
    while (layout.room_width_in / cell) * (layout.room_length_in / cell) > MAX_GRID_CELLS:
        cell *= 2

    cols = max(1, int(layout.room_width_in // cell))
    rows = max(1, int(layout.room_length_in // cell))

    # Plain tuples, not Rect models: this is the hot loop.
    footprints = [
        (item.footprint.x_in, item.footprint.y_in, item.footprint.x2, item.footprint.y2)
        for item in layout.placed
    ]
    clearances = [
        (item.clearance.x_in, item.clearance.y_in, item.clearance.x2, item.clearance.y2)
        for item in layout.placed
    ]

    def overlaps(ax1, ay1, ax2, ay2, box) -> bool:
        bx1, by1, bx2, by2 = box
        return ax1 < bx2 - 1e-6 and bx1 < ax2 - 1e-6 and ay1 < by2 - 1e-6 and by1 < ay2 - 1e-6

    free = [[True] * rows for _ in range(cols)]
    for cx in range(cols):
        x1 = cx * cell
        x2 = x1 + cell
        for cy in range(rows):
            y1 = cy * cell
            y2 = y1 + cell
            if any(overlaps(x1, y1, x2, y2, box) for box in footprints):
                free[cx][cy] = False

    # Entry point: the doorway if known, otherwise any free cell.
    start: tuple[int, int] | None = None
    if layout.door is not None:
        door = layout.door
        if door.wall in ("south", "north"):
            cx = min(cols - 1, int((door.offset_in + door.width_in / 2) // cell))
            cy = 0 if door.wall == "south" else rows - 1
        else:
            cy = min(rows - 1, int((door.offset_in + door.width_in / 2) // cell))
            cx = 0 if door.wall == "west" else cols - 1
        if free[cx][cy]:
            start = (cx, cy)
    if start is None:
        start = next(
            ((cx, cy) for cx in range(cols) for cy in range(rows) if free[cx][cy]),
            None,
        )
    if start is None:
        return False, ["No free floor area remains in the room."]

    seen = [[False] * rows for _ in range(cols)]
    stack = [start]
    seen[start[0]][start[1]] = True
    reachable_cells = 1
    while stack:
        cx, cy = stack.pop()
        for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if 0 <= nx < cols and 0 <= ny < rows and free[nx][ny] and not seen[nx][ny]:
                seen[nx][ny] = True
                reachable_cells += 1
                stack.append((nx, ny))

    # One pass over the grid, accumulating reachability per fixture, rather than
    # a full sweep per fixture.
    reached = [False] * len(layout.placed)
    for cx in range(cols):
        x1 = cx * cell
        x2 = x1 + cell
        for cy in range(rows):
            if not seen[cx][cy]:
                continue
            y1 = cy * cell
            y2 = y1 + cell
            for index, box in enumerate(clearances):
                if not reached[index] and overlaps(x1, y1, x2, y2, box):
                    reached[index] = True

    ok = True
    for index, item in enumerate(layout.placed):
        if not reached[index]:
            ok = False
            notes.append(
                f"{item.product_name} is enclosed by other fixtures — its clear space "
                "cannot be reached from the doorway."
            )

    min_cells = (CIRCULATION_WIDTH_IN / cell) ** 2
    if reachable_cells < min_cells:
        ok = False
        notes.append(
            f"Less than {CIRCULATION_WIDTH_IN:g}in x {CIRCULATION_WIDTH_IN:g}in of reachable "
            "floor remains once every fixture is placed."
        )
    return ok, notes


def solve_layout(
    fixtures: Iterable[FixtureRequest],
    room_width_ft: float | None,
    room_length_ft: float | None,
    door: DoorSpec | None = None,
) -> RoomLayout:
    """Place fixtures against walls with code clearances, or explain what failed."""
    if room_width_ft is None or room_length_ft is None:
        return RoomLayout(
            room_width_in=0.0,
            room_length_in=0.0,
            unplaced=[
                UnplacedFixture(
                    product_id=f.product_id,
                    product_name=f.product_name,
                    category=f.category,
                    reason="Room dimensions are required before any layout can be computed.",
                    status="verification_required",
                )
                for f in fixtures
            ],
            circulation_ok=False,
            notes=["No room dimensions supplied; layout not attempted."],
        )

    room_w = room_width_ft * 12.0
    room_l = room_length_ft * 12.0
    door_swing = _door_swing_rect(door, room_w, room_l) if door else None

    layout = RoomLayout(
        room_width_in=room_w,
        room_length_in=room_l,
        door=door,
        door_swing=door_swing,
    )

    to_place: list[FixtureRequest] = []
    for fixture in fixtures:
        if not needs_floor_space(fixture.category):
            layout.notes.append(
                f"{fixture.product_name} mounts onto another fixture and consumes no floor area."
            )
            continue
        to_place.append(fixture)

    to_place.sort(key=lambda f: (placement_rank(f.category), -(f.width_in or 0)))

    for fixture in to_place:
        rule = rule_for(fixture.category)

        if fixture.width_in is None or fixture.depth_in is None:
            layout.unplaced.append(
                UnplacedFixture(
                    product_id=fixture.product_id,
                    product_name=fixture.product_name,
                    category=fixture.category,
                    reason=(
                        f"{fixture.product_name} has no recorded width/depth, so its position "
                        "cannot be computed. Verify the manufacturer specification."
                    ),
                    status="verification_required",
                )
            )
            continue

        if rule.min_interior_in and (
            fixture.width_in < rule.min_interior_in or fixture.depth_in < rule.min_interior_in
        ):
            layout.unplaced.append(
                UnplacedFixture(
                    product_id=fixture.product_id,
                    product_name=fixture.product_name,
                    category=fixture.category,
                    reason=(
                        f"{fixture.product_name} is {fixture.width_in:g}in x {fixture.depth_in:g}in, "
                        f"below the {rule.min_interior_in:g}in x {rule.min_interior_in:g}in minimum "
                        "interior dimension."
                    ),
                    status="fail",
                )
            )
            continue

        placement = _find_position(fixture, room_w, room_l, layout.placed, door_swing)
        if placement is None:
            span = max(fixture.width_in, rule.min_span_in)
            layout.unplaced.append(
                UnplacedFixture(
                    product_id=fixture.product_id,
                    product_name=fixture.product_name,
                    category=fixture.category,
                    reason=(
                        f"No wall position leaves {fixture.product_name} a {span:g}in run with "
                        f"{rule.front_in:g}in of clear space in front of it once the other "
                        "fixtures and the door swing are placed."
                    ),
                    status="fail",
                    required_span_in=span,
                    required_depth_in=fixture.depth_in + rule.front_in,
                )
            )
            continue
        layout.placed.append(placement)

    layout.circulation_ok, layout.circulation_notes = _check_circulation(layout)
    layout.derived_zones = _derive_zones(layout)
    return layout


def _derive_zones(layout: RoomLayout) -> list[DerivedZone]:
    """Turn solved geometry into the fixture zones the constraint engine reads.

    A zone is the wall run and depth the solver actually reserved for that
    category — derived from the user's own room dimensions and published
    clearance rules, never guessed and never taken from an image.
    """
    zones: dict[str, DerivedZone] = {}
    for item in layout.placed:
        rule = rule_for(item.category)
        horizontal = item.wall in ("south", "north")
        wall_span = item.footprint.width_in if horizontal else item.footprint.depth_in
        projection = item.footprint.depth_in if horizontal else item.footprint.width_in

        # The zone is the floor the solver actually reserved for this category:
        # the fixture itself plus the clear space in front of it. It is therefore
        # always at least as large as the product, which keeps the downstream
        # zone-fit check consistent with the placement that produced it.
        width_ft = max(wall_span, rule.min_span_in) / 12.0
        depth_ft = (projection + rule.front_in) / 12.0

        existing = zones.get(item.category)
        zones[item.category] = DerivedZone(
            category=item.category,
            width_ft=max(width_ft, existing.width_ft if existing else 0.0),
            depth_ft=max(depth_ft, existing.depth_ft if existing else 0.0),
            derived_from=(
                f"Solved placement on the {item.wall} wall, including "
                f"{rule.front_in:g}in clear space in front ({rule.source})"
            ),
        )
    return list(zones.values())
