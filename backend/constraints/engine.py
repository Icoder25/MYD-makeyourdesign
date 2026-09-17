from collections.abc import Iterable

from backend.layout import FixtureRequest, RoomLayout, solve_layout

from .models import BathroomConstraints, CheckResult, ConfigurationReport, FixtureZone, Product

CATEGORY_ALIASES = {
    "toilet": {"toilet", "smart_toilet"},
    "smart_toilet": {"smart_toilet"},
}


def _check(
    constraint: str,
    passed: bool,
    status: str,
    reason: str,
    *,
    blocking: bool | None = None,
    **details: object,
) -> CheckResult:
    """Build a check result.

    ``blocking`` defaults to ``status == "fail"``. Only a *proven* failure makes
    a configuration infeasible. An unknown still does not pass — it surfaces as
    an outstanding verification requirement instead of being silently upgraded.
    """
    return CheckResult(
        constraint=constraint,
        passed=passed,
        status=status,  # type: ignore[arg-type]
        reason=reason,
        blocking=(status == "fail") if blocking is None else blocking,
        details=details,
    )


def fits_room(product: Product, room: BathroomConstraints) -> CheckResult:
    dimensions = product.dimensions
    if room.room_width_ft is None or room.room_length_ft is None:
        return _check(
            "spatial_fit",
            False,
            "verification_required",
            "Room width and length are required before spatial fit can be verified.",
            product_id=product.id,
        )
    if dimensions.width_in is None or dimensions.depth_in is None:
        return _check(
            "spatial_fit",
            False,
            "verification_required",
            "Product width and depth are unknown; verify the manufacturer specification.",
            product_id=product.id,
        )

    available_width = room.room_width_ft * 12
    available_depth = room.room_length_ft * 12
    passed = dimensions.width_in <= available_width and dimensions.depth_in <= available_depth
    if passed:
        reason = f"{product.name} fits within the {available_width:g}in by {available_depth:g}in room envelope."
    else:
        reason = f"{product.name} needs {dimensions.width_in:g}in by {dimensions.depth_in:g}in, exceeding the room envelope."
    return _check(
        "spatial_fit",
        passed,
        "pass" if passed else "fail",
        reason,
        product_id=product.id,
        available_width_in=available_width,
        available_depth_in=available_depth,
    )


def fits_fixture_zone(product: Product, room: BathroomConstraints) -> CheckResult:
    zone = room.fixture_zones.get(product.category)
    if zone is None:
        return _check(
            "fixture_zone_fit",
            False,
            "verification_required",
            f"No verified fixture zone is available for category '{product.category}'.",
            product_id=product.id,
        )
    if zone.width_ft is None or zone.depth_ft is None:
        return _check(
            "fixture_zone_fit",
            False,
            "verification_required",
            f"The {product.category} fixture zone dimensions are unknown.",
            product_id=product.id,
        )
    if product.dimensions.width_in is None or product.dimensions.depth_in is None:
        return _check(
            "fixture_zone_fit",
            False,
            "verification_required",
            "Product dimensions are unknown; verify the manufacturer specification.",
            product_id=product.id,
        )

    available_width = zone.width_ft * 12
    available_depth = zone.depth_ft * 12
    passed = product.dimensions.width_in <= available_width and product.dimensions.depth_in <= available_depth
    return _check(
        "fixture_zone_fit",
        passed,
        "pass" if passed else "fail",
        (
            f"{product.name} fits its {product.category} zone."
            if passed
            else f"{product.name} exceeds its {product.category} zone of {available_width:g}in by {available_depth:g}in."
        ),
        product_id=product.id,
    )


def within_budget(products: Iterable[Product], room: BathroomConstraints) -> CheckResult:
    products = list(products)
    if room.budget is None:
        return _check("budget", False, "verification_required", "A maximum budget is required.")
    if any(product.price is None for product in products):
        return _check("budget", False, "verification_required", "One or more product prices are unknown.")
    mismatched = [product.id for product in products if product.currency != room.currency]
    if mismatched:
        return _check("budget", False, "verification_required", "Product and room currencies are not aligned.", product_ids=mismatched)

    total = sum(product.price or 0 for product in products)
    passed = total <= room.budget
    difference = room.budget - total
    return _check(
        "budget",
        passed,
        "pass" if passed else "fail",
        (
            f"Configuration costs {total:g} {room.currency}, within budget by {difference:g}."
            if passed
            else f"Configuration exceeds budget by {-difference:g} {room.currency}."
        ),
        total=total,
        budget=room.budget,
    )


