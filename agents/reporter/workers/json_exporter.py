"""JSONExporter - Exports reports to JSON format."""

import json
from typing import Any, Dict
from pathlib import Path
from .base_worker import BaseWorker, WorkerResult, ErrorType


class JSONExporter(BaseWorker):
    """Exports reports to JSON format."""
    
    def __init__(self):
        super().__init__("json_exporter")
    
    def execute(self, report_data: Dict[str, Any], file_path: str = None, **kwargs) -> WorkerResult:
        """Export report to JSON.
        
        Args:
            report_data: Report dictionary to export
            file_path: Output file path
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
            if report_data is None or not isinstance(report_data, dict):
                self._add_error(
                    result,
                    ErrorType.DATA_VALIDATION_ERROR,
                    "Report data must be a dictionary",
                    severity="error"
                )
                return result
            
            if file_path is None:
                from datetime import datetime
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                file_path = f"report_{timestamp}.json"
            
            self.logger.info(f"Exporting to JSON: {file_path}")
            
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            file_size = Path(file_path).stat().st_size
            
            result.data = {
                "status": "success",
                "format": "JSON",
                "file_path": str(file_path),
                "file_size": file_size,
                "message": f"Report exported successfully to {file_path}",
            }
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Export failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
