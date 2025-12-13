"""JSONExporter - Exports reports to JSON format.

Enhanced with:
- File writing capability
- File validation
- Compression option
- Pretty-print option
- Error handling
"""

import json
import os
import gzip
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from pathlib import Path
from .base_worker import BaseWorker, WorkerResult, ErrorType, ValidationUtils
from agents.error_intelligence.main import ErrorIntelligence


class JSONExporter(BaseWorker):
    """Exports reports to JSON format with file writing.
    
    Capabilities:
    - Convert report data to JSON
    - Write to file system
    - Optional gzip compression
    - File validation
    - Comprehensive error handling
    """
    
    # Constants
    DEFAULT_OUTPUT_DIR = "reports"
    MAX_FILE_SIZE_MB = 100
    
    def __init__(self):
        super().__init__("json_exporter")
        self._ensure_output_dir()
    
    def execute(
        self,
        report_data: Dict[str, Any],
        file_path: Optional[str] = None,
        compress: bool = False,
        write_to_disk: bool = True,
        pretty_print: bool = True,
        **kwargs
    ) -> WorkerResult:
        """Export report to JSON format.
        
        Args:
            report_data: Report data to export
            file_path: Optional file path (auto-generated if None)
            compress: Whether to gzip compress the JSON
            write_to_disk: Whether to write file to disk
            pretty_print: Whether to pretty-print JSON (with indent)
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
            # Validate input
            if not report_data or not isinstance(report_data, dict):
                self._add_error(
                    result,
                    ErrorType.DATA_VALIDATION_ERROR,
                    "Report data must be a non-empty dictionary",
                    severity="error",
                    suggestion="Ensure report_data is a valid dictionary"
                )
                result.success = False
                return result
            
            # Convert to JSON
            indent = 2 if pretty_print else None
            json_str = json.dumps(report_data, indent=indent, default=str)
            
            # Check file size
            file_size_mb = len(json_str.encode('utf-8')) / (1024 * 1024)
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                self._add_warning(
                    result,
                    f"JSON file size ({file_size_mb:.1f}MB) exceeds recommended max ({self.MAX_FILE_SIZE_MB}MB)"
                )
            
            # Determine file path
            if file_path is None:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                file_ext = ".json.gz" if compress else ".json"
                file_path = f"{self.DEFAULT_OUTPUT_DIR}/report_{timestamp}{file_ext}"
            else:
                # Add compression extension if needed
                if compress and not file_path.endswith('.gz'):
                    file_path = file_path + '.gz'
            
            # Write to disk if requested
            write_path = None
            if write_to_disk:
                write_path = self._write_to_disk(
                    json_str,
                    file_path,
                    compress,
                    result
                )
                if not write_path:
                    # Error already added in _write_to_disk
                    result.success = False
                    return result
            
            result.data = {
                "status": "success",
                "json": json_str[:1000] if len(json_str) > 1000 else json_str,  # First 1000 chars
                "json_size": len(json_str),
                "file_size_mb": round(file_size_mb, 2),
                "file_path": write_path or file_path,
                "compressed": compress,
                "written_to_disk": write_to_disk and write_path is not None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            result.quality_score = 0.95
            
            self.logger.info(f"JSON export completed: {write_path or file_path}")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Export failed: {str(e)}",
                severity="error",
                details={"exception_type": type(e).__name__}
            )
            result.success = False
        
        return result
    
    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        try:
            Path(self.DEFAULT_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Output directory ready: {self.DEFAULT_OUTPUT_DIR}")
        except Exception as e:
            self.logger.warning(f"Could not create output directory: {e}")
    
    def _write_to_disk(
        self,
        json_str: str,
        file_path: str,
        compress: bool,
        result: WorkerResult
    ) -> Optional[str]:
        """Write JSON to disk with error handling.
        
        Args:
            json_str: JSON string to write
            file_path: Path where to write
            compress: Whether to compress
            result: WorkerResult to add errors to
            
        Returns:
            Path written to, or None if failed
        """
        try:
            # Ensure directory exists
            output_dir = os.path.dirname(file_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Convert to absolute path
            abs_path = os.path.abspath(file_path)
            
            # Write file
            if compress:
                with gzip.open(abs_path, 'wt', encoding='utf-8') as f:
                    f.write(json_str)
            else:
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
            
            # Verify file was written
            if not os.path.exists(abs_path):
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    f"File verification failed: {abs_path}",
                    severity="error"
                )
                return None
            
            file_size = os.path.getsize(abs_path) / 1024  # KB
            self.logger.info(f"JSON file written: {abs_path} ({file_size:.1f} KB)")
            
            return abs_path
        
        except IOError as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Failed to write file: {str(e)}",
                severity="error",
                suggestion="Check directory permissions and available disk space"
            )
            return None
        except Exception as e:
            self._add_error(
                result,
                ErrorType.UNKNOWN_ERROR,
                f"Unexpected error writing file: {str(e)}",
                severity="error"
            )
            return None
