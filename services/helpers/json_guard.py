from typing import Any, Dict
import json
import re


def extract_json(text: str) -> str:
    # strip fences if any
    if text.strip().startswith("```"):
        parts = re.split(r"```(?:json)?", text, flags=re.IGNORECASE)
        if len(parts) >= 3:
            candidate = parts[1]
            candidate = candidate.split("```")[0]
            return candidate.strip()
    return text.strip()


def prune_to_schema(obj: Any, schema: Any) -> Any:
    """
    Prune obj to have only keys present in schema-by-example.
    For lists, apply recursively to first item's schema if present.
    """
    if obj is None or schema is None:
        return None
    if isinstance(schema, dict):
        out: Dict[str, Any] = {}
        for k, v in schema.items():
            if isinstance(obj, dict) and k in obj:
                out[k] = prune_to_schema(obj[k], v)
            else:
                out[k] = v
        return out
    if isinstance(schema, list):
        item_schema = schema[0] if schema else None
        if not isinstance(obj, list) or item_schema is None:
            return []
        return [prune_to_schema(x, item_schema) for x in obj][:10]
    return obj


def force_json(text: str, schema_example: Dict) -> Dict:
    payload = extract_json(text)
    try:
        data = json.loads(payload)
    except Exception:
        return schema_example
    return prune_to_schema(data, schema_example)


