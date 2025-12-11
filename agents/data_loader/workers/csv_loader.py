"""CSV Loader Worker - Handles CSV file loading with robust error handling."""

import pandas as pd
from pathlib import Path
from typing import Any, Dict

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class CSVLoaderWorker(BaseWorker):
    """Worker that loads CSV files with robust error handling."""
    
    def __init__(self):
        """Initialize CSVLoaderWorker."""
        super().__init__("CSVLoaderWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute CSV loading with robust error handling.
        
        Args:
            file_path: Path to CSV file
            **kwargs: Additional pandas read_csv arguments
            
        Returns:
            WorkerResult with loaded data
        """
        try:
            result = self._run_csv_load(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="data_loader",
                worker_name="CSVLoaderWorker",
                operation="csv_loading",
                context={"file_path": kwargs.get('file_path')}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="data_loader",
                worker_name="CSVLoaderWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"file_path": kwargs.get('file_path')}
            )
            raise
    
    def _run_csv_load(self, **kwargs) -> WorkerResult:
        """Perform CSV loading."""
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
            # Load CSV with robust error handling
            # - low_memory=False to avoid DtypeWarning
            # - on_bad_lines='skip' to skip corrupt/malformed lines
            # - encoding_errors='ignore' to handle encoding issues
            df = pd.read_csv(
                file_path,
                low_memory=False,
                on_bad_lines='skip',  # Skip corrupt lines
                encoding_errors='ignore'  # Ignore encoding errors
            )
            
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
