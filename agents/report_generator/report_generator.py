"""ReportGenerator - Main coordinator for intelligent report generation.

Orchestrates all workers to create professional reports with narrative + visuals.
Integrated with Week 1 systems:
- Structured logging
- Error recovery with retry logic
- Input/output validation
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import WorkerError
from core.error_recovery import retry_on_error
from core.validators import validate_output
from agents.report_generator.workers.topic_analyzer import TopicAnalyzer
from agents.report_generator.workers.chart_mapper import ChartMapper
from agents.report_generator.workers.chart_selector import ChartSelector
from agents.report_generator.workers.report_formatter import ReportFormatter
from agents.report_generator.workers.customization_engine import CustomizationEngine


class ReportGenerator:
    """Main coordinator for intelligent report generation.
    
    Responsibilities:
    - Analyze narrative to extract topics
    - Map topics to visualizations
    - Intelligently select relevant charts
    - Format professional reports
    - Handle user customization
    
    Workers:
    - TopicAnalyzer: Extract topics from narrative
    - ChartMapper: Map topics to chart types  
    - ChartSelector: Select relevant charts
    - ReportFormatter: Create formatted output
    - CustomizationEngine: Handle user preferences
    
    Architecture:
    - Uses worker pattern for separation of concerns
    - Each worker handles one specific responsibility
    - Clean interfaces between components
    - Integrated with Week 1 systems
    - Error Intelligence monitoring at worker level
    """

    def __init__(self) -> None:
        """Initialize ReportGenerator with all workers."""
        self.name = "ReportGenerator"
        self.logger = get_logger("ReportGenerator")
        self.structured_logger = get_structured_logger("ReportGenerator")
        
        # Initialize workers
        self.topic_analyzer = TopicAnalyzer()
        self.chart_mapper = ChartMapper()
        self.chart_selector = ChartSelector(self.chart_mapper)
        self.report_formatter = ReportFormatter()
        self.customization_engine = CustomizationEngine()
        
        # Tracking
        self.generated_reports = []
        
        self.logger.info("ReportGenerator initialized with 5 workers")
        self.structured_logger.info("ReportGenerator initialized", {
            'version': '1.0-intelligent',
            'workers': [
                'TopicAnalyzer',
                'ChartMapper',
                'ChartSelector',
                'ReportFormatter',
                'CustomizationEngine'
            ]
        })

    # ========== Topic Analysis ==========

    @retry_on_error(max_attempts=2, backoff=1)
    def analyze_narrative(self, narrative: str) -> Dict[str, Any]:
        """Analyze narrative to extract topics and structure.
        
        Args:
            narrative: Full narrative text
        
        Returns:
            Analysis dict with topics and structure
        
        Raises:
            WorkerError: If analysis fails
        """
        try:
            self.logger.info("Analyzing narrative")
            return self.topic_analyzer.analyze_narrative(narrative)
        except Exception as e:
            self.logger.error(f"Narrative analysis failed: {e}")
            raise

    # ========== Chart Selection ==========

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def select_charts_for_narrative(
        self,
        narrative: str,
        available_charts: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Select best charts for narrative.
        
        Args:
            narrative: Full narrative text
            available_charts: List of available chart objects
            user_preferences: Optional user preferences
        
        Returns:
            Selected charts organized by section (validated)
        
        Raises:
            WorkerError: If selection fails
        """
        try:
            self.logger.info("Selecting charts for narrative")
            self.structured_logger.info("Chart selection started", {
                'available_charts': len(available_charts),
                'has_preferences': user_preferences is not None
            })
            
            # Step 1: Analyze narrative
            sections = self.topic_analyzer.extract_narrative_sections(narrative)
            
            # Step 2: Select charts
            selected = self.chart_selector.select_charts_for_narrative(
                sections,
                available_charts,
                user_preferences
            )
            
            # Get summary
            summary = self.chart_selector.get_selection_summary(selected)
            self.structured_logger.info("Chart selection complete", summary)
            
            return selected
        
        except Exception as e:
            self.logger.error(f"Chart selection failed: {e}")
            raise WorkerError(f"Chart selection failed: {e}")

    # ========== Report Generation ==========

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def generate_report(
        self,
        narrative: str,
        available_charts: List[Dict[str, Any]],
        title: str = "Data Analysis Report",
        output_format: str = 'html',
        user_preferences: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate complete report with narrative and charts.
        
        Args:
            narrative: Full narrative text
            available_charts: List of available charts
            title: Report title
            output_format: Output format ('html', 'markdown', 'pdf')
            user_preferences: Optional user customization preferences
            metadata: Optional report metadata
        
        Returns:
            Report dict with formatted content (validated)
        
        Raises:
            WorkerError: If generation fails
        """
        if not narrative:
            raise WorkerError("Narrative is required")
        if not available_charts:
            raise WorkerError("At least one chart is required")
        if output_format not in ['html', 'markdown', 'pdf']:
            raise WorkerError(f"Unsupported format: {output_format}")
        
        try:
            self.logger.info(f"Generating {output_format} report")
            self.structured_logger.info("Report generation started", {
                'format': output_format,
                'title': title,
                'charts_available': len(available_charts)
            })
            
            # Step 1: Select charts
            selected_charts = self.select_charts_for_narrative(
                narrative,
                available_charts,
                user_preferences
            )
            
            # Step 2: Format output
            if output_format == 'html':
                formatted = self.report_formatter.format_to_html(
                    narrative,
                    selected_charts,
                    title,
                    metadata
                )
            elif output_format == 'markdown':
                formatted = self.report_formatter.format_to_markdown(
                    narrative,
                    selected_charts,
                    title,
                    metadata
                )
            else:  # pdf
                # For now, return HTML (PDF generation would require external lib)
                formatted = self.report_formatter.format_to_html(
                    narrative,
                    selected_charts,
                    title,
                    metadata
                )
            
            # Step 3: Create result
            report = {
                'status': 'success',
                'report_type': 'intelligent_analysis',
                'title': title,
                'format': output_format,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'narrative': narrative,
                'selected_charts': selected_charts,
                'formatted_content': formatted,
                'metadata': metadata or {},
                'summary': {
                    'sections': len(selected_charts),
                    'total_charts': sum(len(c) for c in selected_charts.values()),
                    'word_count': len(narrative.split())
                }
            }
            
            # Track report
            self.generated_reports.append({
                'title': title,
                'format': output_format,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'charts_count': report['summary']['total_charts']
            })
            
            self.structured_logger.info("Report generation complete", {
                'format': output_format,
                'sections': report['summary']['sections'],
                'charts': report['summary']['total_charts'],
                'size_kb': len(formatted) / 1024
            })
            
            return report
        
        except WorkerError:
            raise
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise WorkerError(f"Report generation failed: {e}")

    # ========== Quick Report Methods ==========

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def generate_html_report(
        self,
        narrative: str,
        available_charts: List[Dict[str, Any]],
        title: str = "Data Analysis Report",
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate HTML report (validated)."""
        return self.generate_report(
            narrative,
            available_charts,
            title,
            'html',
            user_preferences
        )

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def generate_markdown_report(
        self,
        narrative: str,
        available_charts: List[Dict[str, Any]],
        title: str = "Data Analysis Report",
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate Markdown report (validated)."""
        return self.generate_report(
            narrative,
            available_charts,
            title,
            'markdown',
            user_preferences
        )

    # ========== Customization Methods ==========

    def get_customization_options(
        self,
        available_charts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Get available customization options.
        
        Args:
            available_charts: Optional available charts
        
        Returns:
            Customization options dict
        """
        return self.customization_engine.get_customization_options(available_charts)

    def get_preset(self, preset_name: str) -> Dict[str, Any]:
        """Get a customization preset.
        
        Args:
            preset_name: Name of the preset
        
        Returns:
            Preset dict
        """
        return self.customization_engine.get_preset(preset_name)

    def list_presets(self) -> List[Dict[str, str]]:
        """List available customization presets.
        
        Returns:
            List of preset summaries
        """
        return self.customization_engine.list_presets()

    def validate_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user preferences.
        
        Args:
            preferences: User preferences dict
        
        Returns:
            Validation result dict
        """
        return self.customization_engine.validate_preferences(preferences)

    # ========== Status & Reporting ==========

    @validate_output('dict')
    def get_status(self) -> Dict[str, Any]:
        """Get current ReportGenerator status.
        
        Returns:
            Status dict (validated)
        """
        return {
            'name': self.name,
            'status': 'active',
            'workers': 5,
            'reports_generated': len(self.generated_reports),
            'last_report': self.generated_reports[-1] if self.generated_reports else None
        }

    @validate_output('dict')
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed status including all reports.
        
        Returns:
            Detailed status dict (validated)
        """
        return {
            'name': self.name,
            'status': 'active',
            'workers': {
                'topic_analyzer': self.topic_analyzer.name,
                'chart_mapper': self.chart_mapper.name,
                'chart_selector': self.chart_selector.name,
                'report_formatter': self.report_formatter.name,
                'customization_engine': self.customization_engine.name
            },
            'reports_generated': len(self.generated_reports),
            'reports': self.generated_reports[-10:] if self.generated_reports else [],
            'capabilities': {
                'formats': ['html', 'markdown', 'pdf'],
                'chart_selection': True,
                'customization': True,
                'user_preferences': True
            }
        }

    # ========== Utility Methods ==========

    def reset(self) -> None:
        """Reset report generator (clear history)."""
        self.generated_reports = []
        self.logger.info("ReportGenerator reset")

    def shutdown(self) -> None:
        """Shutdown report generator."""
        self.reset()
        self.logger.info("ReportGenerator shutdown")
