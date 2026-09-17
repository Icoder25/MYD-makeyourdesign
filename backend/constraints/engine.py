from collections.abc import Iterable

from .models import BathroomConstraints, CheckResult, ConfigurationReport, Product

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
    blocking: bool = True,
    **details: object,
) -> CheckResult:
    return CheckResult(
        constraint=constraint,
        passed=passed,
        status=status,  # type: ignore[arg-type]
        reason=reason,
        blocking=blocking,
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


def validate_configuration(products: Iterable[Product], room: BathroomConstraints) -> ConfigurationReport:
    products = list(products)
    checks = [check_required_categories(products, room), within_budget(products, room), check_compatibility(products)]
    checks.extend(fits_room(product, room) for product in products)
    checks.extend(fits_fixture_zone(product, room) for product in products)
    checks.extend([check_power_requirement(products, room), check_installation(products, room), check_user_constraints(products, room)])
    return ConfigurationReport(feasible=all(check.passed for check in checks), checks=checks)
