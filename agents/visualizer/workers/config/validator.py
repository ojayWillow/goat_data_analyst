"""Config validation - Prevent silent failures.

Validates themes and palettes before use.
Throws clear errors instead of silent failures.
"""

from typing import Tuple
from .themes import THEMES, list_themes
from .palettes import PALETTES, list_palettes


class ConfigValidator:
    """Validates chart configuration."""
    
    @staticmethod
    def validate_theme(theme_name: str) -> Tuple[bool, str]:
        """Validate theme name.
        
        Args:
            theme_name: Theme name to validate
            
        Returns:
            (is_valid, message)
        """
        if not theme_name:
            return False, "Theme name cannot be empty"
        
        if theme_name not in THEMES:
            available = list(THEMES.keys())
            return False, f"Theme '{theme_name}' not found. Available: {available}"
        
        return True, "OK"
    
    @staticmethod
    def validate_palette(palette_name: str) -> Tuple[bool, str]:
        """Validate palette name.
        
        Args:
            palette_name: Palette name to validate
            
        Returns:
            (is_valid, message)
        """
        if not palette_name:
            return False, "Palette name cannot be empty"
        
        if palette_name not in PALETTES:
            available = list(PALETTES.keys())
            return False, f"Palette '{palette_name}' not found. Available: {available}"
        
        return True, "OK"
    
    @staticmethod
    def validate_bins(bins: int) -> Tuple[bool, str]:
        """Validate histogram bins.
        
        Args:
            bins: Number of bins
            
        Returns:
            (is_valid, message)
        """
        if not isinstance(bins, int):
            return False, f"Bins must be integer, got {type(bins)}"
        
        if bins < 1:
            return False, f"Bins must be >= 1, got {bins}"
        
        if bins > 1000:
            return False, f"Bins must be <= 1000 (got {bins}) to avoid performance issues"
        
        return True, "OK"
    
    @staticmethod
    def validate_marker_bool(value: any) -> Tuple[bool, str]:
        """Validate boolean parameter.
        
        Args:
            value: Boolean value to validate
            
        Returns:
            (is_valid, message)
        """
        if not isinstance(value, bool):
            return False, f"Expected boolean, got {type(value)}"
        
        return True, "OK"
