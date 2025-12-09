"""Color palette configuration - EASILY UPGRADEABLE.

Add new color palettes here without touching worker code.
Each palette is a Plotly color scale or list of colors.
"""

# Built-in Plotly scales
PALETTES = {
    # Sequential (low to high)
    "viridis": "Viridis",
    "plasma": "Plasma",
    "inferno": "Inferno",
    "blues": "Blues",
    "greens": "Greens",
    "purples": "Purples",
    "greys": "Greys",
    
    # Diverging (centered)
    "rdbu": "RdBu",
    "brbg": "BrBG",
    "piyg": "PiYG",
    "rdgy": "RdGy",
    
    # Categorical (distinct)
    "set1": "Set1",
    "set2": "Set2",
    "pastel": "Pastel",
    "dark": "Dark",
    "bold": "Bold",
    
    # Custom
    "ocean": "Blues",
    "sunset": "Reds",
    "forest": "Greens",
    "twilight": "Purples",
}

# Palette metadata
PALETTE_METADATA = {
    "viridis": {
        "type": "sequential",
        "description": "Perceptually uniform, colorblind-friendly",
        "best_for": "Continuous data, heatmaps",
    },
    "rdbu": {
        "type": "diverging",
        "description": "Red-Blue diverging scale",
        "best_for": "Correlation matrices, positive/negative data",
    },
    "set1": {
        "type": "categorical",
        "description": "Distinct colors for categories",
        "best_for": "Pie charts, bar charts, categories",
    },
}

def get_palette(palette_name: str, default: str = "viridis") -> str:
    """Get color palette.
    
    Args:
        palette_name: Palette name
        default: Default palette if not found
        
    Returns:
        Plotly color scale string
    """
    return PALETTES.get(palette_name, PALETTES.get(default, "Viridis"))


def list_palettes() -> dict:
    """List available palettes.
    
    Returns:
        Dictionary with palette information
    """
    return {
        "available_palettes": list(PALETTES.keys()),
        "count": len(PALETTES),
        "metadata": PALETTE_METADATA,
    }


def get_palette_by_type(palette_type: str) -> dict:
    """Get palettes by type.
    
    Args:
        palette_type: "sequential", "diverging", or "categorical"
        
    Returns:
        Dictionary of matching palettes
    """
    matching = {}
    for name, metadata in PALETTE_METADATA.items():
        if metadata.get("type") == palette_type:
            matching[name] = PALETTES.get(name)
    return matching


# TO ADD NEW PALETTE:
# 1. Add entry to PALETTES dict
# 2. Add metadata to PALETTE_METADATA (optional)
# 3. Done! Workers automatically pick it up.
