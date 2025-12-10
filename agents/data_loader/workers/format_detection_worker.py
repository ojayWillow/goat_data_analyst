"""Format Detection Worker - Auto-detects file format using magic bytes."""

from pathlib import Path

from agents.data_loader.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class FormatDetectionWorker(BaseWorker):
    """Worker that detects file format using magic bytes."""
    
    def __init__(self):
        """Initialize FormatDetectionWorker."""
        super().__init__("FormatDetectionWorker")
    
    def execute(self, file_path: str = None, **kwargs) -> WorkerResult:
        """Detect file format.
        
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
            detected_format = self._detect_by_magic_bytes(file_path)
            
            result.data = {
                "file_path": str(file_path),
                "detected_format": detected_format,
                "extension": file_path.suffix.lower(),
                "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2)
            }
            
            logger.info(f"Format detected: {detected_format} for {file_path.name}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Format detection failed: {e}")
            result.success = False
            return result
    
    def _detect_by_magic_bytes(self, file_path: Path) -> str:
        """Detect format by reading magic bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            Format string ('csv', 'json', 'parquet', 'excel', 'sqlite', etc.)
        """
        with open(file_path, 'rb') as f:
            magic = f.read(8)
        
        # Parquet: PAR1
        if magic.startswith(b'PAR1'):
            return 'parquet'
        
        # JSON: { or [
        if magic.startswith((b'{', b'[')):
            return 'json'
        
        # Excel: PK (ZIP format)
        if magic.startswith(b'PK'):
            return 'excel'
        
        # SQLite: SQLite format 3
        if magic.startswith(b'SQLite format 3'):
            return 'sqlite'
        
        # CSV (text-based)
        try:
            text = magic.decode('utf-8', errors='ignore')
            if any(c in text for c in [',', '\t', '|']):
                return 'csv'
        except:
            pass
        
        # Default to CSV
        return 'csv'
