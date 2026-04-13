"""Small helpers for reading YAML and ensuring directories exist."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, MutableMapping

import yaml


_yaml_cache: dict[Path, Mapping[str, Any]] = {}


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists.

    Args:
        path: Directory path.

    Returns:
        The same path.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_yaml_cached(path: Path) -> Mapping[str, Any]:
    """Load a YAML file with simple in-process caching.

    Args:
        path: Path to YAML.

    Returns:
        Parsed mapping.

    Raises:
        FileNotFoundError: If file is missing.
    """
    resolved = path.resolve()
    if resolved not in _yaml_cache:
        with resolved.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, MutableMapping):
            raise ValueError(f"YAML root must be a mapping: {resolved}")
        _yaml_cache[resolved] = data
    return _yaml_cache[resolved]


def clear_yaml_cache() -> None:
    """Clear YAML cache (mainly for tests)."""
    _yaml_cache.clear()
