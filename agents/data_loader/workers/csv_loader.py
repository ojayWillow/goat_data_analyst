"""CSV Loader Worker - Handles CSV file loading."""

import pandas as pd
from pathlib import Path
from typing import Any, Dict

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class CSVLoaderWorker(BaseWorker):
    """Worker that loads CSV files."""
    
    def __init__(self):
        """Initialize CSVLoaderWorker."""
        super().__init__("CSVLoaderWorker")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute CSV loading.
        
        Args:
            file_path: Path to CSV file
            **kwargs: Additional pandas read_csv arguments
            
        Returns:
            WorkerResult with loaded data
        """
        return self.safe_execute(**kwargs)
    
    def execute(self, **kwargs) -> WorkerResult:
        """Actual implementation of CSV loading."""
        file_path = kwargs.get('file_path')
        
        result = self._create_result(task_type="csv_loading")
        
        # Validate file path
        if not file_path:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "No file path provided")
            result.success = False
            return result
        
        file_path = Path(file_path)
        
        # Check file exists
        if not file_path.exists():
            self._add_error(result, ErrorType.FILE_NOT_FOUND, f"File not found: {file_path}")
            result.success = False
            return result
        
        try:
            # Load CSV with low_memory=False to avoid warnings
            df = pd.read_csv(file_path, low_memory=False)
            
            if df.empty:
                self._add_error(result, ErrorType.EMPTY_DATA, "CSV file is empty")
                result.success = False
                return result
            
            result.data = df
            result.metadata = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "file_size_mb": file_path.stat().st_size / (1024 * 1024),
            }
            
            logger.info(f"CSV loaded: {len(df)} rows, {len(df.columns)} columns")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Failed to load CSV: {e}")
            result.success = False
            return result
