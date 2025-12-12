"""Parquet Loader Worker - Loads Parquet files with A+ standards.

Handles:
- Parquet file loading
- Input validation
- Data quality tracking
- Comprehensive error intelligence
- Quality score calculation (0-1 range)
"""

import pandas as pd
from pathlib import Path
from typing import Any, Dict
import time

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# ===== CONSTANTS =====
MIN_ROWS_REQUIRED = 1
QUALITY_THRESHOLD = 0.8


class ParquetLoaderWorker(BaseWorker):
    """Worker that loads Parquet files with robust error handling.
    
    Capabilities:
    - Load Parquet files efficiently
    - Extract comprehensive metadata
    - Track data quality metrics
    - Provide quality score (0-1)
    - Handle loading errors gracefully
    
    Input Format:
        {
            'file_path': str (required),
            'columns': List[str] (optional)
        }
    
    Output Format:
        WorkerResult with:
        - success: bool
        - data: DataFrame or None
        - quality_score: 0-1 metric
        - rows_processed: int
        - metadata: Dict with file info
        - errors: List of errors encountered
    
    Example:
        >>> worker = ParquetLoaderWorker()
        >>> result = worker.safe_execute(file_path='data.parquet')
        >>> print(f"Quality: {result.quality_score}")
        >>> print(f"Rows: {result.rows_processed}")
    """
    
    def __init__(self) -> None:
        """Initialize ParquetLoaderWorker."""
        super().__init__("ParquetLoaderWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input meets all requirements.
        
        Checks:
        - file_path exists and is accessible
        - File has .parquet extension
        - File is not too large (>100MB)
        
        Args:
            input_data: Dictionary with 'file_path' key
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If file path is invalid
            TypeError: If wrong data types
        """
        file_path = input_data.get('file_path')
        
        if not file_path:
            raise ValueError("file_path is required")
        
        if not isinstance(file_path, (str, Path)):
            raise TypeError(f"file_path must be str or Path, got {type(file_path)}")
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.parquet':
            raise ValueError(f"File must be Parquet, got {file_path.suffix}")
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 100:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB (max: 100MB)")
        
        return True
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute Parquet loading with robust error handling.
        
        Args:
            file_path: Path to Parquet file (required)
            columns: Optional list of columns to load
            **kwargs: Additional pandas read_parquet arguments
            
        Returns:
            WorkerResult with loaded data and quality metrics
        """
        start_time = time.time()
        try:
            # Validate input
            self.validate_input({'file_path': kwargs.get('file_path')})
            
            result = self._run_parquet_load(**kwargs)
            
            # Track success
            self.error_intelligence.track_success(
                agent_name="data_loader",
                worker_name="ParquetLoaderWorker",
                operation="parquet_loading",
                context={
                    "file_path": kwargs.get('file_path'),
                    "quality_score": result.quality_score,
                    "rows": result.rows_processed
                }
            )
            
            return result
            
        except Exception as e:
            # Track error
            self.error_intelligence.track_error(
                agent_name="data_loader",
                worker_name="ParquetLoaderWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"file_path": kwargs.get('file_path')}
            )
            
            duration_ms = (time.time() - start_time) * 1000
            return WorkerResult(
                worker=self.name,
                task_type="parquet_loading",
                success=False,
                data=None,
                errors=[{"type": ErrorType.LOAD_ERROR.value, "message": str(e)}],
                execution_time_ms=duration_ms,
                quality_score=0.0,
            )
    
    def _run_parquet_load(self, **kwargs) -> WorkerResult:
        """Perform Parquet loading operation.
        
        Args:
            **kwargs: Parameters for Parquet loading
            
        Returns:
            WorkerResult with loaded data
        """
        file_path = kwargs.get('file_path')
        columns = kwargs.get('columns')  # Optional column list
        
        result = self._create_result(task_type="parquet_loading")
        file_path = Path(file_path)
        
        try:
            # Load Parquet with optional column selection
            df = pd.read_parquet(file_path, columns=columns)
            
            rows_loaded = len(df)
            cols_loaded = len(df.columns)
            
            # Check if empty
            if df.empty:
                self._add_error(
                    result,
                    ErrorType.EMPTY_DATA,
                    "Parquet file is empty"
                )
                result.success = False
                return result
            
            # Check data quality
            quality_info = self._check_data_quality(df)
            if quality_info['issues']:
                for issue in quality_info['issues']:
                    self._add_warning(result, issue)
            
            # Calculate metrics
            result.data = df
            result.rows_processed = rows_loaded
            result.rows_failed = 0  # No failed rows since we load all
            result.quality_score = self._calculate_quality_score(
                rows_loaded, 0
            )
            result.data_loss_pct = 0.0
            
            # Build metadata
            result.metadata = {
                "file_name": file_path.name,
                "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                "rows": rows_loaded,
                "columns": cols_loaded,
                "column_names": df.columns.tolist(),
                "column_dtypes": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
                "null_count": int(df.isna().sum().sum()),
                "null_pct": round(quality_info['null_pct'], 2),
                "duplicates": quality_info['duplicates'],
                "duplicate_pct": round(quality_info['duplicate_pct'], 2),
            }
            
            result.success = True
            logger.info(
                f"Parquet loaded successfully: {rows_loaded} rows, "
                f"{cols_loaded} columns, quality={result.quality_score:.2f}"
            )
            return result
        
        except Exception as e:
            self._add_error(
                result,
                ErrorType.LOAD_ERROR,
                f"Failed to load Parquet: {str(e)}"
            )
            result.success = False
            logger.error(f"Parquet loading failed: {e}", exc_info=True)
            return result
