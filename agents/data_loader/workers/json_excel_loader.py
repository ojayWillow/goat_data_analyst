"""JSON & Excel Loader Worker - Loads JSON/Excel files with A+ standards.

Handles:
- JSON file loading
- Excel file loading (.xlsx, .xls)
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
SUPPORTED_FORMATS = ['json', 'xlsx', 'xls']


class JSONExcelLoaderWorker(BaseWorker):
    """Worker that loads JSON and Excel files.
    
    Capabilities:
    - Load JSON files (flat and nested structures)
    - Load Excel files (.xlsx and .xls)
    - Extract comprehensive metadata
    - Track data quality metrics
    - Provide quality score (0-1)
    - Handle loading errors gracefully
    
    Input Format:
        {
            'file_path': str (required),
            'file_format': str ('json', 'xlsx', 'xls') (required),
            'sheet_name': str (optional, for Excel)
        }
    
    Output Format:
        WorkerResult with:
        - success: bool
        - data: DataFrame or None
        - quality_score: 0-1 metric
        - rows_processed: int
        - rows_failed: int
        - data_loss_pct: float
        - metadata: Dict with file info
        - errors: List of errors encountered
    
    Example:
        >>> worker = JSONExcelLoaderWorker()
        >>> result = worker.safe_execute(
        ...     file_path='data.xlsx',
        ...     file_format='xlsx'
        ... )
        >>> print(f"Quality: {result.quality_score}")
        >>> print(f"Rows: {result.rows_processed}")
    """
    
    def __init__(self) -> None:
        """Initialize JSONExcelLoaderWorker."""
        super().__init__("JSONExcelLoaderWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input meets all requirements.
        
        Checks:
        - file_path exists and is accessible
        - file_format is supported (json, xlsx, xls)
        - File extension matches format
        - File is not too large (>100MB)
        
        Args:
            input_data: Dictionary with 'file_path' and 'file_format' keys
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If file path or format is invalid
            TypeError: If wrong data types
        """
        file_path = input_data.get('file_path')
        file_format = input_data.get('file_format', '').lower()
        
        if not file_path:
            raise ValueError("file_path is required")
        
        if not file_format:
            raise ValueError("file_format is required")
        
        if file_format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {file_format}. "
                f"Supported: {SUPPORTED_FORMATS}"
            )
        
        if not isinstance(file_path, (str, Path)):
            raise TypeError(f"file_path must be str or Path, got {type(file_path)}")
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        # Validate extension matches format
        ext = file_path.suffix.lower().lstrip('.')
        if ext != file_format and not (file_format in ['xls', 'xlsx'] and ext in ['xls', 'xlsx']):
            raise ValueError(
                f"File extension '{ext}' does not match format '{file_format}'"
            )
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 100:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB (max: 100MB)")
        
        return True
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute JSON/Excel loading with robust error handling.
        
        Args:
            file_path: Path to file (required)
            file_format: 'json', 'xlsx', or 'xls' (required)
            sheet_name: Sheet name for Excel files (optional)
            **kwargs: Additional pandas arguments
            
        Returns:
            WorkerResult with loaded data and quality metrics
        """
        start_time = time.time()
        try:
            # Validate input
            self.validate_input({
                'file_path': kwargs.get('file_path'),
                'file_format': kwargs.get('file_format')
            })
            
            result = self._run_json_excel_load(**kwargs)
            
            # Track success
            self.error_intelligence.track_success(
                agent_name="data_loader",
                worker_name="JSONExcelLoaderWorker",
                operation="json_excel_loading",
                context={
                    "file_path": kwargs.get('file_path'),
                    "file_format": kwargs.get('file_format'),
                    "quality_score": result.quality_score,
                    "rows": result.rows_processed
                }
            )
            
            return result
            
        except Exception as e:
            # Track error
            self.error_intelligence.track_error(
                agent_name="data_loader",
                worker_name="JSONExcelLoaderWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "file_path": kwargs.get('file_path'),
                    "file_format": kwargs.get('file_format')
                }
            )
            
            duration_ms = (time.time() - start_time) * 1000
            return WorkerResult(
                worker=self.name,
                task_type=f"{kwargs.get('file_format', 'unknown')}_loading",
                success=False,
                data=None,
                errors=[{"type": ErrorType.LOAD_ERROR.value, "message": str(e)}],
                execution_time_ms=duration_ms,
                quality_score=0.0,
            )
    
    def _run_json_excel_load(self, **kwargs) -> WorkerResult:
        """Perform JSON/Excel loading operation.
        
        Args:
            **kwargs: Parameters for loading
            
        Returns:
            WorkerResult with loaded data
        """
        file_path = kwargs.get('file_path')
        file_format = kwargs.get('file_format', '').lower()
        sheet_name = kwargs.get('sheet_name', 0)  # Default to first sheet
        
        result = self._create_result(task_type=f"{file_format}_loading")
        file_path = Path(file_path)
        
        try:
            # Load based on format
            if file_format == 'json':
                df = pd.read_json(file_path)
            elif file_format in ['xlsx', 'xls']:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                self._add_error(
                    result,
                    ErrorType.UNSUPPORTED_FORMAT,
                    f"Unsupported format: {file_format}"
                )
                result.success = False
                return result
            
            rows_loaded = len(df)
            cols_loaded = len(df.columns)
            
            # Check if empty
            if df.empty:
                self._add_error(
                    result,
                    ErrorType.EMPTY_DATA,
                    f"{file_format.upper()} file is empty"
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
                "file_format": file_format,
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
            
            # Add sheet name for Excel
            if file_format in ['xlsx', 'xls']:
                result.metadata['sheet_name'] = sheet_name
            
            result.success = True
            logger.info(
                f"{file_format.upper()} loaded successfully: {rows_loaded} rows, "
                f"{cols_loaded} columns, quality={result.quality_score:.2f}"
            )
            return result
        
        except Exception as e:
            self._add_error(
                result,
                ErrorType.LOAD_ERROR,
                f"Failed to load {file_format}: {str(e)}"
            )
            result.success = False
            logger.error(f"{file_format.upper()} loading failed: {e}", exc_info=True)
            return result
