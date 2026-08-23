"""Channel-neutral contracts for embedding Trident in enterprise workflows."""

from src.integrations.builtin import builtin_integration_surfaces
from src.integrations.contracts import IntegrationOperation, IntegrationSurface

__all__ = [
    "IntegrationOperation",
    "IntegrationSurface",
    "builtin_integration_surfaces",
]
