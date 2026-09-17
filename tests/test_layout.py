"""Tests for the deterministic layout solver.

These are the tests that make the spatial claim defensible. Each one states a
physical fact about a bathroom and asserts the solver agrees.
"""

from backend.layout import DoorSpec, FixtureRequest, solve_layout
from backend.layout.clearances import rule_for


def fixture(category: str, width: float | None, depth: float | None, pid: str | None = None):
    return FixtureRequest(
        product_id=pid or f"{category}_1",
        product_name=category.replace("_", " ").title(),
        category=category,
        width_in=width,
        depth_in=depth,
    )


def test_standard_bathroom_places_every_fixture_legally() -> None:
    layout = solve_layout(
        [fixture("toilet", 28, 29), fixture("vanity", 30, 20), fixture("shower", 36, 36)],
        room_width_ft=6,
        room_length_ft=8,
        door=DoorSpec(),
    )

    assert layout.solved is True
    assert len(layout.placed) == 3
    assert layout.circulation_ok is True


def test_placed_footprints_never_overlap_each_other() -> None:
    layout = solve_layout(
        [fixture("toilet", 28, 29), fixture("vanity", 30, 20), fixture("shower", 36, 36)],
        room_width_ft=6,
        room_length_ft=8,
        door=DoorSpec(),
    )

    footprints = [item.footprint for item in layout.placed]
    for index, left in enumerate(footprints):
        for right in footprints[index + 1 :]:
            assert not left.overlaps(right)


def test_no_fixture_clearance_is_blocked_by_another_fixture() -> None:
    """A fixture you cannot stand in front of is not installed, it is stored."""
    layout = solve_layout(
        [fixture("toilet", 28, 29), fixture("vanity", 30, 20), fixture("shower", 36, 36)],
        room_width_ft=6,
        room_length_ft=8,
        door=DoorSpec(),
    )

    for item in layout.placed:
        for other in layout.placed:
            if other.product_id == item.product_id:
                continue
            assert not item.clearance.overlaps(other.footprint)


def test_everything_stays_inside_the_room() -> None:
    layout = solve_layout(
        [fixture("toilet", 28, 29), fixture("vanity", 30, 20)],
        room_width_ft=6,
        room_length_ft=8,
        door=DoorSpec(),
    )

    for item in layout.placed:
        assert item.footprint.within(layout.room_width_in, layout.room_length_in)
        assert item.clearance.within(layout.room_width_in, layout.room_length_in)


def test_luxury_fixtures_do_not_fit_a_five_by_five_room() -> None:
    """CASE A: the request that must fail, and must say why it failed."""
    layout = solve_layout(
        [
            fixture("smart_toilet", 28, 30),
            fixture("vanity", 72, 22),
            fixture("shower", 36, 36),
        ],
        room_width_ft=5,
        room_length_ft=5,
        door=DoorSpec(),
    )

    assert layout.solved is False
    assert len(layout.unplaced) == 2
    for item in layout.unplaced:
        assert item.status == "fail"
        assert item.reason
        assert item.required_span_in is not None


def test_undersized_shower_fails_minimum_interior_dimension() -> None:
    layout = solve_layout([fixture("shower", 24, 24)], 6, 8, DoorSpec())

    assert layout.solved is False
    assert layout.unplaced[0].status == "fail"
    assert "30in" in layout.unplaced[0].reason


def test_unknown_product_dimensions_require_verification_and_never_pass() -> None:
    layout = solve_layout([fixture("vanity", None, None)], 6, 8, DoorSpec())

    assert layout.solved is False
    assert layout.unplaced[0].status == "verification_required"
    assert not layout.placed


def test_missing_room_dimensions_block_layout_entirely() -> None:
    layout = solve_layout([fixture("toilet", 28, 29)], None, None, DoorSpec())

    assert layout.solved is False
    assert layout.unplaced[0].status == "verification_required"
    assert "Room dimensions are required" in layout.unplaced[0].reason


def test_wall_mounted_products_consume_no_floor_area() -> None:
    layout = solve_layout(
        [fixture("toilet", 28, 29), fixture("faucet", 8, 6)], 6, 8, DoorSpec()
    )

    placed_categories = {item.category for item in layout.placed}
    assert "faucet" not in placed_categories
    assert "toilet" in placed_categories
    assert not layout.unplaced


def test_inward_door_swing_consumes_floor_and_outward_does_not() -> None:
    fixtures = [fixture("toilet", 28, 29), fixture("vanity", 48, 22), fixture("shower", 36, 36)]
    inward = solve_layout(fixtures, 5, 7, DoorSpec(swing="inward", width_in=32))
    outward = solve_layout(fixtures, 5, 7, DoorSpec(swing="outward", width_in=32))

    # An outward-opening door frees the floor its swing would have taken, so it
    # can only ever place at least as many fixtures as the inward case.
    assert len(outward.placed) >= len(inward.placed)


def test_derived_zone_is_never_smaller_than_the_product_it_came_from() -> None:
    """Regression: the zone the solver reserves must contain the fixture it placed."""
    layout = solve_layout([fixture("toilet", 28, 29), fixture("vanity", 30, 20)], 6, 8, DoorSpec())

    zones = {zone.category: zone for zone in layout.derived_zones}
    for item in layout.placed:
        zone = zones[item.category]
        horizontal = item.wall in ("south", "north")
        span = item.footprint.width_in if horizontal else item.footprint.depth_in
        projection = item.footprint.depth_in if horizontal else item.footprint.width_in
        assert zone.width_ft * 12 >= span
        assert zone.depth_ft * 12 >= projection


def test_derived_zone_includes_the_code_clearance() -> None:
    layout = solve_layout([fixture("toilet", 28, 29)], 6, 8, DoorSpec())

    zone = layout.derived_zones[0]
    expected_depth_in = 29 + rule_for("toilet").front_in
    assert abs(zone.depth_ft * 12 - expected_depth_in) < 0.01
    assert "clear space in front" in zone.derived_from


def test_solver_is_deterministic() -> None:
    fixtures = [fixture("toilet", 28, 29), fixture("vanity", 30, 20), fixture("shower", 36, 36)]
    first = solve_layout(fixtures, 6, 8, DoorSpec())
    second = solve_layout(fixtures, 6, 8, DoorSpec())

    assert first.model_dump() == second.model_dump()


def test_large_room_accommodates_a_full_premium_suite() -> None:
    layout = solve_layout(
        [
            fixture("smart_toilet", 28, 30),
            fixture("vanity", 72, 22),
            fixture("shower", 48, 36),
            fixture("bathtub", 60, 32),
        ],
        room_width_ft=12,
        room_length_ft=12,
        door=DoorSpec(),
    )

    assert layout.solved is True
    assert len(layout.placed) == 4
