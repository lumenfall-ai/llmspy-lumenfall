"""
Dynamic model catalog for Lumenfall llmspy extension.

Loads models from a cached JSON file (refreshed from the API at runtime)
or falls back to a static models.json shipped with the package.
"""

import json
import os

_here = os.path.dirname(os.path.abspath(__file__))
_static_path = os.path.join(_here, "models.json")
_cache_path = None  # set by set_cache_dir()

_DEFAULT_MODALITIES = {"input": ["text"], "output": ["image"]}


def _load_static_modalities():
    """Load modalities lookup from the static models.json shipped with the package."""
    try:
        with open(_static_path) as f:
            data = json.load(f)
        return {
            m["id"]: m["modalities"]
            for m in data.get("data", [])
            if "modalities" in m
        }
    except (json.JSONDecodeError, OSError, KeyError):
        return {}


_static_modalities = _load_static_modalities()


def set_cache_dir(cache_dir):
    """Set the directory for the cached models file."""
    global _cache_path
    os.makedirs(cache_dir, exist_ok=True)
    _cache_path = os.path.join(cache_dir, "lumenfall_models.json")


def get_models():
    """Return models from cache (if exists) or static fallback."""
    # Try cached version first (downloaded from API)
    if _cache_path and os.path.exists(_cache_path):
        try:
            with open(_cache_path) as f:
                return _parse_models(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    # Fall back to static file shipped with the package
    with open(_static_path) as f:
        return _parse_models(json.load(f))


def save_models(api_response):
    """Save API response to cache."""
    if not _cache_path:
        return
    with open(_cache_path, "w") as f:
        json.dump(api_response, f)


def _parse_models(api_response):
    """Convert API /v1/models response to {id: {id, name, modalities}} dict.

    Modalities are resolved in priority order:
    1. From the API response (future gateway support)
    2. From the static models.json shipped with the package
    3. Default: text input, image output
    """
    models = {}
    for m in api_response.get("data", []):
        mid = m["id"]
        models[mid] = {
            "id": mid,
            "name": m.get("name", mid),
            "modalities": (
                m.get("modalities")
                or _static_modalities.get(mid)
                or _DEFAULT_MODALITIES
            ),
        }
    return models