def check_required_categories(products: Iterable[Product], room: BathroomConstraints) -> CheckResult:
    products = list(products)
    present = {product.category for product in products}
    missing = [
        required
        for required in room.required_categories
        if not present.intersection(CATEGORY_ALIASES.get(required, {required}))
    ]
    passed = not missing
    return _check(
        "category_requirements",
        passed,
        "pass" if passed else "fail",
        "All required categories are present." if passed else f"Missing required categories: {', '.join(missing)}.",
        missing=missing,
    )


def check_compatibility(products: Iterable[Product]) -> CheckResult:
    products = list(products)
    ids = {product.id for product in products}
    for product in products:
        conflict = ids.intersection(product.incompatible_with)
        if conflict:
            return _check(
                "compatibility",
                False,
                "fail",
                f"{product.name} is explicitly incompatible with {', '.join(sorted(conflict))}.",
                product_id=product.id,
                incompatible_product_ids=sorted(conflict),
            )

    for index, left in enumerate(products):
        for right in products[index + 1 :]:
            if not left.compatibility_group or not right.compatibility_group:
                return _check(
                    "compatibility",
                    False,
                    "verification_required",
                    f"Compatibility between {left.name} and {right.name} is not documented.",
                    product_ids=[left.id, right.id],
                )
            if not set(left.compatibility_group).intersection(right.compatibility_group):
                return _check(
                    "compatibility",
                    False,
                    "verification_required",
                    f"No shared compatibility group is documented for {left.name} and {right.name}.",
                    product_ids=[left.id, right.id],
                )
    return _check("compatibility", True, "pass", "All product pairs have documented compatibility.")


def check_power_requirement(products: Iterable[Product], room: BathroomConstraints) -> CheckResult:
    powered = [product for product in products if product.electrical_required is True or product.smart.features]
    if not powered:
        return _check("electrical", True, "pass", "No product in the configuration requires electrical power.", blocking=False)
    if room.electrical_available is None:
        return _check(
            "electrical",
            False,
            "verification_required",
            "Electrical availability is unknown for powered products.",
            product_ids=[product.id for product in powered],
        )
    if not room.electrical_available:
        return _check(
            "electrical",
            False,
            "fail",
            "The room has no confirmed electrical availability for powered products.",
            product_ids=[product.id for product in powered],
        )
    return _check("electrical", True, "pass", "Electrical availability is confirmed for powered products.", blocking=False)


def check_installation(products: Iterable[Product], room: BathroomConstraints) -> CheckResult:
    warnings: list[str] = []
    for product in products:
        is_toilet = product.category in CATEGORY_ALIASES["toilet"]
        product_rough_in = product.installation.rough_in_in
        if is_toilet:
            if product_rough_in is None or room.toilet_rough_in_in is None:
                return _check(
                    "installation",
                    False,
                    "verification_required",
                    f"Toilet rough-in for {product.name} cannot be verified.",
                    product_id=product.id,
                )
            if abs(product_rough_in - room.toilet_rough_in_in) > 0.5:
                return _check(
                    "installation",
                    False,
                    "fail",
                    f"{product.name} rough-in does not match the verified room rough-in.",
                    product_id=product.id,
                    product_rough_in_in=product_rough_in,
                    room_rough_in_in=room.toilet_rough_in_in,
                )
        elif product.installation.type is None:
            warnings.append(f"Installation method for {product.name} is not documented; verify before purchase.")
    if warnings:
        return _check("installation", True, "warning", " ".join(warnings), blocking=False)
    return _check("installation", True, "pass", "Installation requirements are verified for the configuration.", blocking=False)


