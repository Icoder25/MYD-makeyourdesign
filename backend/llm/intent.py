"""Turning a sentence into a structured modification request.

Two implementations of the same contract:

- `extract_intent_llm` — asks Gemini for structured JSON.
- `extract_intent_keywords` — deterministic keyword matching.

The keyword version is not a stub. It handles every phrasing in the demo script
and a good deal more, so the product's conversational modification works with no
API key at all. The LLM version handles the phrasings nobody anticipated.

Whichever produces the intent, the intent is then applied *deterministically* and
the plan is recomputed by the same engines. The model's output is a request, not
a result — it cannot make something feasible by asserting it.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.catalog import get_catalog
from backend.designpulse.impact_engine import DesignModification
if TYPE_CHECKING:
    from backend.designpulse.models import DesignState

from .prompts import INTENT_EXTRACTION_PROMPT, SYSTEM_PROMPT
from .schema import gemini_response_schema

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "vanity",
    "basin",
    "faucet",
    "toilet",
    "smart_toilet",
    "shower",
    "smart_shower",
    "bathtub",
    "storage",
}

PriorityShift = Literal[
    "cheaper", "premium", "water_efficiency", "smart_features", "storage", "none"
]


class ModificationIntent(BaseModel):
    """What the user asked for, before anyone checks whether it is possible."""

    model_config = ConfigDict(extra="forbid")

    add_categories: list[str] = Field(default_factory=list)
    remove_categories: list[str] = Field(default_factory=list)
    budget_change: Literal["keep", "increase", "decrease", "none"] = "none"
    new_budget: float | None = None
    priority_shift: PriorityShift = "none"
    preferred_styles: list[str] = Field(default_factory=list)
    question: str | None = None
    summary: str = ""

    # Dimensional modification intent extensions
    target_category: str | None = None
    target_dimension: dict[str, float] | None = None
    target_product_id: str | None = None
    action: Literal["replace_product", "change_dimension", "add_category", "remove_category", "none"] = "none"

    def to_design_modification(
        self, current_state: DesignState | None = None
    ) -> DesignModification | None:
        """Convert structured intent into a DesignPulse DesignModification."""
        cat = self.target_category or (self.add_categories[0] if self.add_categories else None)
        if not cat:
            return None
        act = self.action if self.action != "none" else ("change_dimension" if self.target_dimension else "replace_product")
        return DesignModification(
            category=cat,
            action=act,
            target_product_id=self.target_product_id,
            target_dimension=self.target_dimension,
            natural_language_request=self.summary or None,
        )

    def sanitised(self) -> "ModificationIntent":
        """Drop anything outside the known vocabulary.

        A language model that invents a category name must not be able to inject
        it into the planning pipeline.
        """
        return self.model_copy(
            update={
                "add_categories": [c for c in self.add_categories if c in VALID_CATEGORIES],
                "remove_categories": [c for c in self.remove_categories if c in VALID_CATEGORIES],
            }
        )

    def is_empty(self) -> bool:
        """True when nothing actionable was expressed.

        The dimensional fields count. They were added after this check and
        omitting them meant a perfectly good "make the vanity wider" was
        classified as empty and thrown away in favour of the keyword parser.
        """
        return (
            not self.add_categories
            and not self.remove_categories
            and self.budget_change == "none"
            and self.new_budget is None
            and self.priority_shift == "none"
            and not self.preferred_styles
            and self.target_category is None
            and self.target_dimension is None
            and self.target_product_id is None
            and self.action == "none"
        )


# --- Deterministic fallback ---------------------------------------------------

_CATEGORY_PATTERNS: list[tuple[str, str]] = [
    (r"\b(smart|digital|connected)\s+shower", "smart_shower"),
    (r"\b(smart|intelligent|bidet)\s+toilet", "smart_toilet"),
    (r"\bbidet\b", "smart_toilet"),
    (r"\bbath\s*tub\b|\bbathtub\b|\btub\b", "bathtub"),
    (r"\bshower\b", "shower"),
    (r"\btoilet\b|\bwc\b|\bcommode\b", "toilet"),
    (r"\bvanity\b", "vanity"),
    (r"\bbasin\b|\bsink\b|\blavatory\b", "basin"),
    (r"\bfaucet\b|\btap\b|\bmixer\b", "faucet"),
    (r"\bstorage\b|\bcabinet\b|\bmirror\b", "storage"),
]

_ADD_VERBS = (
    r"\b(add|include|want|need|put in|fit|give me|with a|also|like|prefer|swap in|upgrade to)\b"
)
_REMOVE_VERBS = r"\b(remove|drop|without|delete|take out|get rid of|skip|lose the)\b"

_STYLE_WORDS = {
    "modern": "modern",
    "minimalist": "minimalist",
    "minimal": "minimalist",
    "contemporary": "contemporary",
    "traditional": "traditional",
    "transitional": "transitional",
    "luxury": "luxury",
    "luxurious": "luxury",
}


def _categories_in(text: str) -> list[str]:
    found: list[str] = []
    consumed = text
    for pattern, category in _CATEGORY_PATTERNS:
        if re.search(pattern, consumed):
            if category not in found:
                found.append(category)
            # Remove the matched text so "smart shower" does not also match "shower".
            consumed = re.sub(pattern, " ", consumed)
    return found


def _parse_amount(text: str) -> float | None:
    """Read an Indian-format budget figure: '2.5 lakh', 'Rs 300000', '3L'."""
    lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|l\b)", text)
    if lakh:
        return float(lakh.group(1)) * 100_000
    crore = re.search(r"(\d+(?:\.\d+)?)\s*crore", text)
    if crore:
        return float(crore.group(1)) * 10_000_000
    plain = re.search(r"(?:rs\.?|inr|₹)\s*([\d,]{4,})", text)
    if plain:
        return float(plain.group(1).replace(",", ""))
    bare = re.search(r"\b(\d{5,})\b", text)
    if bare:
        return float(bare.group(1))
    return None


def extract_intent_keywords(message: str) -> ModificationIntent:
    """Deterministic intent extraction. No network, no model, no API key."""
    text = message.lower().strip()

    is_question = text.startswith(("why", "what", "how", "which", "can you explain", "explain")) or (
        "?" in text and not re.search(_ADD_VERBS, text) and not re.search(_REMOVE_VERBS, text)
    )
    if is_question:
        return ModificationIntent(
            question=message.strip(),
            summary="Answer a question about the current plan without changing it.",
        )

    add: list[str] = []
    remove: list[str] = []

    # A clause like "a bathtub too" carries no verb of its own; it inherits the
    # action from the sentence around it ("I want a smart toilet AND a bathtub
    # too"). Only inherit when the sentence is unambiguous about which it is.
    sentence_adds = bool(re.search(_ADD_VERBS, text))
    sentence_removes = bool(re.search(_REMOVE_VERBS, text))
    if sentence_adds and not sentence_removes:
        default_action: str | None = "add"
    elif sentence_removes and not sentence_adds:
        default_action = "remove"
    else:
        default_action = None

    # Split on clause boundaries so "add X but remove Y" is read correctly.
    for clause in re.split(r",|\band\b|\bbut\b|\bwhile\b|\bthough\b|\.", text):
        clause = clause.strip()
        if not clause:
            continue
        categories = _categories_in(clause)
        if not categories:
            continue
        if re.search(_REMOVE_VERBS, clause):
            action = "remove"
        elif re.search(_ADD_VERBS, clause):
            action = "add"
        else:
            action = default_action
        if action == "remove":
            remove.extend(c for c in categories if c not in remove)
        elif action == "add":
            add.extend(c for c in categories if c not in add)

    budget_change: Literal["keep", "increase", "decrease", "none"] = "none"
    new_budget = _parse_amount(text)

    if re.search(r"\bkeep\b.{0,20}\bbudget\b|\bsame budget\b|\bwithin (my|the) budget\b|\bstay under\b|\bwithout (increasing|raising)\b", text):
        budget_change = "keep"
    elif re.search(r"\b(increase|raise|more|bigger|extend|stretch|up)\b.{0,20}\bbudget\b|\bbudget\b.{0,20}\b(increase|up to)\b", text):
        budget_change = "increase"
    elif re.search(r"\b(reduce|lower|cut|decrease|shrink)\b.{0,20}\bbudget\b", text):
        budget_change = "decrease"
    elif new_budget is not None and re.search(r"\bbudget\b|\brs\b|\binr\b|₹|\blakh\b", text):
        budget_change = "increase"

    priority: PriorityShift = "none"
    if re.search(r"\bcheap|\bcheaper\b|\bless expensive\b|\baffordab|\bsave money\b|\bbudget[- ]friendly\b", text):
        priority = "cheaper"
    elif re.search(r"\bpremium\b|\bupgrade\b|\bnicer\b|\bhigh[- ]end\b|\bluxur|\bbetter quality\b", text):
        priority = "premium"
    elif re.search(r"\bwater\b|\beco\b|\bsustainab|\befficien|\bconserv|\bgreen\b", text):
        priority = "water_efficiency"
    elif re.search(r"\bsmart\b|\bconnected\b|\bapp\b|\bautomat", text):
        priority = "smart_features"
    elif re.search(r"\bstorage\b|\bspace to store\b|\bshelv|\bdrawer", text):
        priority = "storage"

    styles = []
    for word, style in _STYLE_WORDS.items():
        if re.search(rf"\b{word}\b", text) and style not in styles:
            styles.append(style)

    # Dimensional intent detection
    detected_cats = _categories_in(text)
    target_category = detected_cats[0] if detected_cats else ("vanity" if "vanity" in text else None)
    target_dimension: dict[str, float] | None = None
    target_action: Literal["replace_product", "change_dimension", "add_category", "remove_category", "none"] = "none"

    dim_match = re.search(r"(?:to\s+|by\s+|is\s+|size\s+)?(\d+(?:\.\d+)?)\s*(?:inches|inch|in\b|\"|-inch)", text)
    if not dim_match:
        dim_match = re.search(r"\b(?:vanity|shower|basin|toilet)\s+(?:to\s+)?(\d{2})\b", text)

    if dim_match and target_category:
        target_dimension = {"width_in": float(dim_match.group(1))}
        target_action = "change_dimension"
    elif target_category and re.search(r"\b(larger|bigger|wider|increase|expand|more space)\b", text):
        target_action = "change_dimension"
        target_dimension = {"width_in": 60.0}
    elif target_category and re.search(r"\b(smaller|compact|narrower|decrease|shrink|downsize)\b", text):
        target_action = "change_dimension"
        target_dimension = {"width_in": 36.0}

    summary_text = _summarise(add, remove, budget_change, new_budget, priority, styles)
    if target_dimension and target_category and "No actionable change" in summary_text:
        summary_text = f"Understood as: change {target_category} to {target_dimension.get('width_in'):.0f} inches."

    intent = ModificationIntent(
        add_categories=add,
        remove_categories=remove,
        budget_change=budget_change,
        new_budget=new_budget,
        priority_shift=priority,
        preferred_styles=styles,
        summary=summary_text,
        target_category=target_category,
        target_dimension=target_dimension,
        action=target_action,
    )
    return intent.sanitised()


def _summarise(
    add: list[str],
    remove: list[str],
    budget_change: str,
    new_budget: float | None,
    priority: str,
    styles: list[str],
) -> str:
    parts: list[str] = []
    if add:
        parts.append(f"add {', '.join(c.replace('_', ' ') for c in add)}")
    if remove:
        parts.append(f"remove {', '.join(c.replace('_', ' ') for c in remove)}")
    if budget_change == "keep":
        parts.append("keep the current budget")
    elif budget_change == "increase":
        parts.append(f"raise the budget to {new_budget:,.0f}" if new_budget else "raise the budget")
    elif budget_change == "decrease":
        parts.append("reduce the budget")
    if priority != "none":
        parts.append(f"prioritise {priority.replace('_', ' ')}")
    if styles:
        parts.append(f"favour {', '.join(styles)} styling")
    if not parts:
        return "No actionable change was recognised in the request."
    return "Understood as: " + "; ".join(parts) + "."


# --- LLM implementation -------------------------------------------------------


class LLMIntentPayload(BaseModel):
    """The wire shape asked of the model.

    Flat on purpose. `ModificationIntent.target_dimension` is a mapping, which
    Gemini's schema dialect cannot express, so the one dimension the model is
    ever asked for gets its own scalar field and is reassembled on arrival.
    """

    add_categories: list[str] = Field(default_factory=list)
    remove_categories: list[str] = Field(default_factory=list)
    budget_change: Literal["keep", "increase", "decrease", "none"] = "none"
    new_budget: float | None = None
    priority_shift: PriorityShift = "none"
    preferred_styles: list[str] = Field(default_factory=list)
    question: str | None = None
    summary: str = ""
    target_category: str | None = None
    target_dimension_width_in: float | None = None
    target_product_id: str | None = None
    action: Literal[
        "replace_product", "change_dimension", "add_category", "remove_category", "none"
    ] = "none"

    def to_intent(self) -> ModificationIntent:
        return ModificationIntent(
            add_categories=self.add_categories,
            remove_categories=self.remove_categories,
            budget_change=self.budget_change,
            new_budget=self.new_budget,
            priority_shift=self.priority_shift,
            preferred_styles=self.preferred_styles,
            question=self.question,
            summary=self.summary,
            target_category=self.target_category,
            target_dimension=(
                {"width_in": self.target_dimension_width_in}
                if self.target_dimension_width_in is not None
                else None
            ),
            target_product_id=self.target_product_id,
            action=self.action,
        )


async def extract_intent_llm(message: str, context: str, api_key: str, model: str) -> ModificationIntent:
    """Ask Gemini for a structured intent. Raises on any failure; caller falls back."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = await client.aio.models.generate_content(
        model=model,
        contents=INTENT_EXTRACTION_PROMPT.format(context=context, message=message),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=gemini_response_schema(LLMIntentPayload),
            temperature=0.0,
        ),
    )

    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Gemini returned no structured intent")
    return LLMIntentPayload.model_validate(json.loads(text)).to_intent().sanitised()


