"""
Adapters package for AI Failure Museum.
"""

from typing import Dict, List, Type

from afm.adapters.base import BaseAdapter
from afm.adapters.mock import MockAdapter

_REGISTRY: Dict[str, Type[BaseAdapter]] = {
    "mock": MockAdapter,
}


def get_adapter(name: str) -> BaseAdapter:
    """Instantiates the requested adapter by name."""
    clean = name.strip().lower()
    if clean not in _REGISTRY:
        raise ValueError(
            f"Unknown adapter '{name}'. Available adapters: {', '.join(_REGISTRY.keys())}"
        )
    return _REGISTRY[clean]()


def list_adapters() -> List[str]:
    """Returns names of available adapters."""
    return list(_REGISTRY.keys())
