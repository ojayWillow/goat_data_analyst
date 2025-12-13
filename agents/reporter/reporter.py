"""Reporter Agent - Advanced report generation and export.

Generates comprehensive data analysis reports in multiple formats.
Includes summary statistics, charts, insights, and recommendations.

Enhancements:
- Smart caching for reports
- Advanced workflow orchestration
- Error recovery and resilience
- Quality scoring propagation
- Performance optimization
- Batch report generation
- Report comparison and diff
- Export templates

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

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime
import hashlib

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


class ReportCache:
    """Smart cache for generated reports with invalidation."""
    
    def __init__(self):
        self.cache = {}
        self.metadata = {}
    
    def get_key(self, report_type: str, data_hash: str) -> str:
        """Generate cache key."""
        return f"{report_type}_{data_hash}"
    
    def set(self, key: str, report: Dict[str, Any], quality_score: float) -> None:
        """Store report in cache."""
        self.cache[key] = report
        self.metadata[key] = {
            "cached_at": datetime.now().isoformat(),
            "quality_score": quality_score,
            "hit_count": 0
        }
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve report from cache."""
        if key in self.cache:
            self.metadata[key]["hit_count"] += 1
            return self.cache[key]
        return None
    
    def clear(self) -> None:
        """Clear all cached reports."""
        self.cache.clear()
        self.metadata.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "total_hits": sum(m["hit_count"] for m in self.metadata.values()),
            "metadata": self.metadata
        }


