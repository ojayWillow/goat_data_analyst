"""Validation Utilities - Shared validation functions for all aggregator workers.

Provides consistent input validation across all workers following
AGENT_WORKER_GUIDANCE standards.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from .base_worker import WorkerError, ErrorType


# ===== CONSTANTS =====
MIN_DATA_ROWS = 1
MIN_NUMERIC_COLS = 1
MAX_NULL_PERCENTAGE = 50.0
QUALITY_THRESHOLD = 0.8


class ValidationUtils:
    """Shared validation utilities for workers."""

    @staticmethod
    def validate_dataframe(df: Any) -> Optional[WorkerError]:
        """Validate that input is a proper DataFrame.
        
        Args:
            df: Object to validate
            
        Returns:
            WorkerError if invalid, None if valid
        """
        if df is None:
            return WorkerError(
                ErrorType.MISSING_DATA,
                "DataFrame is None",
                severity="error",
                suggestion="Ensure DataFrame is provided and not None"
            )
        
        if not isinstance(df, pd.DataFrame):
            return WorkerError(
                ErrorType.TYPE_ERROR,
                f"Expected DataFrame, got {type(df).__name__}",
                severity="error",
                suggestion="Pass a pandas DataFrame"
            )
        
        if df.empty:
            return WorkerError(
                ErrorType.MISSING_DATA,
                "DataFrame is empty",
                severity="error",
                suggestion="Ensure DataFrame contains data"
            )
        
        return None

    @staticmethod
    def validate_columns_exist(
        df: pd.DataFrame,
        required_columns: List[str],
        column_name: str = "columns"
    ) -> Optional[WorkerError]:
        """Validate that all required columns exist in DataFrame.
        
        Args:
            df: DataFrame to check
            required_columns: List of column names to validate
            column_name: Name of the parameter (for error messages)
            
        Returns:
            WorkerError if columns missing, None if valid
        """
        if not required_columns:
            return None  # No columns to validate
        
        # Ensure it's a list
        if isinstance(required_columns, str):
            required_columns = [required_columns]
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            available = list(df.columns)
            return WorkerError(
                ErrorType.VALUE_ERROR,
                f"Required {column_name} not found: {missing_cols}",
                severity="error",
                details={
                    "missing_columns": missing_cols,
                    "available_columns": available,
                    "total_columns": len(available)
                },
                suggestion=f"Available columns: {available}"
            )
        
        return None

    @staticmethod
    def validate_numeric_columns(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None
    ) -> Optional[WorkerError]:
        """Validate that specified columns are numeric.
        
        Args:
            df: DataFrame to check
            columns: List of columns to validate (None = all numeric cols)
            
        Returns:
            WorkerError if non-numeric found, None if valid
        """
        if columns is None:
            # Get all numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) == 0:
                return WorkerError(
                    ErrorType.TYPE_ERROR,
                    "No numeric columns found in DataFrame",
                    severity="error",
                    suggestion="Ensure DataFrame contains numeric columns"
                )
            return None
        
        # Check specified columns
        if isinstance(columns, str):
            columns = [columns]
        
        non_numeric = []
        for col in columns:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                non_numeric.append((col, str(df[col].dtype)))
        
        if non_numeric:
            return WorkerError(
                ErrorType.TYPE_ERROR,
                f"Non-numeric columns: {[c[0] for c in non_numeric]}",
                severity="error",
                details={"non_numeric_columns": non_numeric},
                suggestion="Ensure specified columns are numeric (int, float)"
            )
        
        return None

    @staticmethod
    def validate_min_rows(
        df: pd.DataFrame,
        min_rows: int = MIN_DATA_ROWS
    ) -> Optional[WorkerError]:
        """Validate DataFrame has minimum number of rows.
        
        Args:
            df: DataFrame to check
            min_rows: Minimum required rows
            
        Returns:
            WorkerError if too few rows, None if valid
        """
        actual_rows = len(df)
        
        if actual_rows < min_rows:
            return WorkerError(
                ErrorType.MISSING_DATA,
                f"Insufficient rows: need {min_rows}, got {actual_rows}",
                severity="error",
                suggestion=f"Ensure DataFrame has at least {min_rows} rows"
            )
        
        return None

    @staticmethod
    def validate_no_duplicates(
        df: pd.DataFrame,
        subset: Optional[List[str]] = None
    ) -> Optional[WorkerError]:
        """Validate DataFrame has no duplicates.
        
        Args:
            df: DataFrame to check
            subset: Columns to check for duplicates (None = all cols)
            
        Returns:
            WorkerError if duplicates found, None if valid
        """
        if subset is not None:
            if isinstance(subset, str):
                subset = [subset]
            dup_count = df[subset].duplicated().sum()
        else:
            dup_count = df.duplicated().sum()
        
        if dup_count > 0:
            return WorkerError(
                ErrorType.VALIDATION_ERROR,
                f"Found {dup_count} duplicate rows",
                severity="warning",
                suggestion="Remove duplicates or use aggregation function"
            )
        
        return None

    @staticmethod
    def check_null_values(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None
    ) -> tuple[int, float]:
        """Check for null values in DataFrame.
        
        Args:
            df: DataFrame to check
            columns: Specific columns to check (None = all)
            
        Returns:
            Tuple of (null_count, null_percentage)
        """
        if columns is None:
            null_count = df.isnull().sum().sum()
            total_cells = len(df) * len(df.columns)
        else:
            if isinstance(columns, str):
                columns = [columns]
            null_count = df[columns].isnull().sum().sum()
            total_cells = len(df) * len(columns)
        
        null_percentage = (null_count / total_cells * 100) if total_cells > 0 else 0
        return null_count, null_percentage

    @staticmethod
    def calculate_quality_score(
        rows_processed: int,
        rows_failed: int,
        null_warnings: int = 0,
        duplicate_warnings: int = 0
    ) -> float:
        """Calculate quality score based on data quality metrics.
        
        Args:
            rows_processed: Number of rows successfully processed
            rows_failed: Number of rows that failed
            null_warnings: Number of null value issues
            duplicate_warnings: Number of duplicate warnings
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality from data loss
        total_rows = rows_processed + rows_failed
        if total_rows == 0:
            return 0.0
        
        base_quality = rows_processed / total_rows
        
        # Reduce for warnings
        penalty = 0.0
        if null_warnings > 0:
            penalty += min(0.15, null_warnings * 0.05)  # Up to 15% penalty
        if duplicate_warnings > 0:
            penalty += min(0.10, duplicate_warnings * 0.03)  # Up to 10% penalty
        
        quality_score = base_quality - penalty
        
        # Clamp to 0-1 range
        return max(0.0, min(1.0, quality_score))
