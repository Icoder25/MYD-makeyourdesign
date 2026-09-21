"""KOHLER AI BathPlan — application entry point.

The app starts and the full deterministic planner works with no API keys
configured. AI layers attach only when their key is present; their absence is a
normal operating condition, not a startup failure.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import create_planning_router
from .settings import get_settings
from .vision.analyzer import BathroomVisionAnalyzer
from .vision.api import create_vision_router
from .vision.provider import GeminiVisionProvider


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI BathPlan",
        description=(
            "Constraint-aware bathroom planning. Feasibility, dimensions, pricing and "
            "water calculations are deterministic; the language model explains results "
            "and interprets intent, and never decides them."
        ),
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(create_planning_router())

    analyzer = BathroomVisionAnalyzer(GeminiVisionProvider())
    app.include_router(create_vision_router(analyzer))

    return app


app = create_app()
