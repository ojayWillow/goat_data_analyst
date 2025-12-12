"""Validator Worker - Validates data and extracts metadata with A+ standards.

Handles:
- Data validation and quality checks
- Comprehensive metadata extraction
- Null value detection and tracking
- Duplicate detection
- Data type analysis
- Quality score calculation
"""

import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional
import time

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# ===== CONSTANTS =====
MAX_FILE_SIZE_MB = 100
QUALITY_THRESHOLD = 0.8
MAX_NULL_PERCENTAGE = 90.0


class ValidatorWorker(BaseWorker):
    """Worker that validates data and extracts comprehensive metadata.
    
    Validates:
    - DataFrame type and structure
    - Data quality (nulls, duplicates)
    - Column data types
    - Row and column counts
    - Memory usage
    
    Returns:
    - Validation status
    - Comprehensive metadata
    - Quality score (0-1)
    - Detailed quality metrics
    
    Input Format:
        {
            'df': pd.DataFrame (required),
            'file_path': str (optional),
            'file_format': str (optional)
        }
    
    Output Format:
        WorkerResult with:
        - success: bool
        - data: DataFrame or None
        - quality_score: 0-1 metric
        - metadata: Dict with comprehensive info
        - errors: List of validation errors
    
    Example:
        >>> worker = ValidatorWorker()
        >>> result = worker.safe_execute(
        ...     df=my_dataframe,
        ...     file_path='data.csv',
        ...     file_format='csv'
        ... )
        >>> print(f"Valid: {result.success}")
        >>> print(f"Quality: {result.quality_score}")
    """
    
    def __init__(self) -> None:
        """Initialize ValidatorWorker."""
        super().__init__("ValidatorWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input meets all requirements.
        
        Checks:
        - df is a DataFrame
        - df is not None
        - df has rows and columns
        
        Args:
            input_data: Dictionary with 'df' key
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If DataFrame invalid
            TypeError: If wrong type
        """
        df = input_data.get('df')
        
        if df is None:
            raise ValueError("DataFrame is None")
        
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected DataFrame, got {type(df)}")
        
        if len(df) == 0:
            raise ValueError("DataFrame is empty (0 rows)")
        
        if len(df.columns) == 0:
            raise ValueError("DataFrame has no columns")
        
        return True
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute validation and metadata extraction.
        
        Args:
            df: DataFrame to validate (required)
            file_path: Path to source file (optional)
            file_format: File format (optional)
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with validation results and metadata
        """
        start_time = time.time()
        try:
            # Validate input
            self.validate_input({'df': kwargs.get('df')})
            
            result = self._run_validation(**kwargs)
            
            # Track success
            self.error_intelligence.track_success(
                agent_name="data_loader",
                worker_name="ValidatorWorker",
                operation="validation",
                context={
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
                worker_name="ValidatorWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"file_format": kwargs.get('file_format')}
            )
            
            duration_ms = (time.time() - start_time) * 1000
            return WorkerResult(
                worker=self.name,
                task_type="validation",
                success=False,
                data=None,
                errors=[{"type": ErrorType.VALIDATION_ERROR.value, "message": str(e)}],
                execution_time_ms=duration_ms,
                quality_score=0.0,
            )
    
    def _run_validation(self, **kwargs) -> WorkerResult:
        """Perform validation operation.
        
        Args:
            **kwargs: Validation parameters
            
        Returns:
            WorkerResult with validation details
        """
        df = kwargs.get('df')
        file_path = kwargs.get('file_path')
        file_format = kwargs.get('file_format', 'unknown')
        
        result = self._create_result(task_type="validation")
        
        try:
            # Extract metadata
            metadata = self._extract_metadata(df, file_path, file_format)
            
            # Check data quality
            quality_info = self._check_data_quality(df)
            
            # Add warnings for quality issues
            for issue in quality_info['issues']:
                self._add_warning(result, issue)
            
            # Calculate quality score
            quality_score = self._calculate_quality_from_metrics(quality_info)
            
            # Set results
            result.data = df
            result.metadata = {**metadata, **quality_info}
            result.quality_score = quality_score
            result.rows_processed = len(df)
            result.success = quality_info['valid']
            
            logger.info(
                f"Validation completed: {len(df)} rows, "
                f"{len(df.columns)} columns, quality={quality_score:.2f}"
            )
            return result
        
        except Exception as e:
            self._add_error(
                result,
                ErrorType.VALIDATION_ERROR,
                str(e)
            )
            result.success = False
            logger.error(f"Validation failed: {e}", exc_info=True)
            return result
    
    def _extract_metadata(self, df: pd.DataFrame, file_path: Any, file_format: str) -> Dict[str, Any]:
        """Extract comprehensive metadata.
        
        Args:
            df: DataFrame to analyze
            file_path: Path to source file
            file_format: Format of source file
            
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
            except Exception:
                pass
        
        # Memory usage
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        # Column info
        columns_info = {}
        for col in df.columns:
            null_count = int(df[col].isna().sum())
            null_pct = (null_count / len(df) * 100) if len(df) > 0 else 0.0
            
            columns_info[col] = {
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].notna().sum()),
                "null_count": null_count,
                "null_percentage": round(null_pct, 2),
                "unique_values": int(df[col].nunique()),
                "unique_percentage": round((df[col].nunique() / len(df) * 100), 2) if len(df) > 0 else 0.0,
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
        }
    
    def _check_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check comprehensive data quality.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Quality metrics dictionary
        """
        if df is None or df.empty:
            return {
                "valid": False,
                "null_count": 0,
                "null_pct": 100.0,
                "duplicates": 0,
                "duplicate_pct": 0.0,
                "issues": ["DataFrame is empty"]
            }
        
        # Null analysis
        total_cells = len(df) * len(df.columns)
        null_count = int(df.isna().sum().sum())
        null_pct = (null_count / total_cells * 100) if total_cells > 0 else 0.0
        
        # Duplicate analysis
        dup_count = int(df.duplicated().sum())
        dup_pct = (dup_count / len(df) * 100) if len(df) > 0 else 0.0
        
        # Issue detection
        issues = []
        if null_pct > MAX_NULL_PERCENTAGE:
            issues.append(f"High null percentage: {null_pct:.1f}%")
        if dup_pct > 50:
            issues.append(f"High duplicate percentage: {dup_pct:.1f}%")
        if null_pct > 25:
            issues.append(f"Moderate null values: {null_pct:.1f}%")
        
        return {
            "valid": len(issues) == 0,
            "null_count": null_count,
            "null_pct": round(null_pct, 2),
            "duplicates": dup_count,
            "duplicate_pct": round(dup_pct, 2),
            "issues": issues
        }
    
    def _calculate_quality_from_metrics(self, quality_info: Dict[str, Any]) -> float:
        """Calculate quality score from quality metrics.
        
        Formula considers:
        - Null percentage (40% weight)
        - Duplicate percentage (30% weight)
        - Overall validity (30% weight)
        
        Args:
            quality_info: Quality metrics dictionary
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        if not quality_info['valid']:
            # Invalid data = lower score
            base_score = 0.5
        else:
            base_score = 1.0
        
        # Penalize for nulls (40% weight)
        null_penalty = (quality_info['null_pct'] / 100.0) * 0.4
        
        # Penalize for duplicates (30% weight)
        dup_penalty = (quality_info['duplicate_pct'] / 100.0) * 0.3
        
        # Calculate final score
        score = base_score - null_penalty - dup_penalty
        score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
        
        return round(score, 2)
