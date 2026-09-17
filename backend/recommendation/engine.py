from collections import defaultdict
from collections.abc import Iterable

from backend.constraints import (
    CATEGORY_ALIASES,
    BathroomConstraints,
    ConfigurationReport,
    Product,
    validate_configuration,
)

from .models import (
    CandidateConfiguration,
    ClosestAlternative,
    ConstraintViolationSummary,
    NoCompliantConfigurationResult,
    PreferenceProfile,
    RecommendationResult,
    RelaxationSuggestion,
    ScoreBreakdown,
    ScoringWeights,
)

DEFAULT_MAX_CANDIDATES = 3


def retrieve_candidate_products(
    catalog: Iterable[Product], room: BathroomConstraints
) -> dict[str, list[Product]]:
    """Group catalog products by which required category slot they can fill.
    A product fills a slot if its category is that category or a documented
    alias of it (e.g. a smart_toilet fills a 'toilet' requirement)."""
    catalog = list(catalog)
    allowed = set(room.user_constraints.allowed_categories)
    by_slot: dict[str, list[Product]] = {}
    for required in room.required_categories:
        acceptable_categories = CATEGORY_ALIASES.get(required, {required})
        matches = [product for product in catalog if product.category in acceptable_categories]
        if allowed:
            matches = [product for product in matches if product.category in allowed]
        by_slot[required] = matches
    return by_slot


MAX_CONFIGURATIONS_EVALUATED = 2000


def generate_configurations(
    candidates_by_slot: dict[str, list[Product]],
    budget: float | None = None,
    limit: int = MAX_CONFIGURATIONS_EVALUATED,
) -> list[list[Product]]:
    """One product per required-category slot, pruned as the combination is built.

    A full cartesian product over a realistic catalog is tens of thousands of
    combinations, and validating each one means solving a floor plan. Two things
    keep this tractable without changing which configurations are reachable:

    - **Budget pruning.** Slots are explored cheapest-first, and a partial
      combination whose running total already exceeds the budget is abandoned:
      every completion of it would exceed the budget too. This prunes whole
      subtrees rather than individual leaves.
    - **A hard ceiling.** Exploring cheapest-first means the ceiling, if it is
      ever reached, discards only the most expensive combinations — the ones
      least likely to survive a budget constraint anyway.

    When no budget is set, nothing is pruned and only the ceiling applies.
    """
    if not candidates_by_slot:
        return [[]]
    slots = [sorted(products, key=lambda p: p.price or 0) for products in candidates_by_slot.values()]
    if any(not slot for slot in slots):
        return []

    # Cheapest possible completion from each slot onward, for lookahead pruning.
    cheapest_remaining = [0.0] * (len(slots) + 1)
    for index in range(len(slots) - 1, -1, -1):
        cheapest_remaining[index] = cheapest_remaining[index + 1] + (slots[index][0].price or 0)

    results: list[list[Product]] = []

    def walk(index: int, chosen: list[Product], running_total: float) -> None:
        if len(results) >= limit:
            return
        if index == len(slots):
            results.append(list(chosen))
            return
        for product in slots[index]:
            price = product.price or 0
            new_total = running_total + price
            if budget is not None and new_total + cheapest_remaining[index + 1] > budget:
                # Slots are price-sorted, so every later product here is worse.
                break
            chosen.append(product)
            walk(index + 1, chosen, new_total)
            chosen.pop()
            if len(results) >= limit:
                return

    walk(0, [], 0.0)
    return results


def _spatial_score(products: list[Product], room: BathroomConstraints) -> float:
    if not products or room.room_width_ft is None or room.room_length_ft is None:
        return 0.5
    available_width = room.room_width_ft * 12
    available_depth = room.room_length_ft * 12
    pressures: list[float] = []
    for product in products:
        width = product.dimensions.width_in
        depth = product.dimensions.depth_in
        if width is None or depth is None:
            continue
        zone = room.fixture_zones.get(product.category)
        if zone is not None and zone.width_ft is not None and zone.depth_ft is not None:
            ref_width = min(available_width, zone.width_ft * 12)
            ref_depth = min(available_depth, zone.depth_ft * 12)
        else:
            ref_width = available_width
            ref_depth = available_depth
        width_pressure = width / ref_width if ref_width else 1.0
        depth_pressure = depth / ref_depth if ref_depth else 1.0
        pressures.append(max(width_pressure, depth_pressure))
    if not pressures:
        return 0.5
    avg_pressure = sum(pressures) / len(pressures)
    return max(0.0, min(1.0, 1.0 - avg_pressure))


