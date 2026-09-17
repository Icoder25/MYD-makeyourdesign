from fastapi import FastAPI

from .vision.analyzer import BathroomVisionAnalyzer
from .vision.api import create_vision_router
from .vision.provider import GeminiVisionProvider


def create_app() -> FastAPI:
    app = FastAPI(title="KOHLER AI BathPlan")
    analyzer = BathroomVisionAnalyzer(GeminiVisionProvider())
    app.include_router(create_vision_router(analyzer))
    return app


app = create_app()
