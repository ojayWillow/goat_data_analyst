"""HTMLExporter - Exports reports to HTML format."""

import pandas as pd
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from .base_worker import BaseWorker, WorkerResult, ErrorType
from agents.error_intelligence.main import ErrorIntelligence


class HTMLExporter(BaseWorker):
    """Exports reports to HTML format."""
    
    def __init__(self):
        super().__init__("html_exporter")
    
    def execute(self, report_data: Dict[str, Any], file_path: Optional[str] = None, **kwargs) -> WorkerResult:
        """Export report to HTML.
        
        Args:
            report_data: Report data to export
            file_path: Optional file path to save to
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with export information
        """
        result = self._create_result(
            success=True,
            task_type="html_export",
            data={}
        )
        
        try:
            if not report_data:
                self._add_error(
                    result,
                    ErrorType.DATA_VALIDATION_ERROR,
                    "Report data is empty",
                    severity="error"
                )
                return result
            
            # Generate HTML
            html_content = self._generate_html(report_data)
            
            # Determine file path
            if file_path is None:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                file_path = f"report_{timestamp}.html"
            
            result.data = {
                "html": html_content,
                "file_path": file_path,
                "file_size": len(html_content),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            self.logger.info(f"HTML export generated: {file_path}")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Export failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
    
    def _generate_html(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML from report data."""
        html = "<html><head><title>Data Analysis Report</title></head><body>"
        html += "<h1>Data Analysis Report</h1>"
        html += f"<p>Generated: {datetime.now(timezone.utc).isoformat()}</p>"
        
        # Add content based on report structure
        for key, value in report_data.items():
            if isinstance(value, dict):
                html += f"<h2>{key.replace('_', ' ').title()}</h2>"
                html += self._dict_to_html(value)
            elif isinstance(value, str):
                html += f"<p><strong>{key}:</strong> {value}</p>"
        
        html += "</body></html>"
        return html
    
    def _dict_to_html(self, data: Dict[str, Any], depth: int = 0) -> str:
        """Convert dictionary to HTML table."""
        if not data:
            return ""
        
        html = "<table border='1'>"
        for key, value in data.items():
            html += "<tr>"
            html += f"<td><strong>{key}</strong></td>"
            if isinstance(value, dict):
                html += f"<td>{self._dict_to_html(value, depth+1)}</td>"
            else:
                html += f"<td>{value}</td>"
            html += "</tr>"
        html += "</table>"
        return html
