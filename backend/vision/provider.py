import json
import os
from typing import Protocol

from ..llm.schema import gemini_response_schema
from .models import BathroomVisionEvidence
from .prompt import SYSTEM_PROMPT


# Gemini retires model ids. A dated id that 404s takes the whole vision leg
# down silently, so this tracks a currently-served stable release.
DEFAULT_VISION_MODEL = "gemini-2.5-flash"


class VisionProvider(Protocol):
    async def analyze(self, image_bytes: bytes) -> BathroomVisionEvidence:
        """Analyze already-normalized image bytes and return structured evidence."""


class GeminiVisionProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_VISION_MODEL", DEFAULT_VISION_MODEL)

    async def analyze(self, image_bytes: bytes) -> BathroomVisionEvidence:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini vision analysis")
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                "Analyze this bathroom image.",
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=gemini_response_schema(BathroomVisionEvidence),
            ),
        )

        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini returned no structured vision response")
        return BathroomVisionEvidence.model_validate(json.loads(text))
