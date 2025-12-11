"""Report Generator Segment - Intelligent report generation with narrative + visuals.

Responsibilities:
- Analyze narrative to extract topics
- Map topics to relevant visualizations
- Intelligently select charts
- Format professional reports (HTML/PDF/Markdown)
- Handle user customization preferences

Workers:
- TopicAnalyzer: Extract topics from narrative text
- ChartMapper: Map topics to chart types
- ChartSelector: Intelligently pick relevant charts
- ReportFormatter: Create professional output formats
- CustomizationEngine: Handle user preferences

Integrated with Week 1 systems:
- Structured logging
- Error recovery with retry logic
- Input/output validation
"""

from .report_generator import ReportGenerator
from .workers.topic_analyzer import TopicAnalyzer
from .workers.chart_mapper import ChartMapper
from .workers.chart_selector import ChartSelector
from .workers.report_formatter import ReportFormatter
from .workers.customization_engine import CustomizationEngine

__all__ = [
    "ReportGenerator",
    "TopicAnalyzer",
    "ChartMapper",
    "ChartSelector",
    "ReportFormatter",
    "CustomizationEngine"
]
