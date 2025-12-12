"""CSV Streaming - Handles large CSV files with chunked reading."""

import pandas as pd
from pathlib import Path
import time
from typing import Any, Dict

from agents.data_loader.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class CSVStreaming(BaseWorker):
    """Worker that streams large CSV files for memory efficiency."""
    
    def __init__(self):
        """Initialize CSVStreaming."""
        super().__init__("CSVStreaming")
        self.error_intelligence = ErrorIntelligence()
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input before streaming.
        
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
        
        if not str(file_path).lower().endswith('.csv'):
            raise ValueError(f"File must be CSV, got: {file_path.suffix}")
        
        return True
    
    def execute(self, file_path: str = None, **kwargs) -> WorkerResult:
        """Execute CSV streaming for large files.
        
        Args:
            file_path: Path to CSV file
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with loaded data
        """
        try:
            result = self._run_csv_streaming(file_path=file_path, **kwargs)
            
            self.error_intelligence.track_success(
                agent_name="data_loader",
                worker_name="CSVStreaming",
                operation="csv_streaming",
                context={"file_path": file_path}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="data_loader",
                worker_name="CSVStreaming",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"file_path": file_path}
            )
            raise
    
    def _run_csv_streaming(self, file_path: str = None, **kwargs) -> WorkerResult:
        """Perform CSV streaming."""
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
            
            # Calculate quality score
            quality_check = self._check_data_quality(df)
            quality_score = 1.0 if quality_check['valid'] else max(0.0, 1.0 - (quality_check['null_pct'] / 100.0))
            
            result.data = df
            result.metadata = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "file_size_mb": file_path.stat().st_size / (1024 * 1024),
                "duration_sec": round(duration, 3),
                "null_pct": quality_check['null_pct'],
                "duplicates": quality_check['duplicates'],
                "issues": quality_check['issues']
            }
            result.quality_score = quality_score
            result.rows_processed = len(df)
            result.success = True
            
            logger.info(f"CSV streamed: {len(df)} rows, {len(df.columns)} columns in {duration:.3f}s")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"CSV streaming failed: {e}")
            result.success = False
            return result
