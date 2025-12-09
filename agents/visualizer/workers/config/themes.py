"""Theme configuration for charts - EASILY UPGRADEABLE.

Add new themes here without touching worker code.
Each theme defines a complete Plotly template.
"""

# Default themes
THEMES = {
    "plotly_white": "plotly_white",
    "plotly_dark": "plotly_dark",
    "plotly": "plotly",
    "ggplot2": "ggplot2",
    "seaborn": "seaborn",
}

# Theme metadata for easy reference
THEME_METADATA = {
    "plotly_white": {
        "description": "Clean white background, professional look",
        "use_case": "Presentations, reports",
    },
    "plotly_dark": {
        "description": "Dark background with light text",
        "use_case": "Dashboards, night mode",
    },
    "plotly": {
        "description": "Default Plotly theme",
        "use_case": "General purpose",
    },
    "ggplot2": {
        "description": "R ggplot2 style",
        "use_case": "Statistical analysis",
    },
    "seaborn": {
        "description": "Python seaborn style",
        "use_case": "Data science",
    },
}

def get_theme(theme_name: str, default: str = "plotly_white") -> str:
    """Get theme template.
    
    Args:
        theme_name: Theme name
        default: Default theme if not found
        
    Returns:
        Plotly template string
    """
    return THEMES.get(theme_name, THEMES.get(default, "plotly_white"))


def list_themes() -> dict:
    """List available themes.
    
    Returns:
        Dictionary with theme information
    """
    return {
        "available_themes": list(THEMES.keys()),
        "count": len(THEMES),
        "metadata": THEME_METADATA,
    }


# TO ADD NEW THEME:
# 1. Add entry to THEMES dict
# 2. Add metadata to THEME_METADATA
# 3. Done! Workers automatically pick it up.