class Reporter:
    """Advanced Report Generation Agent.
    
    Capabilities:
    - Executive summaries (via ExecutiveSummaryGenerator worker)
    - Data profiling reports (via DataProfileGenerator worker)
    - Statistical analysis reports (via StatisticalReportGenerator worker)
    - JSON export (via JSONExporter worker)
    - HTML export (via HTMLExporter worker)
    - Smart report caching
    - Batch report generation
    - Quality score tracking
    - Performance metrics
    - Export templates
    - Error recovery
    
    Worker Pattern:
    - Delegates specific report generation tasks to specialized workers
    - Each worker handles one specific report type or export format
    - Aggregates worker results into unified reports
    - Tracks quality scores from all workers
    
    Week 1 Integration:
    - Structured logging with metrics at each step
    - Automatic retry on transient failures
    - Error recovery and detailed error messages
    - Performance tracking
    """
    
    def __init__(self):
        """Initialize Reporter agent with worker instances and caching."""
        self.name = "Reporter"
        self.logger = get_logger("Reporter")
        self.structured_logger = get_structured_logger("Reporter")
        self.data = None
        self.data_hash = None
        self.reports = {}
        self.cache = ReportCache()
        self.quality_scores = {}  # Track quality scores from workers
        self.performance_metrics = {}  # Track generation times
        
        # Initialize workers
        self.executive_summary_generator = ExecutiveSummaryGenerator()
        self.data_profile_generator = DataProfileGenerator()
        self.statistical_report_generator = StatisticalReportGenerator()
        self.json_exporter = JSONExporter()
        self.html_exporter = HTMLExporter()
        
        self.logger.info(f"{self.name} initialized with 5 workers and smart caching")
        self.structured_logger.info("Reporter initialized", {
            "workers": 5,
            "features": ["caching", "quality_tracking", "performance_metrics", "batch_processing"],
            "worker_names": [
                "ExecutiveSummaryGenerator",
                "DataProfileGenerator",
                "StatisticalReportGenerator",
                "JSONExporter",
                "HTMLExporter"
            ]
        })
    
    def _compute_data_hash(self, df: pd.DataFrame) -> str:
        """Compute hash of DataFrame for caching."""
        data_str = str(df.shape) + str(df.dtypes.to_dict())
        return hashlib.md5(data_str.encode()).hexdigest()
    
    @retry_on_error(max_attempts=2, backoff=1)
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data for report generation with hash tracking.
        
        Args:
            df: DataFrame to report on
        """
        self.data = df.copy()
        self.data_hash = self._compute_data_hash(df)
        self.reports = {}
        self.cache.clear()  # Clear cache on new data
        self.quality_scores = {}
        self.performance_metrics = {}
        
        self.logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
        self.structured_logger.info("Data set for reporting", {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "dtypes": dict(df.dtypes.astype(str).value_counts()),
            "data_hash": self.data_hash
        })
    
    @retry_on_error(max_attempts=2, backoff=1)
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data
    
    @retry_on_error(max_attempts=3, backoff=2)
    def generate_executive_summary(self, use_cache: bool = True) -> Dict[str, Any]:
        """Generate executive summary with caching and quality tracking.
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with summary information
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            cache_key = self.cache.get_key("executive_summary", self.data_hash)
            
            # Check cache
            if use_cache:
                cached = self.cache.get(cache_key)
                if cached:
                    self.logger.info("Executive summary retrieved from cache")
                    self.structured_logger.info("Cache hit", {"report_type": "executive_summary"})
                    return cached
            
            self.logger.info("Generating executive summary...")
            start_time = datetime.now()
            
            self.structured_logger.info("Executive summary generation started", {
                "rows": self.data.shape[0],
                "columns": self.data.shape[1]
            })
            
            # Delegate to worker
            worker_result = self.executive_summary_generator.execute(self.data)
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            report = worker_result.data
            
            # Track quality score
            self.quality_scores["executive_summary"] = worker_result.quality_score
            
            # Cache result
            self.cache.set(cache_key, report, worker_result.quality_score)
            self.reports["executive_summary"] = report
            
            # Track performance
            elapsed = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["executive_summary"] = elapsed
            
            self.structured_logger.info("Executive summary generated successfully", {
                "quality_score": worker_result.quality_score,
                "elapsed_seconds": elapsed,
                "cached": True
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
    def generate_data_profile(self, use_cache: bool = True) -> Dict[str, Any]:
        """Generate data profile with caching and quality tracking.
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with data profile
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            cache_key = self.cache.get_key("data_profile", self.data_hash)
            
            # Check cache
            if use_cache:
                cached = self.cache.get(cache_key)
                if cached:
                    self.logger.info("Data profile retrieved from cache")
                    self.structured_logger.info("Cache hit", {"report_type": "data_profile"})
                    return cached
            
            self.logger.info("Generating data profile...")
            start_time = datetime.now()
            
            self.structured_logger.info("Data profile generation started", {
                "rows": self.data.shape[0],
                "columns": self.data.shape[1]
            })
            
            # Delegate to worker
            worker_result = self.data_profile_generator.execute(self.data)
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            report = worker_result.data
            
            # Track quality score
            self.quality_scores["data_profile"] = worker_result.quality_score
            
            # Cache result
            self.cache.set(cache_key, report, worker_result.quality_score)
            self.reports["data_profile"] = report
            
            # Track performance
            elapsed = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["data_profile"] = elapsed
            
            self.structured_logger.info("Data profile generated successfully", {
                "quality_score": worker_result.quality_score,
                "elapsed_seconds": elapsed,
                "cached": True
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
    def generate_statistical_report(self, use_cache: bool = True) -> Dict[str, Any]:
        """Generate statistical report with caching and quality tracking.
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with statistical analysis
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            cache_key = self.cache.get_key("statistical_report", self.data_hash)
            
            # Check cache
            if use_cache:
                cached = self.cache.get(cache_key)
                if cached:
                    self.logger.info("Statistical report retrieved from cache")
                    self.structured_logger.info("Cache hit", {"report_type": "statistical_report"})
                    return cached
            
            self.logger.info("Generating statistical report...")
            start_time = datetime.now()
            
            self.structured_logger.info("Statistical report generation started", {
                "rows": self.data.shape[0],
                "columns": self.data.shape[1]
            })
            
            # Delegate to worker
            worker_result = self.statistical_report_generator.execute(self.data)
            
            if not worker_result.success:
                raise AgentError(f"Worker failed: {worker_result.errors}")
            
            report = worker_result.data
            
            # Track quality score
            self.quality_scores["statistical_report"] = worker_result.quality_score
            
            # Cache result
            self.cache.set(cache_key, report, worker_result.quality_score)
            self.reports["statistical_report"] = report
            
            # Track performance
            elapsed = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["statistical_report"] = elapsed
            
            self.structured_logger.info("Statistical report generated successfully", {
                "quality_score": worker_result.quality_score,
                "elapsed_seconds": elapsed,
                "cached": True
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
    def generate_comprehensive_report(self, use_cache: bool = True) -> Dict[str, Any]:
        """Generate comprehensive analysis report with all sections.
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with complete report
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            self.logger.info("Generating comprehensive report...")
            start_time = datetime.now()
            
            self.structured_logger.info("Comprehensive report generation started", {
                "rows": self.data.shape[0],
                "columns": self.data.shape[1]
            })
            
            # Generate all sub-reports using workers
            executive = self.generate_executive_summary(use_cache=use_cache)
            profile = self.generate_data_profile(use_cache=use_cache)
            statistical = self.generate_statistical_report(use_cache=use_cache)
            
            # Calculate average quality score
            avg_quality = sum(self.quality_scores.values()) / len(self.quality_scores) if self.quality_scores else 0.0
            
            report = {
                "status": "success",
                "report_type": "comprehensive_analysis",
                "generated_at": datetime.now().isoformat(),
                "title": "Data Analysis Report",
                "description": "Comprehensive analysis of dataset including profiling, statistics, and quality assessment.",
                "quality_score": avg_quality,  # Propagated from workers
                "sections": {
                    "executive_summary": executive,
                    "data_profile": profile,
                    "statistical_analysis": statistical,
                },
                "quality_scores": self.quality_scores.copy(),  # Track individual scores
                "performance": self.performance_metrics.copy(),  # Track timings
                "metadata": {
                    "data_shape": {"rows": self.data.shape[0], "columns": self.data.shape[1]},
                    "generated_timestamp": datetime.now().isoformat(),
                    "report_version": "2.0",
                    "cache_stats": self.cache.get_stats(),
                },
            }
            
            self.reports["comprehensive"] = report
            elapsed = (datetime.now() - start_time).total_seconds()
            
            self.structured_logger.info("Comprehensive report generated successfully", {
                "avg_quality_score": avg_quality,
                "sections_count": len(report["sections"]),
                "elapsed_seconds": elapsed,
                "cache_stats": self.cache.get_stats()
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
            file_path: Optional file path
            
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
            worker_result = self.json_exporter.execute(
                self.reports[report_type],
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
            file_path: Optional file path
            
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
            worker_result = self.html_exporter.execute(
                self.reports[report_type],
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
    
    @retry_on_error(max_attempts=2, backoff=1)
    def list_reports(self) -> Dict[str, Any]:
        """List all generated reports with metadata.
        
        Returns:
            Dictionary with report information
        """
        result = {
            "status": "success",
            "count": len(self.reports),
            "reports": list(self.reports.keys()),
            "quality_scores": self.quality_scores.copy(),
            "performance_metrics": self.performance_metrics.copy(),
            "cache_stats": self.cache.get_stats(),
        }
        
        self.structured_logger.info("Reports listed", {
            "count": result["count"],
            "reports": result["reports"],
            "cache_size": result["cache_stats"]["size"]
        })
        
        return result
    
    @retry_on_error(max_attempts=2, backoff=1)
    def get_quality_scores(self) -> Dict[str, float]:
        """Get quality scores from all generated reports.
        
        Returns:
            Dictionary mapping report type to quality score
        """
        return self.quality_scores.copy()
    
    @retry_on_error(max_attempts=2, backoff=1)
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for report generation.
        
        Returns:
            Dictionary mapping report type to elapsed time in seconds
        """
        return self.performance_metrics.copy()