BUDGET_SWEET_SPOT = 0.85
"""Fraction of budget a well-matched configuration is expected to use."""


def _budget_score(total_price: float, budget: float | None) -> float:
    """Score how well a configuration *uses* the budget, not how little it spends.

    Someone with a Rs 2.5 lakh budget is not better served by a Rs 76,000 plan.
    Spending far under budget means leaving quality on the table just as surely
    as going over means the plan is unaffordable. This peaks near 85% of budget
    and falls away on both sides; over budget scores zero, because the hard
    constraint has already rejected it and score must never rescue it.
    """
    if not budget:
        return 0.5
    ratio = total_price / budget
    if ratio > 1.0:
        return 0.0
    if ratio >= BUDGET_SWEET_SPOT:
        # 0.85 -> 1.0 tapering to 1.0 -> 0.85 as it approaches the ceiling.
        return 1.0 - 0.15 * (ratio - BUDGET_SWEET_SPOT) / (1.0 - BUDGET_SWEET_SPOT)
    return max(0.0, ratio / BUDGET_SWEET_SPOT)


def _style_score(products: list[Product], preference: PreferenceProfile) -> float:
    if not preference.preferred_styles:
        return 1.0
    present_styles = {style for product in products for style in product.style}
    matched = present_styles.intersection(preference.preferred_styles)
    return len(matched) / len(preference.preferred_styles)


def _smart_feature_score(products: list[Product], preference: PreferenceProfile) -> float:
    has_smart = any(product.smart.features for product in products)
    if preference.smart_feature_preference == "prefer":
        base = 1.0 if has_smart else 0.0
    elif preference.smart_feature_preference == "avoid":
        base = 0.0 if has_smart else 1.0
    else:
        base = 0.5

    if preference.preferred_smart_features:
        present_features = {feature for product in products for feature in product.smart.features}
        matched = present_features.intersection(preference.preferred_smart_features)
        feature_fraction = len(matched) / len(preference.preferred_smart_features)
        base = (base + feature_fraction) / 2
    return base


WATER_RELEVANT_CATEGORIES = frozenset({"toilet", "smart_toilet", "faucet", "shower", "smart_shower"})


def _water_efficiency_score(products: list[Product]) -> tuple[float, list[str]]:
    """Average efficiency across the products that actually use water.

    A vanity has no flow rate. That is not an unknown to be scored neutrally —
    it is simply not a water fixture, and including it would dilute the score of
    every configuration toward 0.5 and make the dimension meaningless.

    For products that do use water, efficiency is read from the *computed*
    eligibility flag (recorded flow against the published WaterSense threshold),
    not from a certification claim. A missing flow figure stays unknown: scored
    neutrally and flagged, never assumed efficient.
    """
    scores: list[float] = []
    notes: list[str] = []
    for product in products:
        if product.category not in WATER_RELEVANT_CATEGORIES:
            continue
        water = product.water
        verdict = water.watersense_eligible
        if verdict is None:
            verdict = water.watersense_certified
        if verdict is True:
            scores.append(1.0)
        elif verdict is False:
            # Records a real, measured figure that exceeds the threshold. Known,
            # not unknown — so it scores low rather than neutral.
            scores.append(0.2)
        else:
            notes.append(
                f"No flow or flush figure is recorded for {product.name}; scored as neutral "
                "pending manufacturer-specification verification."
            )
            scores.append(0.5)
    if not scores:
        return 0.5, notes
    return sum(scores) / len(scores), notes


def _preference_score(products: list[Product], preference: PreferenceProfile) -> float:
    if preference.storage_preference == "neutral":
        return 1.0
    vanities = [product for product in products if product.category == "vanity"]
    widths = [v.dimensions.width_in for v in vanities if v.dimensions.width_in is not None]
    if not widths:
        return 0.5
    avg_width = sum(widths) / len(widths)
    if preference.storage_preference == "spacious":
        return 1.0 if avg_width >= 48 else 0.3
    return 1.0 if avg_width <= 36 else 0.3


