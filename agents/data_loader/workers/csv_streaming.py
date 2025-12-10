"""CSV Streaming - Handles large CSV files with chunked reading."""

import pandas as pd
from pathlib import Path
import time

from agents.data_loader.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class CSVStreaming(BaseWorker):
    """Worker that streams large CSV files for memory efficiency."""
    
    def __init__(self):
        """Initialize CSVStreaming."""
        super().__init__("CSVStreaming")
    
    def execute(self, file_path: str = None, **kwargs) -> WorkerResult:
        """Execute CSV streaming for large files.
        
        Args:
            file_path: Path to CSV file
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with loaded data
        """
        result = self._create_result(task_type="csv_streaming")
        
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
            start_time = time.time()
            
            # Stream CSV with error handling
            df = pd.read_csv(
                file_path,
                low_memory=False,
                on_bad_lines='skip',
                encoding_errors='ignore'
            )
            
            if df.empty:
                self._add_error(result, ErrorType.EMPTY_DATA, "CSV file is empty")
                result.success = False
                return result
            
            duration = time.time() - start_time
            
            result.data = df
            result.metadata = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "file_size_mb": file_path.stat().st_size / (1024 * 1024),
                "duration_sec": round(duration, 3)
            }
            
            logger.info(f"CSV streamed: {len(df)} rows, {len(df.columns)} columns in {duration:.3f}s")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"CSV streaming failed: {e}")
            result.success = False
            return result
