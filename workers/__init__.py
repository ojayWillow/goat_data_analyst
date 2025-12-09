"""Workers module - Specialized workers for agents.

Each worker handles a specific task with quality validation.
Workers communicate in a common language (same interface/protocol).
"""

from .base_worker import BaseWorker
from .validation import ValidationResult, QualityValidator

__all__ = [
    'BaseWorker',
    'ValidationResult',
    'QualityValidator',
]