def check_user_constraints(products: Iterable[Product], room: BathroomConstraints) -> CheckResult:
    products = list(products)
    constraints = room.user_constraints
    disallowed = [product.id for product in products if constraints.allowed_categories and product.category not in constraints.allowed_categories]
    style_misses = [
        product.id
        for product in products
        if constraints.required_styles and not set(constraints.required_styles).intersection(product.style)
    ]
    depth_misses = [
        product.id
        for product in products
        if constraints.max_product_depth_in is not None
        and product.dimensions.depth_in is not None
        and product.dimensions.depth_in > constraints.max_product_depth_in
    ]
    unknown_depths = [
        product.id
        for product in products
        if constraints.max_product_depth_in is not None and product.dimensions.depth_in is None
    ]
    if unknown_depths:
        return _check(
            "user_constraints",
            False,
            "verification_required",
            "A product depth required by the user is unknown.",
            product_ids=unknown_depths,
        )
    if disallowed or style_misses or depth_misses:
        return _check(
            "user_constraints",
            False,
            "fail",
            "One or more products violate explicit user constraints.",
            disallowed_product_ids=disallowed,
            style_mismatch_product_ids=style_misses,
            depth_mismatch_product_ids=depth_misses,
        )
    return _check("user_constraints", True, "pass", "All explicit user constraints are satisfied.")


def build_layout(products: Iterable[Product], room: BathroomConstraints) -> RoomLayout:
    """Run the deterministic layout solver for this configuration in this room."""
    requests = [
        FixtureRequest(
            product_id=product.id,
            product_name=product.name,
            category=product.category,
            width_in=product.dimensions.width_in,
            depth_in=product.dimensions.depth_in,
        )
        for product in products
    ]
    return solve_layout(requests, room.room_width_ft, room.room_length_ft, room.door)


def check_layout(layout: RoomLayout) -> list[CheckResult]:
    """Turn solved geometry into constraint results.

    This is where "does it fit?" stops being a bounding-box comparison against
    the room rectangle and becomes a real question: can every fixture hold a
    legal position, with code clearance in front of it, without blocking the
    door or each other, and can a person still reach all of them?
    """
    checks: list[CheckResult] = []

    for item in layout.unplaced:
        checks.append(
            _check(
                "layout_fit",
                False,
                item.status,
                item.reason,
                product_id=item.product_id,
                category=item.category,
                required_span_in=item.required_span_in,
                required_depth_in=item.required_depth_in,
            )
        )

    if layout.placed and not layout.unplaced:
        checks.append(
            _check(
                "layout_fit",
                True,
                "pass",
                f"All {len(layout.placed)} floor-standing fixtures hold a legal position with "
                "the required clearance in front of each.",
                placed=[item.product_id for item in layout.placed],
            )
        )

    if not layout.circulation_ok:
        for note in layout.circulation_notes or ["The room cannot be navigated once every fixture is placed."]:
            checks.append(_check("circulation", False, "fail", note))
    elif layout.placed:
        checks.append(
            _check(
                "circulation",
                True,
                "pass",
                "Every fixture's clear space is reachable from the doorway.",
            )
        )

    return checks


def _room_with_derived_zones(room: BathroomConstraints, layout: RoomLayout) -> BathroomConstraints:
    """Fill in any fixture zone the user did not state, using solved geometry.

    A zone the solver derived from the user's own room dimensions and published
    clearance rules is a computed fact, not an assumption. A zone the user
    stated explicitly always wins over a derived one.
    """
    derived = layout.zones_as_constraint_input()
    if not derived:
        return room
    merged = dict(room.fixture_zones)
    for category, dims in derived.items():
        if category not in merged:
            merged[category] = FixtureZone.model_validate(dims)
    return room.model_copy(update={"fixture_zones": merged})


def validate_configuration(
    products: Iterable[Product],
    room: BathroomConstraints,
    layout: RoomLayout | None = None,
) -> ConfigurationReport:
    products = list(products)
    if layout is None:
        layout = build_layout(products, room)
    effective_room = _room_with_derived_zones(room, layout)

    checks = [
        check_required_categories(products, room),
        within_budget(products, room),
        check_compatibility(products),
    ]
    checks.extend(fits_room(product, room) for product in products)
    checks.extend(fits_fixture_zone(product, effective_room) for product in products)
    checks.extend(check_layout(layout))
    checks.extend(
        [
            check_power_requirement(products, room),
            check_installation(products, room),
            check_user_constraints(products, room),
        ]
    )

    blocking_failures = [check.reason for check in checks if not check.passed and check.blocking]
    verification_requirements = [
        check.reason for check in checks if not check.passed and not check.blocking
    ]

    if blocking_failures:
        status = "infeasible"
    elif verification_requirements:
        status = "feasible_pending_verification"
    else:
        status = "feasible"

    return ConfigurationReport(
        status=status,
        feasible=status == "feasible",
        offerable=status != "infeasible",
        checks=checks,
        blocking_failures=blocking_failures,
        verification_requirements=verification_requirements,
    )