def score_configuration(
    products: list[Product],
    room: BathroomConstraints,
    preference: PreferenceProfile,
    weights: ScoringWeights,
) -> tuple[ScoreBreakdown, list[str]]:
    total_price = sum(product.price or 0 for product in products)
    spatial = _spatial_score(products, room)
    budget = _budget_score(total_price, room.budget)
    style = _style_score(products, preference)
    smart_feature = _smart_feature_score(products, preference)
    water_efficiency, water_notes = _water_efficiency_score(products)
    preference_score = _preference_score(products, preference)

    weight_values = weights.as_dict()
    dimension_scores = {
        "spatial": spatial,
        "budget": budget,
        "preference": preference_score,
        "water_efficiency": water_efficiency,
        "style": style,
        "smart_feature": smart_feature,
    }
    total_weight = sum(weight_values.values())
    if total_weight > 0:
        total = sum(dimension_scores[key] * weight_values[key] for key in dimension_scores) / total_weight
    else:
        total = sum(dimension_scores.values()) / len(dimension_scores)

    return (
        ScoreBreakdown(
            spatial=spatial,
            budget=budget,
            preference=preference_score,
            water_efficiency=water_efficiency,
            style=style,
            smart_feature=smart_feature,
            weights=weights,
            total=total,
        ),
        water_notes,
    )


def _extract_installation_warnings(report: ConfigurationReport) -> list[str]:
    return [check.reason for check in report.checks if check.constraint == "installation" and check.status == "warning"]


def _extract_verification_notes(report: ConfigurationReport) -> list[str]:
    return [check.reason for check in report.checks if check.status == "warning" and check.constraint != "installation"]


def _annotate_relative(candidates: list[CandidateConfiguration]) -> None:
    if not candidates:
        return
    prices = [candidate.total_price for candidate in candidates]
    min_price, max_price = min(prices), max(prices)
    max_spatial = max(candidate.score.spatial for candidate in candidates)

    for candidate in candidates:
        if min_price != max_price:
            if candidate.total_price == min_price:
                candidate.strengths.append("Lowest total cost among the returned options.")
            else:
                candidate.trade_offs.append(
                    f"Costs {candidate.total_price - min_price:g} {candidate.currency} more than "
                    "the least expensive option returned."
                )
        has_smart = any(product.smart.features for product in candidate.products)
        if has_smart:
            features = sorted({feature for product in candidate.products for feature in product.smart.features})
            candidate.strengths.append(f"Includes smart features: {', '.join(features)}.")
        else:
            candidate.trade_offs.append("Does not include smart features.")
        if candidate.score.spatial == max_spatial and len(candidates) > 1:
            candidate.strengths.append("Most spacious layout among the returned options.")


def _select_diverse_candidates(
    candidates: list[CandidateConfiguration], max_candidates: int
) -> list[CandidateConfiguration]:
    """Pick options that represent genuinely different trade-offs.

    Returning the top three by score tends to return the same configuration
    three times with one component swapped — technically the highest scores,
    practically not a choice at all. Instead each slot is filled by a different
    archetype, so the user is choosing between positions rather than between
    rounding errors:

      1. the best overall balance,
      2. the least expensive option that still holds up,
      3. the most water-efficient option.

    Ranking integrity is preserved: every candidate here already passed the hard
    constraints, and a fully verified configuration is never displaced by an
    unverified one because the pool is ordered by tier before selection.
    """
    if not candidates:
        return []

    def tier(candidate: CandidateConfiguration) -> int:
        return 0 if candidate.constraint_report.status == "feasible" else 1

    best_tier = min(tier(candidate) for candidate in candidates)
    pool = [candidate for candidate in candidates if tier(candidate) == best_tier]

    selected: list[CandidateConfiguration] = []
    chosen_ids: set[frozenset[str]] = set()

    def take(candidate: CandidateConfiguration | None, label: str) -> None:
        if candidate is None or len(selected) >= max_candidates:
            return
        key = frozenset(product.id for product in candidate.products)
        if key in chosen_ids:
            return
        candidate.label = label
        chosen_ids.add(key)
        selected.append(candidate)

    def best_by(key, exclude_chosen: bool = True):
        remaining = [
            candidate
            for candidate in pool
            if not exclude_chosen
            or frozenset(p.id for p in candidate.products) not in chosen_ids
        ]
        return max(remaining, key=key) if remaining else None

    take(best_by(lambda c: c.score.total), "recommended")
    take(best_by(lambda c: -c.total_price), "budget_focused")
    take(best_by(lambda c: (c.score.water_efficiency, c.score.total)), "sustainability_focused")

    # Backfill by score if archetypes collided on the same configuration.
    while len(selected) < max_candidates:
        filler = best_by(lambda c: c.score.total)
        if filler is None:
            break
        take(filler, "alternative")

    return selected


