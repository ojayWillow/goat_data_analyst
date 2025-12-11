"""Template Worker - Example for creating new chart types.

Use this as a template when adding new chart types.
Just copy this file, rename the class, implement execute(), and register in __init__.py.
"""

import pandas as pd
from typing import Any, Dict, Optional

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .base_worker import BaseChartWorker, WorkerResult, ErrorType
from .config import get_theme
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)


class TemplateChartWorker(BaseChartWorker):
    """Template worker - Copy and modify to create new chart types.
    
    STEPS TO CREATE NEW CHART:
    1. Copy this file to my_new_chart_worker.py
    2. Rename TemplateChartWorker to MyNewChartWorker
    3. Update chart_type in __init__
    4. Implement execute() with your chart logic
    5. Add to workers/__init__.py exports
    6. Done! Agent automatically picks it up.
    """
    
    def __init__(self):
        """Initialize TemplateChartWorker.
        
        Change these:
        - "TemplateChartWorker" → Your worker class name
        - "template" → Your chart type identifier
        """
        super().__init__("TemplateChartWorker", "template")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute chart creation.
        
        Args:
            df: DataFrame to visualize
            **kwargs: Chart-specific parameters
            
        Returns:
            WorkerResult with chart
            
        TEMPLATE STRUCTURE:
        1. Extract parameters
        2. Create result object
        3. Validate inputs
        4. Check Plotly available
        5. Create chart using plotly
        6. Store chart and metadata
        7. Return result
        """
        # STEP 1: Extract parameters
        df = kwargs.get('df')
        title = kwargs.get('title')
        theme = kwargs.get('theme', 'plotly_white')
        
        # STEP 2: Create result
        result = self._create_result()
        
        # STEP 3: Validate inputs
        validation = self._validate_dataframe(df)
        if validation:
            return validation
        
        # STEP 4: Check dependencies
        try:
            if not PLOTLY_AVAILABLE:
                self._add_error(result, ErrorType.MISSING_DEPENDENCY, "Plotly not installed")
                result.success = False
                return result
            
            # STEP 5: Create chart
            # fig = px.your_chart_type(...)
            
            # STEP 6: Store result
            # result.data = fig
            # result.plotly_json = fig.to_json()
            # result.metadata = {...}
            
            logger.info(f"Chart created")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.RENDER_ERROR, str(e))
            result.success = False
            return result
