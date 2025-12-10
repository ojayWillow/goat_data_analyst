"""Reporter Agent - Report generation and export.

Generates comprehensive data analysis reports in multiple formats.
Includes summary statistics, charts, insights, and recommendations.

Wired to use Workers Pattern:
- ExecutiveSummaryGenerator worker
- DataProfileGenerator worker
- StatisticalReportGenerator worker
- JSONExporter worker
- HTMLExporter worker
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from core.exceptions import AgentError

# Worker imports
from agents.reporter.workers import (
    ExecutiveSummaryGenerator,
    DataProfileGenerator,
    StatisticalReportGenerator,
    JSONExporter,
    HTMLExporter,
)

logger = get_logger(__name__)


class Reporter:
    """Agent for report generation.
    
    Capabilities:
    - Executive summaries (via ExecutiveSummaryGenerator worker)
    - Data profiling reports (via DataProfileGenerator worker)
    - Statistical analysis reports (via StatisticalReportGenerator worker)
    - JSON export (via JSONExporter worker)
    - HTML export (via HTMLExporter worker)
    - Report templates
    - Anomaly reports
    - Trend analysis reports
    - CSV export
    
    Worker Pattern:
    - Delegates specific report generation tasks to specialized workers
    - Each worker handles one specific report type or export format
    - Aggregates worker results into unified reports
    """
    
    def __init__(self):
        """Initialize Reporter agent with worker instances."""
        self.name = "Reporter"
        self.data = None
        self.reports = {}
        
        # Initialize workers
        self.executive_summary_generator = ExecutiveSummaryGenerator()
        self.data_profile_generator = DataProfileGenerator()
        self.statistical_report_generator = StatisticalReportGenerator()
        self.json_exporter = JSONExporter()
        self.html_exporter = HTMLExporter()
        
        logger.info(f"{self.name} initialized with 5 workers")
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data for report generation.
        
        Args:
            df: DataFrame to report on
        """
        self.data = df.copy()
        self.reports = {}
        logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data
    
    def generate_executive_summary(self) -> Dict[str, Any]:
        """Delegate executive summary generation to worker.
        
        Returns:
            Dictionary with summary information
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Generating executive summary...")
            
            # Delegate to worker
            worker_result = self.executive_summary_generator.safe_execute(df=self.data)
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            report = worker_result.data
            self.reports["executive_summary"] = report
            
            return report
        
        except Exception as e:
            logger.error(f"Executive summary generation failed: {e}")
            raise AgentError(f"Generation failed: {e}")
    
    def generate_data_profile(self) -> Dict[str, Any]:
        """Delegate data profile generation to worker.
        
        Returns:
            Dictionary with data profile
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Generating data profile...")
            
            # Delegate to worker
            worker_result = self.data_profile_generator.safe_execute(df=self.data)
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            report = worker_result.data
            self.reports["data_profile"] = report
            
            return report
        
        except Exception as e:
            logger.error(f"Data profile generation failed: {e}")
            raise AgentError(f"Generation failed: {e}")
    
    def generate_statistical_report(self) -> Dict[str, Any]:
        """Delegate statistical report generation to worker.
        
        Returns:
            Dictionary with statistical analysis
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Generating statistical report...")
            
            # Delegate to worker
            worker_result = self.statistical_report_generator.safe_execute(df=self.data)
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            report = worker_result.data
            self.reports["statistical_analysis"] = report
            
            return report
        
        except Exception as e:
            logger.error(f"Statistical report generation failed: {e}")
            raise AgentError(f"Generation failed: {e}")
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report with all sections.
        
        Returns:
            Dictionary with complete report
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Generating comprehensive report...")
            
            # Generate all sub-reports using workers
            executive = self.generate_executive_summary()
            profile = self.generate_data_profile()
            statistical = self.generate_statistical_report()
            
            report = {
                "status": "success",
                "report_type": "comprehensive_analysis",
                "generated_at": datetime.utcnow().isoformat(),
                "title": "Data Analysis Report",
                "description": "Comprehensive analysis of dataset including profiling, statistics, and quality assessment.",
                "sections": {
                    "executive_summary": executive,
                    "data_profile": profile,
                    "statistical_analysis": statistical,
                },
                "metadata": {
                    "data_shape": {"rows": self.data.shape[0], "columns": self.data.shape[1]},
                    "generated_timestamp": datetime.utcnow().isoformat(),
                    "report_version": "1.0",
                },
            }
            
            self.reports["comprehensive"] = report
            return report
        
        except Exception as e:
            logger.error(f"Comprehensive report generation failed: {e}")
            raise AgentError(f"Generation failed: {e}")
    
    def export_to_json(self, report_type: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Delegate JSON export to worker.
        
        Args:
            report_type: Type of report to export
            file_path: Optional file path (default: report_<type>_<timestamp>.json)
            
        Returns:
            Dictionary with export information
            
        Raises:
            AgentError: If report not found
        """
        try:
            if report_type not in self.reports:
                raise AgentError(f"Report '{report_type}' not found")
            
            logger.info(f"Exporting {report_type} to JSON...")
            
            # Delegate to worker
            worker_result = self.json_exporter.safe_execute(
                report_data=self.reports[report_type],
                file_path=file_path
            )
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            return worker_result.data
        
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise AgentError(f"Export failed: {e}")
    
    def export_to_html(self, report_type: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Delegate HTML export to worker.
        
        Args:
            report_type: Type of report to export
            file_path: Optional file path (default: report_<type>_<timestamp>.html)
            
        Returns:
            Dictionary with export information
            
        Raises:
            AgentError: If report not found
        """
        try:
            if report_type not in self.reports:
                raise AgentError(f"Report '{report_type}' not found")
            
            logger.info(f"Exporting {report_type} to HTML...")
            
            # Delegate to worker
            worker_result = self.html_exporter.safe_execute(
                report_data=self.reports[report_type],
                file_path=file_path
            )
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            return worker_result.data
        
        except Exception as e:
            logger.error(f"HTML export failed: {e}")
            raise AgentError(f"Export failed: {e}")
    
    def list_reports(self) -> Dict[str, Any]:
        """List all generated reports.
        
        Returns:
            Dictionary with report information
        """
        return {
            "status": "success",
            "count": len(self.reports),
            "reports": list(self.reports.keys()),
        }
