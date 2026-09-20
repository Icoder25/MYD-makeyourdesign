"""Planning API routes.

The endpoint set is small and task-shaped rather than resource-shaped: a user
creates a plan, resolves a conflict, or modifies a plan. Those are the three
things this product does.
"""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from backend.catalog import CatalogError, get_catalog
from backend.catalog.loader import KNOWN_CATEGORIES
from backend.designpulse.impact_engine import (
    DesignModification,
    ImpactReport,
    TradeoffOption,
    apply_tradeoff,
    impact_engine,
)
from backend.designpulse.models import (
    DecisionRecord,
    DesignState,
    DesignStateDiff,
    compute_design_state_diff,
    create_design_state_from_candidate,
)
from backend.export.generator import export_generator
from backend.inspiration.engine import inspiration_engine
from backend.llm.intent import interpret_modification_intent
from backend.settings import get_settings

from ..services.planner import create_plan
from ..services.store import store
from .schemas import (
    BathroomBrief,
    CatalogResponse,
    ExportPackageResponse,
    HealthResponse,
    ImpactRequest,
    InspirationApplyResponse,
    InspirationPresetsResponse,
    InspirationRequest,
    ModifyRequest,
    ModifyResponse,
    PlanResponse,
    ProjectHistoryResponse,
    ResolveRequest,
    TradeoffApplyRequest,
    TradeoffApplyResponse,
    VersionSummary,
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

    @router.get("/plan/{project_id}/state", response_model=DesignState)
    def get_design_state(
        project_id: str,
        version_id: str | None = Query(default=None),
    ) -> DesignState:
        state = store.get_design_state(project_id, version_id=version_id)
        if state is None:
            raise HTTPException(
                status_code=404,
                detail=f"No design state found for project '{project_id}'.",
            )
        return state

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

    @router.post("/plan/{project_id}/modify", response_model=ModifyResponse)
    async def modify(project_id: str, request: ModifyRequest) -> ModifyResponse:
        """Change a plan in plain language.

        The message is translated into a structured request, applied
        deterministically, and the plan is recomputed by the same engines. The
        language model never decides the outcome, so an impossible request comes
        back as a conflict with options rather than an invented success.
        """
        existing = store.get(project_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Unknown project id")

        from backend.llm.agent import modify_plan

        result = await modify_plan(request.message, existing)
        store.save(result.plan)
        return result

    # --- DesignPulse Endpoints ------------------------------------------------

    @router.post("/plan/{project_id}/impact", response_model=ImpactReport)
    async def impact(project_id: str, request: ImpactRequest) -> ImpactReport:
        """Run DesignPulse change impact analysis against the active DesignState.

        Deterministically traverses dependencies, evaluates spatial and budget constraints,
        and generates explainable trade-offs.
        IMPORTANT: This endpoint does NOT mutate the active design.
        """
        existing_plan = store.get(project_id)
        history = store.get_history(project_id)
        if existing_plan is None and history is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

        active_state = store.get_design_state(project_id)
        if active_state is None:
            raise HTTPException(
                status_code=404,
                detail=f"No active design state found for project '{project_id}'.",
            )

        # Interpret or construct structured DesignModification
        if request.message and (not request.category or not request.target_dimension):
            mod, _ = await interpret_modification_intent(request.message, active_state)
            if request.category:
                mod = mod.model_copy(update={"category": request.category})
            if request.target_dimension:
                mod = mod.model_copy(update={"target_dimension": request.target_dimension})
            if request.target_product_id:
                mod = mod.model_copy(update={"target_product_id": request.target_product_id})
        elif request.category:
            mod = DesignModification(
                category=request.category,
                action=request.action,
                target_product_id=request.target_product_id,
                target_dimension=request.target_dimension,
                natural_language_request=request.message,
            )
        else:
            raise HTTPException(
                status_code=422,
                detail="Invalid modification: either category or natural-language message must be provided.",
            )

        if mod.category not in KNOWN_CATEGORIES:
            raise HTTPException(
                status_code=422,
                detail=f"Category '{mod.category}' is not recognized.",
            )

        # The impact engine reasons about swapping or resizing something the
        # design already contains: it diffs an old product against a new one.
        # Adding or dropping a whole fixture changes what the room has to hold
        # and is a re-plan, not a diff — /modify does that properly. Saying so
        # here beats letting the engine raise "not present in current design
        # state" at someone who was explicitly trying to add it.
        if mod.action in ("add_category", "remove_category"):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"DesignPulse analyses changes to fixtures already in the design; "
                    f"it cannot {mod.action.replace('_', ' ')} '{mod.category}'. "
                    f"Use the conversational modify endpoint to add or remove a fixture — "
                    f"that recomputes the whole plan against the amended brief."
                ),
            )

        if mod.action in ("replace_product", "change_dimension"):
            curr_p = active_state.get_product(mod.category)
            if curr_p is None:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Category '{mod.category}' is not present in the active design, "
                        f"so there is nothing to change. Add it with the modify endpoint first."
                    ),
                )

        if mod.target_product_id:
            catalog_map = {p.id: p for p in get_catalog()}
            if mod.target_product_id not in catalog_map:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product '{mod.target_product_id}' not found in catalog.",
                )

        try:
            report = impact_engine.compute_impact(active_state, mod)
        except Exception as exc:
            raise HTTPException(
                status_code=422, detail=f"Impact computation error: {exc}"
            ) from exc

        # Cache report for subsequent tradeoff application
        store.set_last_impact(project_id, report)

        # Pure inspection: V1 is not mutated
        return report

    @router.post("/plan/{project_id}/tradeoff", response_model=TradeoffApplyResponse)
    def tradeoff(project_id: str, request: TradeoffApplyRequest) -> TradeoffApplyResponse:
        """Apply a selected valid TradeoffOption.

        Behavior:
        1. Retrieve active DesignState.
        2. Validate the selected trade-off.
        3. Construct V2 using the Phase 2 engine.
        4. Preserve V1.
        5. Save V2 into VersionHistory.
        6. Make V2 active.
        7. Return V2 + diff from V1.
        """
        existing_plan = store.get(project_id)
        history = store.get_history(project_id)
        if existing_plan is None and history is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

        active_state = store.get_design_state(project_id)
        if active_state is None:
            raise HTTPException(
                status_code=404,
                detail=f"No active design state found for project '{project_id}'.",
            )

        # Resolve TradeoffOption
        selected: TradeoffOption | None = None
        if request.tradeoff and request.tradeoff.id == request.tradeoff_id:
            selected = request.tradeoff
        else:
            last_impact = store.get_last_impact(project_id)
            if last_impact and last_impact.candidate_tradeoffs:
                for opt in last_impact.candidate_tradeoffs:
                    if opt.id == request.tradeoff_id:
                        selected = opt
                        break

        if selected is None:
            raise HTTPException(
                status_code=404,
                detail=f"Trade-off '{request.tradeoff_id}' not found or has expired.",
            )

        # Validate trade-off feasibility
        if not selected.resulting_is_feasible:
            raise HTTPException(
                status_code=422,
                detail="Selected trade-off is marked infeasible and cannot be applied.",
            )

        # Validate products in trade-off substitutions
        catalog_map = {p.id: p for p in get_catalog()}
        for sub in selected.substitutions:
            add_id = sub.get("add_id")
            if add_id and add_id not in catalog_map:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product '{add_id}' specified in trade-off not found in catalog.",
                )

        # Construct V2
        next_v_id = history.next_version_id() if history else f"v{active_state.version_number + 1}"
        try:
            v2_state = apply_tradeoff(
                current_state=active_state,
                tradeoff=selected,
                new_version_id=next_v_id,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=422, detail=f"Trade-off application error: {exc}"
            ) from exc

        if not v2_state.layout.solved:
            raise HTTPException(
                status_code=422,
                detail="Layout solver failed to place fixtures in room for this trade-off.",
            )

        # Preserve V1 in history and save V2 as active
        store.save_design_state(v2_state, set_active=True)

        diff = compute_design_state_diff(active_state, v2_state)

        return TradeoffApplyResponse(
            project_id=project_id,
            version_id=v2_state.version_id,
            version_number=v2_state.version_number,
            v2=v2_state,
            diff=diff,
        )

    @router.get("/plan/{project_id}/history", response_model=ProjectHistoryResponse)
    def history(project_id: str) -> ProjectHistoryResponse:
        """Return version timeline: available versions, active version, parent relationships, timestamps."""
        vhistory = store.get_history(project_id)
        if not vhistory or not vhistory.versions:
            plan = store.get(project_id)
            if not plan:
                raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
            store.get_design_state(project_id)
            vhistory = store.get_history(project_id)

        if not vhistory or not vhistory.versions:
            raise HTTPException(
                status_code=404,
                detail=f"No version history found for project '{project_id}'.",
            )

        summaries = [
            VersionSummary(
                version_id=v.version_id,
                version_number=v.version_number,
                parent_version_id=v.parent_version_id,
                timestamp=v.created_at,
                total_price=v.total_price,
                currency=v.currency,
                is_active=(v.version_id == vhistory.active_version_id),
                metadata=v.metadata,
            )
            for v in sorted(vhistory.versions.values(), key=lambda s: s.version_number)
        ]

        return ProjectHistoryResponse(
            project_id=project_id,
            active_version_id=vhistory.active_version_id
            or (summaries[-1].version_id if summaries else "v1"),
            versions=summaries,
        )

    @router.get("/plan/{project_id}/diff", response_model=DesignStateDiff)
    def diff(
        project_id: str,
        from_version: str = "v1",
        to_version: str = "v2",
    ) -> DesignStateDiff:
        """Compare two versions using the DesignState diff implementation."""
        vhistory = store.get_history(project_id)
        if not vhistory:
            plan = store.get(project_id)
            if not plan:
                raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
            store.get_design_state(project_id)
            vhistory = store.get_history(project_id)

        if not vhistory:
            raise HTTPException(
                status_code=404,
                detail=f"No version history found for project '{project_id}'.",
            )

        v1_key = f"v{from_version}" if from_version.isdigit() else from_version
        v2_key = f"v{to_version}" if to_version.isdigit() else to_version

        v1 = vhistory.get_version(v1_key)
        if v1 is None:
            raise HTTPException(
                status_code=404,
                detail=f"Version '{from_version}' not found in project history.",
            )

        v2 = vhistory.get_version(v2_key)
        if v2 is None:
            raise HTTPException(
                status_code=404,
                detail=f"Version '{to_version}' not found in project history.",
            )

        return compute_design_state_diff(v1, v2)

    # --- Phase 5: Inspiration & Professional Export Endpoints -----------------

    @router.get("/inspiration/presets", response_model=InspirationPresetsResponse)
    def get_inspiration_presets() -> InspirationPresetsResponse:
        """Returns all curated KOHLER architectural style directions."""
        return InspirationPresetsResponse(presets=inspiration_engine.list_presets())

    @router.post("/plan/{project_id}/inspiration", response_model=InspirationApplyResponse)
    def apply_inspiration(
        project_id: str,
        request: InspirationRequest,
    ) -> InspirationApplyResponse:
        """Applies an inspiration preset to a project's brief and generates a revalidated plan & DesignState.

        CRITICAL: Feeds DesignState through the brief without bypassing physical constraints or catalog facts.
        """
        existing_plan = store.get(project_id)
        if not existing_plan:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

        # Determine target preset
        if request.preset_id:
            preset = inspiration_engine.get_preset(request.preset_id)
            if not preset:
                raise HTTPException(status_code=404, detail=f"Preset '{request.preset_id}' not found.")
        elif request.query:
            preset = inspiration_engine.match_preset(request.query)
        else:
            raise HTTPException(status_code=400, detail="Must provide either preset_id or query.")

        # Apply preset to brief
        new_brief = inspiration_engine.apply_preset_to_brief(existing_plan.brief, preset)

        # Generate re-evaluated plan with deterministic ranking
        plan_response = create_plan(new_brief, project_id=project_id)
        store.save(plan_response)

        # Construct or advance DesignState
        history = store.get_history(project_id)
        v1_state = store.get_design_state(project_id)
        next_ver_num = (len(history.versions) + 1) if (history and history.versions) else 1
        ver_id = f"v{next_ver_num}"

        if plan_response.candidates:
            new_state = create_design_state_from_candidate(
                candidate=plan_response.candidates[0],
                brief=new_brief,
                project_id=project_id,
                version_id=ver_id,
                version_number=next_ver_num,
                parent_version_id=v1_state.version_id if v1_state else None,
            )
            # Add decision record documenting the aesthetic alignment
            new_state.decision_records.append(
                DecisionRecord(
                    decision_id=f"dec_{ver_id}",
                    timestamp=new_state.created_at,
                    category="aesthetic",
                    action="designer_change",
                    rationale=f"Applied KOHLER Inspiration: {preset.title}. {preset.tagline}",
                    client_requirement_ref=f"keywords: {', '.join(preset.style_keywords)}",
                )
            )
            store.save_design_state(new_state, set_active=True)
            active_state = new_state
        else:
            if v1_state:
                active_state = v1_state
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No compliant configuration found for this style direction.",
                )

        return InspirationApplyResponse(
            project_id=project_id,
            preset=preset,
            applied_styles=new_brief.preferred_styles,
            plan=plan_response,
            state=active_state,
        )

    @router.get("/plan/{project_id}/export", response_model=ExportPackageResponse)
    def get_export_package(
        project_id: str,
        role: Literal["client", "designer", "dealer"] = Query(default="client"),
        version_id: str | None = Query(default=None),
    ) -> ExportPackageResponse:
        """Retrieves structured export data for Client, Designer, or Dealer BOM from validated DesignState."""
        state = store.get_design_state(project_id, version_id=version_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"No DesignState found for project '{project_id}'.")

        if role == "client":
            data = export_generator.generate_client_package(state).model_dump()
        elif role == "designer":
            data = export_generator.generate_designer_spec(state).model_dump()
        else:
            data = export_generator.generate_dealer_bom(state).model_dump()

        return ExportPackageResponse(
            role=role,
            project_id=project_id,
            version_id=state.version_id,
            data=data,
        )

    @router.get("/plan/{project_id}/export/document", response_class=HTMLResponse)
    def get_export_document(
        project_id: str,
        role: Literal["client", "designer", "dealer"] = Query(default="client"),
        version_id: str | None = Query(default=None),
    ) -> HTMLResponse:
        """Returns standalone printable HTML architectural package for the validated DesignState."""
        state = store.get_design_state(project_id, version_id=version_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"No DesignState found for project '{project_id}'.")

        html_content = export_generator.generate_printable_html(state, role=role)
        return HTMLResponse(content=html_content)

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