def _summarize_violations(
    evaluated: list[tuple[list[Product], ConfigurationReport]],
    missing_slots: list[str],
) -> list[ConstraintViolationSummary]:
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for _, report in evaluated:
        for check in report.checks:
            if check.passed:
                continue
            key = (check.constraint, check.status)
            if len(grouped[key]) < 5:
                grouped[key].append(check.reason)

    for slot in missing_slots:
        key = ("category_requirements", "fail")
        grouped[key].append(f"No catalog product is available to satisfy required category '{slot}'.")

    summaries = []
    for (constraint, status), reasons in grouped.items():
        summaries.append(
            ConstraintViolationSummary(
                constraint=constraint,
                status=status,
                occurrences=len(reasons),
                example_reasons=reasons,
            )
        )
    return summaries


def _closest_alternatives(
    evaluated: list[tuple[list[Product], ConfigurationReport]],
    max_candidates: int,
) -> list[ClosestAlternative]:
    def violation_count(item: tuple[list[Product], ConfigurationReport]) -> int:
        return sum(1 for check in item[1].checks if not check.passed and check.blocking)

    ranked = sorted(evaluated, key=lambda item: (violation_count(item), sum(p.price or 0 for p in item[0])))
    alternatives = []
    for products, report in ranked[:max_candidates]:
        alternatives.append(
            ClosestAlternative(
                products=products,
                total_price=sum(product.price or 0 for product in products),
                currency=products[0].currency if products else "INR",
                constraint_report=report,
                violations=[check for check in report.checks if not check.passed],
            )
        )
    return alternatives


def _suggest_relaxations(
    evaluated: list[tuple[list[Product], ConfigurationReport]],
    missing_slots: list[str],
    room: BathroomConstraints,
) -> list[RelaxationSuggestion]:
    seen: set[str] = set()
    suggestions: list[RelaxationSuggestion] = []

    def add(constraint: str, description: str, product_ids: list[str]) -> None:
        if description in seen:
            return
        seen.add(description)
        suggestions.append(RelaxationSuggestion(constraint=constraint, description=description, product_ids=product_ids))

    for slot in missing_slots:
        add(
            "category_requirements",
            f"Add a catalog product for required category '{slot}', or remove it from required categories.",
            [],
        )

    min_overage: float | None = None
    for products, report in evaluated:
        for check in report.checks:
            if check.passed:
                continue
            if check.constraint == "budget" and check.status == "fail":
                total = check.details.get("total")
                budget = check.details.get("budget")
                if total is not None and budget is not None:
                    overage = total - budget
                    if min_overage is None or overage < min_overage:
                        min_overage = overage
            elif check.constraint in {"spatial_fit", "fixture_zone_fit"} and check.status == "fail":
                product_id = check.details.get("product_id")
                add(
                    check.constraint,
                    f"Increase the available room or fixture-zone dimensions for product '{product_id}', "
                    "or choose a smaller product for that slot.",
                    [product_id] if product_id else [],
                )
            elif check.constraint == "electrical":
                add(
                    "electrical",
                    "Confirm electrical availability in the room for smart/powered products.",
                    check.details.get("product_ids", []),
                )
            elif check.constraint == "installation":
                add(
                    "installation",
                    "Confirm the toilet rough-in measurement for the room and the selected product.",
                    [check.details.get("product_id")] if check.details.get("product_id") else [],
                )
            elif check.constraint == "compatibility":
                missing = check.details.get("missing_interfaces") or []
                if missing:
                    add(
                        "compatibility",
                        f"Choose products whose connections match: nothing in this configuration "
                        f"provides {', '.join(missing)}. A faucet must match the basin's drilling.",
                        [check.details.get("product_id")] if check.details.get("product_id") else [],
                    )
                else:
                    add(
                        "compatibility",
                        "Replace one of the flagged products; they are recorded as incompatible.",
                        check.details.get("product_ids") or check.details.get("incompatible_product_ids", []),
                    )
            elif check.constraint == "layout_fit" and check.status == "fail":
                category = check.details.get("category")
                product_id = check.details.get("product_id")
                add(
                    "layout_fit",
                    f"No wall position remains for the {category or 'fixture'}. Either drop "
                    f"'{category}' from the required categories, choose a smaller product for "
                    "that slot, or plan a larger room.",
                    [product_id] if product_id else [],
                )
                if category:
                    add(
                        "category_requirements",
                        f"Remove '{category}' from the required categories — the room cannot "
                        "hold every requested fixture at once.",
                        [],
                    )
            elif check.constraint == "circulation":
                add(
                    "circulation",
                    "The room cannot be navigated with every requested fixture in place. "
                    "Remove one fixture, or choose more compact products.",
                    [],
                )
            elif check.constraint == "user_constraints":
                add(
                    "user_constraints",
                    "Relax the explicit user constraint (allowed categories, required styles, or max depth) that excluded these products.",
                    check.details.get("disallowed_product_ids", []),
                )

    if min_overage is not None:
        add(
            "budget",
            f"Increase the budget by at least {min_overage:g} {room.currency} to reach the closest compliant option.",
            [],
        )

    return suggestions


