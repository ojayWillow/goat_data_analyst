"""Parquet Loader Worker - Handles Parquet file loading."""

import pandas as pd
from pathlib import Path
from typing import Any, Dict

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class ParquetLoaderWorker(BaseWorker):
    """Worker that loads Parquet files."""
    
    def __init__(self):
        """Initialize ParquetLoaderWorker."""
        super().__init__("ParquetLoaderWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute Parquet loading.
        
        Args:
            file_path: Path to Parquet file
            **kwargs: Additional pandas read_parquet arguments
            
        Returns:
            WorkerResult with loaded data
        """
        try:
            result = self._run_parquet_load(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="data_loader",
                worker_name="ParquetLoaderWorker",
                operation="parquet_loading",
                context={"file_path": kwargs.get('file_path')}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="data_loader",
                worker_name="ParquetLoaderWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"file_path": kwargs.get('file_path')}
            )
            raise
    
    def _run_parquet_load(self, **kwargs) -> WorkerResult:
        """Perform Parquet loading."""
        file_path = kwargs.get('file_path')
        
        result = self._create_result(task_type="parquet_loading")
        
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
            # Load Parquet
            df = pd.read_parquet(file_path)
            
            if df.empty:
                self._add_error(result, ErrorType.EMPTY_DATA, "Parquet file is empty")
                result.success = False
                return result
            
            result.data = df
            result.metadata = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "file_size_mb": file_path.stat().st_size / (1024 * 1024),
            }
            
            logger.info(f"Parquet loaded: {len(df)} rows, {len(df.columns)} columns")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Failed to load Parquet: {e}")
            result.success = False
            return result
