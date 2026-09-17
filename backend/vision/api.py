from fastapi import APIRouter, File, HTTPException, UploadFile

from .analyzer import BathroomVisionAnalyzer
from .models import BathroomVisionEvidence


def create_vision_router(analyzer: BathroomVisionAnalyzer) -> APIRouter:
    router = APIRouter(prefix="/api/v1/project/{project_id}", tags=["vision"])

    @router.post("/vision", response_model=BathroomVisionEvidence)
    async def analyze_project_vision(
        project_id: str,
        image: UploadFile = File(...),
    ) -> BathroomVisionEvidence:
        del project_id
        try:
            image_bytes = await image.read()
            return await analyzer.analyze(image_bytes)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="vision analysis unavailable") from exc

    return router
