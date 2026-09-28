"""
Synthetic data generator package for component burn-in screening.
"""

from .generator import (
    SyntheticDatasetGenerator,
    generate_synthetic_data,
    DEFAULT_PARAMETERS,
    COMPONENT_TYPES,
)

__all__ = [
    "SyntheticDatasetGenerator",
    "generate_synthetic_data",
    "DEFAULT_PARAMETERS",
    "COMPONENT_TYPES",
]
