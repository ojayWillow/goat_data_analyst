"""Visualizer Workers - Chart creation plugins.

EASY TO UPGRADE:
1. Create new worker inheriting BaseChartWorker
2. Add to exports below
3. Agent automatically picks it up!
"""

from .base_worker import BaseChartWorker, WorkerResult, ErrorType
from .line_worker import LineChartWorker
from .bar_worker import BarChartWorker
from .scatter_worker import ScatterPlotWorker
from .histogram_worker import HistogramWorker
from .boxplot_worker import BoxPlotWorker
from .heatmap_worker import HeatmapWorker
from .pie_worker import PieChartWorker
from .template_worker import TemplateChartWorker

__all__ = [
    "BaseChartWorker",
    "WorkerResult",
    "ErrorType",
    "LineChartWorker",
    "BarChartWorker",
    "ScatterPlotWorker",
    "HistogramWorker",
    "BoxPlotWorker",
    "HeatmapWorker",
    "PieChartWorker",
    "TemplateChartWorker",
]
