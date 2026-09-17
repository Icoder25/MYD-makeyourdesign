"""Vision prompt, re-exported from the shared prompt registry.

All prompts live in backend/llm/prompts.py so docs/prompts.md is generated
from a single source and cannot drift from what actually runs.
"""

from backend.llm.prompts import VISION_SYSTEM_PROMPT as SYSTEM_PROMPT

__all__ = ["SYSTEM_PROMPT"]
