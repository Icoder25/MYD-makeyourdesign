from collections.abc import Iterable

from backend.constraints import BathroomConstraints, Product, validate_configuration

from .models import TradeoffOption, TradeoffResult


def propose_budget_reduction(
    current_products: list[Product],
    catalog: Iterable[Product],
    room: BathroomConstraints,
    preserve_categories: Iterable[str],
) -> TradeoffResult:
    """Given a current configuration, find substitutions or removals for the
    categories NOT in `preserve_categories` that reduce total price while
    keeping the configuration valid and keeping every preserved category
    untouched. This is the deterministic answer to requests such as
    "keep smart features but reduce budget" once the caller (an LLM or a
    structured form) has translated that into preserve_categories=["smart_toilet"].
    """
    catalog = list(catalog)
    preserve = set(preserve_categories)
    movable = [product for product in current_products if product.category not in preserve]

    options: list[TradeoffOption] = []
    for product in movable:
        cheaper_alternatives = sorted(
            (
                candidate
                for candidate in catalog
                if candidate.category == product.category
                and candidate.id != product.id
                and (candidate.price or 0) < (product.price or 0)
            ),
            key=lambda candidate: candidate.price or 0,
        )
        for alternative in cheaper_alternatives:
            trial = [alternative if p.id == product.id else p for p in current_products]
            report = validate_configuration(trial, room)
            if not report.feasible:
                continue
            price_delta = (alternative.price or 0) - (product.price or 0)
            options.append(
                TradeoffOption(
                    action="substitute",
                    category=product.category,
                    removed_product_id=product.id,
                    added_product_id=alternative.id,
                    price_delta=price_delta,
                    resulting_total_price=sum(p.price or 0 for p in trial),
                    resulting_report=report,
                    description=(
                        f"Replace {product.name} with {alternative.name} to save "
                        f"{-price_delta:g} {room.currency} while keeping "
                        f"{', '.join(sorted(preserve)) or 'all preserved categories'} unchanged."
                    ),
                )
            )
            break  # cheapest valid alternative for this product is enough

        if product.category not in room.required_categories:
            trial = [p for p in current_products if p.id != product.id]
            if trial:
                report = validate_configuration(trial, room)
                if report.feasible:
                    price_delta = -(product.price or 0)
                    options.append(
                        TradeoffOption(
                            action="remove",
                            category=product.category,
                            removed_product_id=product.id,
                            added_product_id=None,
                            price_delta=price_delta,
                            resulting_total_price=sum(p.price or 0 for p in trial),
                            resulting_report=report,
                            description=(
                                f"Remove {product.name} (category '{product.category}' is not required) "
                                f"to save {-price_delta:g} {room.currency}."
                            ),
                        )
                    )

    options.sort(key=lambda option: option.price_delta)
    status = "ok" if options else "no_option_found"
    notes = (
        []
        if options
        else [
            "No substitution or removal in the catalog reduces cost while keeping the "
            "preserved categories and remaining valid against hard constraints."
        ]
    )
    return TradeoffResult(status=status, preserved_categories=sorted(preserve), options=options, notes=notes)