# --- DesignPulse Modification Intent Extraction --------------------------------


def extract_modification_intent_keywords(
    message: str,
    current_state: DesignState | None = None,
) -> DesignModification:
    """Deterministic conversion of natural language into a structured DesignModification.

    Handles phrasings such as:
      - 'Increase the vanity to 60 inches.'
      - 'Make the vanity 60 inches.'
      - 'Client wants a larger vanity.'
      - 'Vanity 60 inch.'
    without calling an LLM or external service. All calculations and catalog lookups
    are deterministic.
    """
    text = message.lower().strip()

    # 1. Identify category
    categories = _categories_in(text)
    if categories:
        category = categories[0]
    elif "vanity" in text or "counter" in text:
        category = "vanity"
    elif "shower" in text:
        category = "shower"
    elif "toilet" in text or "commode" in text:
        category = "toilet"
    elif "basin" in text or "sink" in text:
        category = "basin"
    elif "faucet" in text or "tap" in text:
        category = "faucet"
    elif "tub" in text:
        category = "bathtub"
    else:
        category = "vanity"

    action: Literal["replace_product", "change_dimension", "add_category", "remove_category"] = (
        "change_dimension"
    )
    target_dimension: dict[str, float] | None = None
    target_product_id: str | None = None

    # 2. Check for explicit numeric dimension (e.g., 60 inches, 60", 60-inch, to 60)
    dim_match = re.search(r"(?:to\s+|by\s+|is\s+|size\s+)?(\d+(?:\.\d+)?)\s*(?:inches|inch|in\b|\"|-inch)", text)
    if not dim_match:
        dim_match = re.search(r"\b(?:vanity|shower|basin|toilet)\s+(?:to\s+)?(\d{2})\b", text)

    catalog = list(get_catalog())
    cat_products = [p for p in catalog if p.category == category]
    cat_products_with_width = [p for p in cat_products if p.dimensions and p.dimensions.width_in]
    cat_products_with_width.sort(key=lambda p: p.dimensions.width_in or 0)

    current_prod = current_state.get_product(category) if current_state else None
    current_width = current_prod.dimensions.width_in if (current_prod and current_prod.dimensions) else None

    if dim_match:
        width_val = float(dim_match.group(1))
        target_dimension = {"width_in": width_val}
        action = "change_dimension"
    elif re.search(r"\b(larger|bigger|wider|increase|expand|more space|upgrade)\b", text):
        action = "change_dimension"
        if current_width and cat_products_with_width:
            larger_options = [p for p in cat_products_with_width if (p.dimensions.width_in or 0) > current_width]
            if larger_options:
                target_dimension = {"width_in": float(larger_options[0].dimensions.width_in or 0)}
            else:
                target_dimension = {"width_in": float(cat_products_with_width[-1].dimensions.width_in or 0)}
        else:
            target_dimension = {"width_in": 60.0}
    elif re.search(r"\b(smaller|compact|narrower|decrease|shrink|downsize)\b", text):
        action = "change_dimension"
        if current_width and cat_products_with_width:
            smaller_options = [p for p in cat_products_with_width if (p.dimensions.width_in or 0) < current_width]
            if smaller_options:
                target_dimension = {"width_in": float(smaller_options[-1].dimensions.width_in or 0)}
            else:
                target_dimension = {"width_in": float(cat_products_with_width[0].dimensions.width_in or 0)}
        else:
            target_dimension = {"width_in": 36.0}
    elif re.search(_REMOVE_VERBS, text):
        action = "remove_category"
    elif re.search(_ADD_VERBS, text) and (not current_prod):
        action = "add_category"

    # Check for direct product mention or ID
    for p in catalog:
        if p.id in text or (p.category == category and p.name.lower() in text):
            target_product_id = p.id
            action = "replace_product"
            break

    return DesignModification(
        category=category,
        action=action,
        target_product_id=target_product_id,
        target_dimension=target_dimension,
        natural_language_request=message,
    )


