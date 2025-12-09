"""Configuration module for Visualizer workers.

EASY UPGRADES:
- Add themes: Edit themes.py
- Add palettes: Edit palettes.py
- Validation automatic!
"""

from .themes import get_theme, list_themes, THEMES
from .palettes import get_palette, list_palettes, PALETTES
from .validator import ConfigValidator

__all__ = [
    "get_theme",
    "list_themes",
    "THEMES",
    "get_palette",
    "list_palettes",
    "PALETTES",
    "ConfigValidator",
]
