"""JSONExporter - Exports reports to JSON format."""

import json
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from .base_worker import BaseWorker, WorkerResult, ErrorType
from agents.error_intelligence.main import ErrorIntelligence


class JSONExporter(BaseWorker):
    """Exports reports to JSON format."""
    
    def __init__(self):
        super().__init__("json_exporter")
    
    def execute(self, report_data: Dict[str, Any], file_path: Optional[str] = None, **kwargs) -> WorkerResult:
        """Export report to JSON.
        
        Args:
            report_data: Report data to export
            file_path: Optional file path to save to
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with export information
        """
        result = self._create_result(
            success=True,
            task_type="json_export",
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
            
            # Convert to JSON
            json_str = json.dumps(report_data, indent=2, default=str)
            
            # Determine file path
            if file_path is None:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                file_path = f"report_{timestamp}.json"
            
            result.data = {
                "json": json_str,
                "file_path": file_path,
                "file_size": len(json_str),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            self.logger.info(f"JSON export generated: {file_path}")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Export failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