class LLMModificationIntent(BaseModel):
    category: str
    action: Literal["replace_product", "change_dimension", "add_category", "remove_category"] = "change_dimension"
    dimension_width_in: float | None = None
    target_product_id: str | None = None
    relative_direction: Literal["larger", "smaller", "none"] = "none"


MODIFICATION_EXTRACTION_PROMPT = """You are an assistant for KOHLER AI BathPlan DesignPulse.
Convert the user's design modification request into structured JSON.
Current bathroom context:
{context}

User request: "{message}"

Respond strictly with a JSON object matching this schema:
{{
    "category": "<vanity|toilet|smart_toilet|shower|smart_shower|basin|faucet|bathtub|storage>",
    "action": "<replace_product|change_dimension|add_category|remove_category>",
    "dimension_width_in": <number or null>,
    "target_product_id": "<product_id or null>",
    "relative_direction": "<larger|smaller|none>"
}}
CRITICAL: Do NOT invent or calculate prices, clearances, or rules. Only extract what the user requested.
"""


async def extract_modification_intent_llm(
    message: str,
    context: str,
    api_key: str,
    model: str,
    current_state: DesignState | None = None,
) -> DesignModification:
    """Ask Gemini to interpret the user's natural language request.

    The LLM extracts intent only; all dimensions, prices, and rules are resolved
    by deterministic engines.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = await client.aio.models.generate_content(
        model=model,
        contents=MODIFICATION_EXTRACTION_PROMPT.format(context=context, message=message),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=gemini_response_schema(LLMModificationIntent),
            temperature=0.0,
        ),
    )

    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Gemini returned no structured modification intent")
    parsed = LLMModificationIntent.model_validate(json.loads(text))

    cat = parsed.category if parsed.category in VALID_CATEGORIES else "vanity"
    target_dim: dict[str, float] | None = None

    if parsed.dimension_width_in is not None:
        target_dim = {"width_in": parsed.dimension_width_in}
    elif parsed.relative_direction == "larger":
        # Deterministically determine the next larger size from the catalog
        catalog = list(get_catalog())
        cat_products = [p for p in catalog if p.category == cat and p.dimensions and p.dimensions.width_in]
        cat_products.sort(key=lambda p: p.dimensions.width_in or 0)
        curr_prod = current_state.get_product(cat) if current_state else None
        curr_w = curr_prod.dimensions.width_in if (curr_prod and curr_prod.dimensions) else None
        if curr_w and cat_products:
            larger = [p for p in cat_products if (p.dimensions.width_in or 0) > curr_w]
            target_dim = {"width_in": float(larger[0].dimensions.width_in if larger else cat_products[-1].dimensions.width_in)}
        else:
            target_dim = {"width_in": 60.0}
    elif parsed.relative_direction == "smaller":
        target_dim = {"width_in": 36.0}

    return DesignModification(
        category=cat,
        action=parsed.action,
        target_product_id=parsed.target_product_id,
        target_dimension=target_dim,
        natural_language_request=message,
    )


async def interpret_modification_intent(
    message: str,
    current_state: DesignState | None = None,
) -> tuple[DesignModification, str]:
    """Get a structured DesignModification, preferring LLM interpretation if configured.

    Always falls back to deterministic keyword/regex extraction on failure, timeout,
    or missing API key.
    """
    from backend.settings import get_settings

    settings = get_settings()
    if settings.llm_available:
        try:
            ctx = f"Room has: {', '.join(p.name for p in current_state.selected_products)}" if current_state else "Bathroom plan in progress."
            mod = await asyncio.wait_for(
                extract_modification_intent_llm(
                    message=message,
                    context=ctx,
                    api_key=settings.gemini_api_key,
                    model=settings.llm_model,
                    current_state=current_state,
                ),
                timeout=8.0,
            )
            return mod, "llm"
        except Exception:
            # The deterministic parser below is genuinely capable, so the user
            # still gets an answer — but an operator needs to know the model
            # leg is down, otherwise "provider unreachable" is indistinguishable
            # from "nothing actionable was said".
            logger.warning(
                "LLM modification-intent extraction failed; using deterministic keywords",
                exc_info=True,
            )

    return extract_modification_intent_keywords(message, current_state), "deterministic_keywords"

