"""Pydantic models to Gemini response schemas.

Passing a Pydantic model straight to ``response_schema`` looks like it should
work, and the SDK accepts it, but the JSON Schema pydantic emits carries keys
the Gemini REST API rejects outright — ``additionalProperties`` (which
``extra="forbid"`` adds to every model), ``$defs``/``$ref`` indirection, and
``anyOf: [T, null]`` for optional fields. The request comes back 400
INVALID_ARGUMENT, the caller's ``except`` swallows it, and the product quietly
runs on its deterministic fallback forever while still reporting "AI active".

So the conversion happens here, explicitly, once: resolve the references,
translate nullable unions into the ``nullable`` flag Gemini understands, and
drop the vocabulary it does not know.

Free-form mappings (``dict[str, float]``) have no representation in this subset
at all. Rather than emit something the API will reject, they are rejected here,
at import time of the caller, so the incompatibility surfaces as a test failure
rather than a silent production fallback. Models sent to Gemini must be flat.
"""

from typing import Any

from pydantic import BaseModel

# Keys pydantic emits that the Gemini schema dialect does not accept.
_UNSUPPORTED_KEYS = frozenset(
    {
        "$schema",
        "additionalProperties",
        "default",
        "discriminator",
        "examples",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "patternProperties",
        "title",
    }
)


class UnsupportedSchemaError(TypeError):
    """The model cannot be expressed in Gemini's schema subset."""


def gemini_response_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Convert a Pydantic model into a schema Gemini's API will accept."""
    raw = model.model_json_schema()
    defs = raw.pop("$defs", {})
    converted = _convert(raw, defs, model.__name__)
    if converted.get("type") != "object" or not converted.get("properties"):
        raise UnsupportedSchemaError(
            f"{model.__name__} does not describe an object with properties"
        )
    return converted


def _convert(node: Any, defs: dict[str, Any], path: str) -> Any:
    if not isinstance(node, dict):
        return node

    if "$ref" in node:
        ref = node["$ref"].rsplit("/", 1)[-1]
        if ref not in defs:
            raise UnsupportedSchemaError(f"{path}: unresolvable reference {node['$ref']!r}")
        return _convert(defs[ref], defs, f"{path}.{ref}")

    if "anyOf" in node:
        return _convert_any_of(node, defs, path)

    result: dict[str, Any] = {}
    for key, value in node.items():
        if key in _UNSUPPORTED_KEYS:
            continue
        if key == "const":
            # Gemini expresses a fixed value as a one-entry enum, and only for
            # strings. A Literal[False] has no equivalent, so the type carries
            # through alone; the pinned value is re-applied after parsing
            # anyway, which is where it actually needs to be enforced.
            if isinstance(value, str):
                result["enum"] = [value]
            continue
        if key == "properties":
            result[key] = {
                name: _convert(sub, defs, f"{path}.{name}") for name, sub in value.items()
            }
        elif key == "items":
            result[key] = _convert(value, defs, f"{path}[]")
        else:
            result[key] = value

    if result.get("type") == "object" and "properties" not in result:
        raise UnsupportedSchemaError(
            f"{path}: free-form mappings have no Gemini equivalent; "
            "give the model explicit fields instead"
        )
    return result


def _convert_any_of(node: dict[str, Any], defs: dict[str, Any], path: str) -> dict[str, Any]:
    """Collapse ``T | None`` into ``T`` plus Gemini's ``nullable`` flag."""
    branches = [b for b in node["anyOf"] if b.get("type") != "null"]
    nullable = len(branches) != len(node["anyOf"])

    if len(branches) != 1:
        raise UnsupportedSchemaError(
            f"{path}: only optional (T | None) unions are supported, got {len(branches)} branches"
        )

    converted = _convert(branches[0], defs, path)
    if nullable:
        converted["nullable"] = True
    # A description written on the optional field itself outranks the branch's.
    if "description" in node:
        converted["description"] = node["description"]
    return converted
