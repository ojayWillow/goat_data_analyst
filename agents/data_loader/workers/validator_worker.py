"""Validator Worker - Validates and extracts metadata from loaded data."""

import pandas as pd
from pathlib import Path
from typing import Any, Dict, List

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class ValidatorWorker(BaseWorker):
    """Worker that validates data and extracts metadata."""
    
    MAX_FILE_SIZE_MB = 100
    
    def __init__(self):
        """Initialize ValidatorWorker."""
        super().__init__("ValidatorWorker")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute validation and metadata extraction.
        
        Args:
            file_path: Path to file
            df: DataFrame to validate
            file_format: File format
            
        Returns:
            WorkerResult with metadata
        """
        return self.safe_execute(**kwargs)
    
    def execute(self, **kwargs) -> WorkerResult:
        """Actual implementation of validation."""
        df = kwargs.get('df')
        file_path = kwargs.get('file_path')
        file_format = kwargs.get('file_format', 'unknown')
        
        result = self._create_result(task_type="validation")
        
        # Validate DataFrame
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "DataFrame is None")
            result.success = False
            return result
        
        if not isinstance(df, pd.DataFrame):
            self._add_error(result, ErrorType.VALIDATION_ERROR, "Data is not a DataFrame")
            result.success = False
            return result
        
        if df.empty:
            self._add_error(result, ErrorType.EMPTY_DATA, "DataFrame is empty")
            result.success = False
            return result
        
        try:
            # Extract metadata
            metadata = self._extract_metadata(df, file_path, file_format)
            
            result.data = df
            result.metadata = metadata
            
            logger.info(f"Validation passed: {len(df)} rows, {len(df.columns)} columns")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.VALIDATION_ERROR, str(e))
            result.success = False
            return result
    
    def _extract_metadata(self, df: pd.DataFrame, file_path: Any, file_format: str) -> Dict[str, Any]:
        """Extract comprehensive metadata.
        
        Args:
            df: DataFrame
            file_path: File path
            file_format: File format
            
        Returns:
            Metadata dictionary
        """
        # File info
        file_size_mb = 0
        file_name = "unknown"
        if file_path:
            try:
                file_path = Path(file_path)
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                file_name = file_path.name
            except:
                pass
        
        # Memory usage
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        # Column info
        columns_info = {}
        for col in df.columns:
            columns_info[col] = {
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].notna().sum()),
                "null_count": int(df[col].isna().sum()),
                "null_percentage": round(float(df[col].isna().sum() / len(df) * 100), 2) if len(df) > 0 else 0,
            }
        
        return {
            "file_name": file_name,
            "file_format": file_format,
            "file_size_mb": round(file_size_mb, 2),
            "rows": df.shape[0],
            "columns": df.shape[1],
            "column_names": df.columns.tolist(),
            "memory_usage_mb": round(memory_mb, 2),
            "columns_info": columns_info,
            "duplicates": int(df.duplicated().sum()),
            "duplicate_percentage": round(float(df.duplicated().sum() / len(df) * 100), 2) if len(df) > 0 else 0,
        }