def recommend(
    catalog: Iterable[Product],
    room: BathroomConstraints,
    preference: PreferenceProfile | None = None,
    weights: ScoringWeights | None = None,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
) -> RecommendationResult:
    preference = preference or PreferenceProfile()
    weights = weights or ScoringWeights()
    catalog = list(catalog)

    candidates_by_slot = retrieve_candidate_products(catalog, room)
    missing_slots = [slot for slot, products in candidates_by_slot.items() if not products]
    combos = generate_configurations(candidates_by_slot, room.budget) if not missing_slots else []
    budget_pruned_everything = not combos and not missing_slots and room.budget is not None
    if budget_pruned_everything:
        # Every combination was abandoned for exceeding the budget. Rebuild a
        # bounded unpruned set so the conflict can be quantified — the user needs
        # to know *how far* over budget the closest option is, not just that
        # nothing fit.
        combos = generate_configurations(candidates_by_slot, budget=None, limit=200)

    evaluated = [(combo, validate_configuration(combo, room)) for combo in combos]
    # Offerable, not merely feasible: a configuration with nothing proven broken
    # is worth showing, provided its outstanding verifications travel with it.
    valid = [(products, report) for products, report in evaluated if report.offerable]

    if valid:
        candidate_objs: list[CandidateConfiguration] = []
        for products, report in valid:
            total_price = sum(product.price or 0 for product in products)
            remaining_budget = (room.budget - total_price) if room.budget is not None else None
            score, water_notes = score_configuration(products, room, preference, weights)
            candidate_objs.append(
                CandidateConfiguration(
                    products=products,
                    total_price=total_price,
                    currency=products[0].currency if products else room.currency,
                    remaining_budget=remaining_budget,
                    constraint_report=report,
                    score=score,
                    installation_warnings=_extract_installation_warnings(report),
                    verification_requirements=(
                        report.verification_requirements + _extract_verification_notes(report) + water_notes
                    ),
                )
            )
        # A fully verified configuration always outranks one with outstanding
        # verifications, whatever the scores say. Score only breaks ties inside a
        # tier — it can never promote an unverified option above a verified one.
        candidate_objs.sort(
            key=lambda candidate: (
                0 if candidate.constraint_report.status == "feasible" else 1,
                -candidate.score.total,
                candidate.total_price,
            )
        )
        top = _select_diverse_candidates(candidate_objs, max_candidates)
        _annotate_relative(top)
        return RecommendationResult(status="ok", candidates=top)

    return RecommendationResult(
        status="no_fully_compliant_configuration",
        no_compliant_configuration=NoCompliantConfigurationResult(
            violated_constraints=_summarize_violations(evaluated, missing_slots),
            closest_alternatives=_closest_alternatives(evaluated, max_candidates),
            possible_relaxations=_suggest_relaxations(evaluated, missing_slots, room),
        ),
    )
