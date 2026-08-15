"""Framework-neutral application core for Trident."""

from src.core.container import ServiceContainer
from src.core.registry import ExtensionRegistry
from src.core.runtime import EvolutionPolicy, ResearchRunContext

__all__ = [
    "EvolutionPolicy",
    "ExtensionRegistry",
    "ResearchRunContext",
    "ServiceContainer",
]
