"""Planning API routes.

The endpoint set is small and task-shaped rather than resource-shaped: a user
creates a plan, resolves a conflict, or modifies a plan. Those are the three
things this product does.
"""

from fastapi import APIRouter, HTTPException

from backend.catalog import CatalogError, get_catalog
from backend.settings import get_settings

from ..services.planner import create_plan
from ..services.store import store
from .schemas import (
    BathroomBrief,
    CatalogResponse,
    HealthResponse,
    PlanResponse,
    ResolveRequest,
)

DATA_DISCLAIMER = (
    "Prototype catalog. Prices are illustrative and are not KOHLER pricing; dimensions "
    "are class-typical where a specification sheet could not be verified. WaterSense "
    "eligibility is computed from recorded flow figures against the published threshold "
    "and is not a certification claim. See docs/verified-facts.md."
)


def create_planning_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["planning"])

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        settings = get_settings()
        try:
            catalog = get_catalog()
            loaded, size = True, len(catalog)
        except CatalogError:
            loaded, size = False, 0
        return HealthResponse(
            status="ok",
            catalog_loaded=loaded,
            catalog_size=size,
            vision_available=settings.vision_available,
            llm_available=settings.llm_available,
        )

    @router.get("/catalog", response_model=CatalogResponse)
    def catalog() -> CatalogResponse:
        try:
            products = list(get_catalog())
        except CatalogError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return CatalogResponse(
            count=len(products),
            categories=sorted({product.category for product in products}),
            products=products,
            data_disclaimer=DATA_DISCLAIMER,
        )

    @router.post("/plan", response_model=PlanResponse)
    def plan(brief: BathroomBrief) -> PlanResponse:
        try:
            result = create_plan(brief, store.new_id())
        except CatalogError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return store.save(result)

    @router.get("/plan/{project_id}", response_model=PlanResponse)
    def get_plan(project_id: str) -> PlanResponse:
        existing = store.get(project_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Unknown project id")
        return existing

    @router.post("/plan/{project_id}/resolve", response_model=PlanResponse)
    def resolve(project_id: str, request: ResolveRequest) -> PlanResponse:
        """Apply the user's chosen trade-off and recompute.

        The system never picks the relaxation itself. It presents what would have
        to give, the user decides which one, and the whole plan is recomputed from
        the amended brief — not patched, recomputed, so the result is exactly as
        trustworthy as a first-time plan.
        """
        existing = store.get(project_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Unknown project id")

        brief = _apply_relaxation(existing.brief, request)
        result = create_plan(brief, project_id)
        return store.save(result)

    return router


def _apply_relaxation(brief: BathroomBrief, request: ResolveRequest) -> BathroomBrief:
    """Amend the brief according to the user's choice. Deterministic, no LLM."""
    updates: dict[str, object] = {}

    if request.relaxation == "increase_budget":
        if request.budget is None:
            raise HTTPException(status_code=422, detail="increase_budget requires a budget value")
        if brief.budget is not None and request.budget < brief.budget:
            raise HTTPException(
                status_code=422,
                detail="increase_budget must not lower the budget; use a new plan instead",
            )
        updates["budget"] = request.budget

    elif request.relaxation == "drop_category":
        if not request.category:
            raise HTTPException(status_code=422, detail="drop_category requires a category")
        if request.category not in brief.required_categories:
            raise HTTPException(
                status_code=422,
                detail=f"'{request.category}' is not currently a required category",
            )
        updates["required_categories"] = [
            category for category in brief.required_categories if category != request.category
        ]

    elif request.relaxation == "allow_lower_tier":
        # Tier is a ranking preference, not a hard filter, so the deterministic
        # action is to shift weight toward budget fit and let scoring re-sort.
        updates["weights"] = brief.weights.model_copy(update={"budget": brief.weights.budget * 3})

    elif request.relaxation == "confirm_electrical":
        updates["electrical_available"] = True

    elif request.relaxation == "confirm_rough_in":
        if request.toilet_rough_in_in is None:
            raise HTTPException(
                status_code=422, detail="confirm_rough_in requires a measured rough-in value"
            )
        updates["toilet_rough_in_in"] = request.toilet_rough_in_in

    elif request.relaxation == "enlarge_room":
        if request.room_width_ft is None and request.room_length_ft is None:
            raise HTTPException(
                status_code=422, detail="enlarge_room requires a new width or length"
            )
        if request.room_width_ft is not None:
            updates["room_width_ft"] = request.room_width_ft
        if request.room_length_ft is not None:
            updates["room_length_ft"] = request.room_length_ft

    return brief.model_copy(update=updates)
