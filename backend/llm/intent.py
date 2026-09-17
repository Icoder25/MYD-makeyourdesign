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

import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .prompts import INTENT_EXTRACTION_PROMPT, SYSTEM_PROMPT

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
        return (
            not self.add_categories
            and not self.remove_categories
            and self.budget_change == "none"
            and self.new_budget is None
            and self.priority_shift == "none"
            and not self.preferred_styles
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

    intent = ModificationIntent(
        add_categories=add,
        remove_categories=remove,
        budget_change=budget_change,
        new_budget=new_budget,
        priority_shift=priority,
        preferred_styles=styles,
        summary=_summarise(add, remove, budget_change, new_budget, priority, styles),
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
            response_schema=ModificationIntent,
            temperature=0.0,
        ),
    )

    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, ModificationIntent):
        return parsed.sanitised()
    if parsed is not None:
        return ModificationIntent.model_validate(parsed).sanitised()

    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Gemini returned no structured intent")
    return ModificationIntent.model_validate(json.loads(text)).sanitised()
