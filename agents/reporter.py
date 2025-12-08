"""Reporter Agent - Report generation and export.

Generates comprehensive data analysis reports in multiple formats.
Includes summary statistics, charts, insights, and recommendations.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

from core.logger import get_logger
from core.exceptions import AgentError

logger = get_logger(__name__)


class Reporter:
    """Agent for report generation.
    
    Capabilities:
    - Executive summaries
    - Data profiling reports
    - Statistical analysis reports
    - Anomaly reports
    - Trend analysis reports
    - JSON export
    - HTML export
    - CSV export
    - Report templates
    """
    
    def __init__(self):
        """Initialize Reporter agent."""
        self.name = "Reporter"
        self.data = None
        self.reports = {}
        logger.info(f"{self.name} initialized")
    
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
        """Generate executive summary report.
        
        Returns:
            Dictionary with summary information
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Generating executive summary...")
            
            rows, cols = self.data.shape
            null_pct = (self.data.isnull().sum().sum() / (rows * cols) * 100) if (rows * cols) > 0 else 0
            duplicates = self.data.duplicated().sum()
            numeric_cols = len(self.data.select_dtypes(include=[np.number]).columns)
            categorical_cols = len(self.data.select_dtypes(include=['object']).columns)
            
            # Quality rating
            if null_pct == 0 and duplicates == 0:
                quality = "Excellent"
            elif null_pct < 5 and duplicates < 1:
                quality = "Good"
            elif null_pct < 20 and duplicates < 5:
                quality = "Fair"
            else:
                quality = "Poor"
            
            summary = {
                "status": "success",
                "report_type": "executive_summary",
                "generated_at": datetime.utcnow().isoformat(),
                "dataset_info": {
                    "rows": rows,
                    "columns": cols,
                    "numeric_columns": numeric_cols,
                    "categorical_columns": categorical_cols,
                    "total_cells": rows * cols,
                },
                "data_quality": {
                    "quality_rating": quality,
                    "null_percentage": round(null_pct, 2),
                    "duplicate_count": int(duplicates),
                    "duplicate_percentage": round((duplicates / rows * 100) if rows > 0 else 0, 2),
                },
                "summary_statement": f"Dataset contains {rows:,} rows and {cols} columns with {quality} data quality.",
            }
            
            self.reports["executive_summary"] = summary
            return summary
        
        except Exception as e:
            logger.error(f"Executive summary generation failed: {e}")
            raise AgentError(f"Generation failed: {e}")
    
    def generate_data_profile(self) -> Dict[str, Any]:
        """Generate detailed data profile report.
        
        Returns:
            Dictionary with data profile
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Generating data profile...")
            
            profile = {
                "status": "success",
                "report_type": "data_profile",
                "generated_at": datetime.utcnow().isoformat(),
                "columns": {},
            }
            
            for col in self.data.columns:
                dtype = str(self.data[col].dtype)
                null_count = self.data[col].isnull().sum()
                null_pct = (null_count / len(self.data) * 100) if len(self.data) > 0 else 0
                unique = self.data[col].nunique()
                
                col_info = {
                    "data_type": dtype,
                    "missing_values": int(null_count),
                    "missing_percentage": round(null_pct, 2),
                    "unique_values": unique,
                    "completeness": round(100 - null_pct, 2),
                }
                
                # Add type-specific statistics
                if self.data[col].dtype in [np.int64, np.float64, np.int32, np.float32]:
                    series = self.data[col].dropna()
                    col_info["statistics"] = {
                        "mean": float(series.mean()) if len(series) > 0 else None,
                        "median": float(series.median()) if len(series) > 0 else None,
                        "std": float(series.std()) if len(series) > 0 else None,
                        "min": float(series.min()) if len(series) > 0 else None,
                        "max": float(series.max()) if len(series) > 0 else None,
                    }
                else:
                    top_values = self.data[col].value_counts().head(3)
                    col_info["top_values"] = dict(top_values.items())
                
                profile["columns"][col] = col_info
            
            self.reports["data_profile"] = profile
            return profile
        
        except Exception as e:
            logger.error(f"Data profile generation failed: {e}")
            raise AgentError(f"Generation failed: {e}")
    
    def generate_statistical_report(self) -> Dict[str, Any]:
        """Generate statistical analysis report.
        
        Returns:
            Dictionary with statistical analysis
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Generating statistical report...")
            
            numeric_data = self.data.select_dtypes(include=[np.number])
            
            report = {
                "status": "success",
                "report_type": "statistical_analysis",
                "generated_at": datetime.utcnow().isoformat(),
                "summary_statistics": numeric_data.describe().round(2).to_dict(),
                "correlation_analysis": {},
            }
            
            # Correlation analysis
            if numeric_data.shape[1] >= 2:
                corr_matrix = numeric_data.corr()
                report["correlation_analysis"] = {
                    "matrix": corr_matrix.round(3).to_dict(),
                    "strong_correlations": [],
                }
                
                # Find strong correlations
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            report["correlation_analysis"]["strong_correlations"].append({
                                "col1": corr_matrix.columns[i],
                                "col2": corr_matrix.columns[j],
                                "correlation": float(corr_val),
                            })
            
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
            
            # Generate all sub-reports
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
        """Export report to JSON file.
        
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
            
            if file_path is None:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                file_path = f"report_{report_type}_{timestamp}.json"
            
            logger.info(f"Exporting {report_type} to JSON: {file_path}")
            
            with open(file_path, 'w') as f:
                json.dump(self.reports[report_type], f, indent=2, default=str)
            
            file_size = Path(file_path).stat().st_size
            
            return {
                "status": "success",
                "format": "JSON",
                "report_type": report_type,
                "file_path": file_path,
                "file_size": file_size,
                "message": f"Report exported successfully to {file_path}",
            }
        
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise AgentError(f"Export failed: {e}")
    
    def export_to_html(self, report_type: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Export report to HTML file.
        
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
            
            if file_path is None:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                file_path = f"report_{report_type}_{timestamp}.html"
            
            logger.info(f"Exporting {report_type} to HTML: {file_path}")
            
            report = self.reports[report_type]
            
            # Generate HTML
            html_content = self._generate_html(report)
            
            with open(file_path, 'w') as f:
                f.write(html_content)
            
            file_size = Path(file_path).stat().st_size
            
            return {
                "status": "success",
                "format": "HTML",
                "report_type": report_type,
                "file_path": file_path,
                "file_size": file_size,
                "message": f"Report exported successfully to {file_path}",
            }
        
        except Exception as e:
            logger.error(f"HTML export failed: {e}")
            raise AgentError(f"Export failed: {e}")
    
    def _generate_html(self, report: Dict[str, Any]) -> str:
        """Generate HTML content from report.
        
        Args:
            report: Report dictionary
            
        Returns:
            HTML content string
        """
        title = report.get("title", "Data Analysis Report")
        timestamp = report.get("generated_at", datetime.utcnow().isoformat())
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .metric {{
            display: inline-block;
            background: #f0f4ff;
            padding: 15px 20px;
            margin: 10px 10px 10px 0;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        .metric-label {{
            font-size: 0.9em;
            color: #666;
        }}
        .metric-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        table td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        table tr:hover {{
            background: #f5f5f5;
        }}
        .footer {{
            text-align: center;
            color: #999;
            padding: 20px;
            font-size: 0.9em;
        }}
        .status-success {{
            color: #27ae60;
        }}
        .status-warning {{
            color: #e74c3c;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Generated: {timestamp}</p>
    </div>
"""
        
        # Add sections
        if "sections" in report:
            for section_name, section_data in report["sections"].items():
                html += f'<div class="section">\n<h2>{section_name.replace("_", " ").title()}</h2>\n'
                html += self._dict_to_html(section_data)
                html += '</div>\n'
        
        html += """
    <div class="footer">
        <p>This report was generated by GOAT Data Analyst</p>
    </div>
</body>
</html>
"""
        return html
    
    def _dict_to_html(self, data: Dict[str, Any], depth: int = 0) -> str:
        """Convert dictionary to HTML representation.
        
        Args:
            data: Dictionary to convert
            depth: Recursion depth
            
        Returns:
            HTML string
        """
        html = ""
        for key, value in data.items():
            if key in ["status", "report_type", "generated_at", "columns"]:
                continue
            
            if isinstance(value, dict):
                if len(value) > 0:
                    html += f'<h3>{key.replace("_", " ").title()}</h3>\n'
                    for k, v in list(value.items())[:10]:  # Limit to 10 items
                        if isinstance(v, (int, float)):
                            html += f'<div class="metric"><div class="metric-label">{k}</div><div class="metric-value">{v}</div></div>\n'
            elif isinstance(value, (int, float)):
                html += f'<div class="metric"><div class="metric-label">{key.replace("_", " ").title()}</div><div class="metric-value">{value}</div></div>\n'
            elif isinstance(value, str):
                html += f'<p><strong>{key.replace("_", " ").title()}:</strong> {value}</p>\n'
        
        return html
    
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
