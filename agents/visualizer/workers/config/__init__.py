"""Configuration module for Visualizer workers.

EASY UPGRADES:
- Add themes: Edit themes.py
- Add palettes: Edit palettes.py
- Workers automatically pick them up!
"""

from .themes import get_theme, list_themes, THEMES
from .palettes import get_palette, list_palettes, PALETTES

__all__ = [
    "get_theme",
    "list_themes",
    "THEMES",
    "get_palette",
    "list_palettes",
    "PALETTES",
]
