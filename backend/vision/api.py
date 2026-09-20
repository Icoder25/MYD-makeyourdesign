import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.services.store import store
from .analyzer import BathroomVisionAnalyzer
from .mapping import attach_vision_to_design_state
from .models import BathroomVisionEvidence

logger = logging.getLogger(__name__)

# Provider conditions that clear on their own: quota windows, overload, timeouts.
_RETRIABLE_STATUS = frozenset({429, 500, 502, 503, 504})


def _is_retriable(exc: Exception) -> bool:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if isinstance(code, int) and code in _RETRIABLE_STATUS:
        return True
    return isinstance(exc, TimeoutError)



def create_vision_router(analyzer: BathroomVisionAnalyzer) -> APIRouter:
    router = APIRouter(prefix="/api/v1/project/{project_id}", tags=["vision"])

    @router.post("/vision", response_model=BathroomVisionEvidence)
    async def analyze_project_vision(
        project_id: str,
        image: UploadFile = File(...),
    ) -> BathroomVisionEvidence:
        try:
            image_bytes = await image.read()
            evidence = await analyzer.analyze(image_bytes)

            # Bind vision evidence into store
            store.set_vision_evidence(project_id, evidence)

            # If an active DesignState already exists for this project, attach vision analysis
            active_state = store.get_design_state(project_id)
            if active_state:
                updated_state = attach_vision_to_design_state(active_state, evidence)
                store.save_design_state(updated_state, set_active=True)

            return evidence
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            # GUARDRAIL 4: Clean, non-blocking failure message.
            #
            # A quota or overload response is worth separating out: it is
            # temporary and retrying works, whereas the generic message reads
            # as "this feature is broken" and sends the user off to do the
            # whole brief by hand for no reason.
            logger.warning("Vision analysis failed for project %s", project_id, exc_info=True)
            if _is_retriable(exc):
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "The image service is temporarily busy and could not read this photo. "
                        "Nothing was lost — wait a few seconds and upload again, or continue "
                        "entering the room details by hand."
                    ),
                ) from exc
            raise HTTPException(
                status_code=502,
                detail="Vision analysis unavailable. You can continue using manual project inputs.",
            ) from exc

    return router
