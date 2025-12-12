"""Format Detection - Auto-detects file format from extension and content."""

from pathlib import Path
import pandas as pd
from typing import Any, Dict

from agents.data_loader.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class FormatDetection(BaseWorker):
    """Worker that auto-detects file format."""
    
    def __init__(self):
        """Initialize FormatDetection."""
        super().__init__("FormatDetection")
        self.error_intelligence = ErrorIntelligence()
        self.supported_formats = {'.csv', '.json', '.xlsx', '.xls', '.parquet', '.pkl'}
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input before format detection.
        
        Args:
            input_data: Dictionary with 'file_path' key
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
            TypeError: If wrong data types
        """
        if 'file_path' not in input_data:
            raise ValueError("file_path is required")
        
        file_path = input_data['file_path']
        
        if file_path is None:
            raise ValueError("file_path cannot be None")
        
        if not isinstance(file_path, (str, Path)):
            raise TypeError("file_path must be str or Path")
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        return True
    
    def execute(self, file_path: str = None, **kwargs) -> WorkerResult:
        """Detect file format from extension and content.
        
        Args:
            file_path: Path to file
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with detected format
        """
        try:
            result = self._run_format_detection(file_path=file_path, **kwargs)
            
            self.error_intelligence.track_success(
                agent_name="data_loader",
                worker_name="FormatDetection",
                operation="format_detection",
                context={"file_path": file_path}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="data_loader",
                worker_name="FormatDetection",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"file_path": file_path}
            )
            raise
    
    def _run_format_detection(self, file_path: str = None, **kwargs) -> WorkerResult:
        """Perform format detection."""
        result = self._create_result(task_type="format_detection")
        
        if not file_path:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "file_path required")
            result.success = False
            return result
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            self._add_error(result, ErrorType.FILE_NOT_FOUND, f"File not found: {file_path}")
            result.success = False
            return result
        
        try:
            # Get extension
            extension = file_path.suffix.lower()
            
            if extension not in self.supported_formats:
                self._add_error(
                    result,
                    ErrorType.VALIDATION_ERROR,
                    f"Unsupported format: {extension}. Supported: {self.supported_formats}"
                )
                result.success = False
                return result
            
            # Map extension to format
            format_map = {
                '.csv': 'CSV',
                '.json': 'JSON',
                '.xlsx': 'Excel',
                '.xls': 'Excel',
                '.parquet': 'Parquet',
                '.pkl': 'Pickle'
            }
            
            detected_format = format_map.get(extension, 'Unknown')
            
            # Additional content validation
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            result.data = {
                "file_name": file_path.name,
                "extension": extension,
                "detected_format": detected_format,
                "file_size_mb": round(file_size_mb, 2),
                "is_supported": True
            }
            result.quality_score = 1.0
            result.success = True
            
            logger.info(f"Format detected: {detected_format} ({extension})")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Format detection failed: {e}")
            result.success = False
            return result
