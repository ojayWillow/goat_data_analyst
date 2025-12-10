"""Format Detection - Auto-detects file format from extension and content."""

from pathlib import Path
import pandas as pd

from agents.data_loader.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class FormatDetection(BaseWorker):
    """Worker that auto-detects file format."""
    
    def __init__(self):
        """Initialize FormatDetection."""
        super().__init__("FormatDetection")
        self.supported_formats = {'.csv', '.json', '.xlsx', '.xls', '.parquet', '.pkl'}
    
    def execute(self, file_path: str = None, **kwargs) -> WorkerResult:
        """Detect file format from extension and content.
        
        Args:
            file_path: Path to file
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with detected format
        """
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
            
            logger.info(f"Format detected: {detected_format} ({extension})")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Format detection failed: {e}")
            result.success = False
            return result
