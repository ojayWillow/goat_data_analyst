"""Reporter Agent - Report generation and export.

Generates comprehensive data analysis reports in multiple formats.
Includes summary statistics, charts, insights, and recommendations.

Wired to use Workers Pattern:
- ExecutiveSummaryGenerator worker
- DataProfileGenerator worker
- StatisticalReportGenerator worker
- JSONExporter worker
- HTMLExporter worker

Integrated with Week 1 Systems:
- Structured logging with metrics
- Automatic retry with exponential backoff
- Error recovery and handling
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
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
structured_logger = get_structured_logger(__name__)


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
    
    Week 1 Integration:
    - Structured logging with metrics at each step
    - Automatic retry on transient failures
    - Error recovery and detailed error messages
    """
    
    def __init__(self):
        """Initialize Reporter agent with worker instances."""
        self.name = "Reporter"
        self.logger = get_logger("Reporter")
        self.structured_logger = get_structured_logger("Reporter")
        self.data = None
        self.reports = {}
        
        # Initialize workers
        self.executive_summary_generator = ExecutiveSummaryGenerator()
        self.data_profile_generator = DataProfileGenerator()
        self.statistical_report_generator = StatisticalReportGenerator()
        self.json_exporter = JSONExporter()
        self.html_exporter = HTMLExporter()
        
        self.logger.info(f"{self.name} initialized with 5 workers")
        self.structured_logger.info("Reporter initialized", {
            "workers": 5,
            "worker_names": [
                "ExecutiveSummaryGenerator",
                "DataProfileGenerator",
                "StatisticalReportGenerator",
                "JSONExporter",
                "HTMLExporter"
            ]
        })
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data for report generation.
        
        Args:
            df: DataFrame to report on
        """
        self.data = df.copy()
        self.reports = {}
        self.logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
        self.structured_logger.info("Data set for reporting", {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "dtypes": dict(df.dtypes.astype(str).value_counts())
        })
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data
    
    @retry_on_error(max_attempts=3, backoff=2)
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
            self.logger.info("Generating executive summary...")
            self.structured_logger.info("Executive summary generation started", {
                "rows": self.data.shape[0],
                "columns": self.data.shape[1]
            })
            
            # Delegate to worker
            worker_result = self.executive_summary_generator.safe_execute(df=self.data)
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            report = worker_result.data
            self.reports["executive_summary"] = report
            
            self.structured_logger.info("Executive summary generated successfully", {
                "sections": len(report.get("sections", {})),
                "status": "success"
            })
            
            return report
        
        except Exception as e:
            self.logger.error(f"Executive summary generation failed: {e}")
            self.structured_logger.error("Executive summary generation failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise AgentError(f"Generation failed: {e}")
    
    @retry_on_error(max_attempts=3, backoff=2)
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
            self.logger.info("Generating data profile...")
            self.structured_logger.info("Data profile generation started", {
                "rows": self.data.shape[0],
                "columns": self.data.shape[1]
            })
            
            # Delegate to worker
            worker_result = self.data_profile_generator.safe_execute(df=self.data)
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            report = worker_result.data
            self.reports["data_profile"] = report
            
            self.structured_logger.info("Data profile generated successfully", {
                "columns_analyzed": len(report.get("columns", {})),
                "status": "success"
            })
            
            return report
        
        except Exception as e:
            self.logger.error(f"Data profile generation failed: {e}")
            self.structured_logger.error("Data profile generation failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise AgentError(f"Generation failed: {e}")
    
    @retry_on_error(max_attempts=3, backoff=2)
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
            self.logger.info("Generating statistical report...")
            self.structured_logger.info("Statistical report generation started", {
                "rows": self.data.shape[0],
                "columns": self.data.shape[1]
            })
            
            # Delegate to worker
            worker_result = self.statistical_report_generator.safe_execute(df=self.data)
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            report = worker_result.data
            self.reports["statistical_analysis"] = report
            
            self.structured_logger.info("Statistical report generated successfully", {
                "analysis_types": len(report.get("statistics", {})),
                "status": "success"
            })
            
            return report
        
        except Exception as e:
            self.logger.error(f"Statistical report generation failed: {e}")
            self.structured_logger.error("Statistical report generation failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise AgentError(f"Generation failed: {e}")
    
    @retry_on_error(max_attempts=3, backoff=2)
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
            self.logger.info("Generating comprehensive report...")
            self.structured_logger.info("Comprehensive report generation started", {
                "rows": self.data.shape[0],
                "columns": self.data.shape[1]
            })
            
            # Generate all sub-reports using workers
            executive = self.generate_executive_summary()
            profile = self.generate_data_profile()
            statistical = self.generate_statistical_report()
            
            report = {
                "status": "success",
                "report_type": "comprehensive_analysis",
                "generated_at": datetime.now().isoformat(),
                "title": "Data Analysis Report",
                "description": "Comprehensive analysis of dataset including profiling, statistics, and quality assessment.",
                "sections": {
                    "executive_summary": executive,
                    "data_profile": profile,
                    "statistical_analysis": statistical,
                },
                "metadata": {
                    "data_shape": {"rows": self.data.shape[0], "columns": self.data.shape[1]},
                    "generated_timestamp": datetime.now().isoformat(),
                    "report_version": "1.0",
                },
            }
            
            self.reports["comprehensive"] = report
            
            self.structured_logger.info("Comprehensive report generated successfully", {
                "sections_count": len(report["sections"]),
                "data_shape": report["metadata"]["data_shape"],
                "status": "success"
            })
            
            return report
        
        except Exception as e:
            self.logger.error(f"Comprehensive report generation failed: {e}")
            self.structured_logger.error("Comprehensive report generation failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise AgentError(f"Generation failed: {e}")
    
    @retry_on_error(max_attempts=3, backoff=2)
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
            
            self.logger.info(f"Exporting {report_type} to JSON...")
            self.structured_logger.info("JSON export started", {
                "report_type": report_type,
                "file_path": file_path
            })
            
            # Delegate to worker
            worker_result = self.json_exporter.safe_execute(
                report_data=self.reports[report_type],
                file_path=file_path
            )
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            self.structured_logger.info("JSON export completed successfully", {
                "report_type": report_type,
                "file_size": worker_result.data.get("file_size", "unknown")
            })
            
            return worker_result.data
        
        except Exception as e:
            self.logger.error(f"JSON export failed: {e}")
            self.structured_logger.error("JSON export failed", {
                "report_type": report_type,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise AgentError(f"Export failed: {e}")
    
    @retry_on_error(max_attempts=3, backoff=2)
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
            
            self.logger.info(f"Exporting {report_type} to HTML...")
            self.structured_logger.info("HTML export started", {
                "report_type": report_type,
                "file_path": file_path
            })
            
            # Delegate to worker
            worker_result = self.html_exporter.safe_execute(
                report_data=self.reports[report_type],
                file_path=file_path
            )
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            self.structured_logger.info("HTML export completed successfully", {
                "report_type": report_type,
                "file_size": worker_result.data.get("file_size", "unknown")
            })
            
            return worker_result.data
        
        except Exception as e:
            self.logger.error(f"HTML export failed: {e}")
            self.structured_logger.error("HTML export failed", {
                "report_type": report_type,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise AgentError(f"Export failed: {e}")
    
    def list_reports(self) -> Dict[str, Any]:
        """List all generated reports.
        
        Returns:
            Dictionary with report information
        """
        result = {
            "status": "success",
            "count": len(self.reports),
            "reports": list(self.reports.keys()),
        }
        
        self.structured_logger.info("Reports listed", {
            "count": result["count"],
            "reports": result["reports"]
        })
        
        return result
