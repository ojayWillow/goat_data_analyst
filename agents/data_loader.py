"""DataLoader Agent - Handles data ingestion from multiple file formats.

This agent loads and validates data from various file types and provides
metadata about the loaded dataset.

Supported formats: CSV, JSON, Excel (XLSX, XLS), Parquet

Returns:
    Dictionary with the following structure:
    {
        'status': 'success' or 'error',
        'message': 'human-readable message',
        'data': pandas.DataFrame or None,
        'metadata': {
            'file_name': str,
            'rows': int,
            'columns': int,
            'column_names': list,
            'file_size_mb': float,
            'memory_usage_mb': float,
            'null_counts': dict,
            'duplicates': int
        },
        'errors': list of error messages
    }

Example:
    loader = DataLoader()
    result = loader.load('data.csv')
    if result['status'] == 'success':
        df = result['data']
        print(f"Loaded {result['metadata']['rows']} rows")
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

from core.logger import get_logger
from core.exceptions import DataLoadError, DataValidationError


class DataLoader:
    """DataLoader: Loads and validates data from various file formats."""

    SUPPORTED_FORMATS = ['csv', 'json', 'xlsx', 'xls', 'parquet']
    MAX_FILE_SIZE_MB = 100

    def __init__(self):
        """Initialize DataLoader agent."""
        self.logger = get_logger("DataLoader")
        self.loaded_data = None
        self.metadata = {}
        self.logger.info("DataLoader initialized")

    # ===== SECTION 1: Main Loading =====
    # What: Load data from file
    # Input: file path
    # Output: structured dictionary with data and metadata

    def load(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Load data from a file.
        
        Args:
            file_path: Path to the data file
            **kwargs: Additional arguments passed to pandas read functions
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': DataFrame or None,
                'metadata': dict,
                'errors': list
            }
        """
        try:
            self.logger.info(f"Loading data from: {file_path}")
            
            # Step 1: Validate file
            validation_result = self._validate_file(file_path)
            if validation_result['status'] == 'error':
                return validation_result
            
            # Step 2: Load based on format
            file_path = Path(file_path)
            file_format = file_path.suffix.lower().lstrip('.')
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            df = self._load_by_format(file_path, file_format, **kwargs)
            
            # Step 3: Validate data
            data_validation = self._validate_data(df)
            if data_validation['status'] == 'error':
                return data_validation
            
            # Step 4: Extract metadata
            self.loaded_data = df
            self.metadata = self._extract_metadata(df, file_path, file_format, file_size_mb)
            
            self.logger.info(f"Successfully loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            
            return {
                'status': 'success',
                'message': f"Loaded {df.shape[0]} rows and {df.shape[1]} columns",
                'data': df,
                'metadata': self.metadata,
                'errors': []
            }
        
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            return {
                'status': 'error',
                'message': f"Failed to load data: {e}",
                'data': None,
                'metadata': {},
                'errors': [str(e)]
            }

    # ===== SECTION 2: File Validation =====
    # What: Check if file exists and is valid
    # Input: file path
    # Output: validation result dictionary

    def _validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate file before loading.
        
        Checks:
        - File exists
        - File size within limit
        - Format is supported
        
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': None,
                'metadata': {},
                'errors': list
            }
        """
        file_path = Path(file_path)
        errors = []
        
        # Check file exists
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return {
                'status': 'error',
                'message': f"File not found: {file_path}",
                'data': None,
                'metadata': {},
                'errors': errors
            }
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            errors.append(f"File too large: {file_size_mb:.1f}MB (max: {self.MAX_FILE_SIZE_MB}MB)")
            return {
                'status': 'error',
                'message': f"File too large",
                'data': None,
                'metadata': {},
                'errors': errors
            }
        
        # Check format
        file_format = file_path.suffix.lower().lstrip('.')
        if file_format not in self.SUPPORTED_FORMATS:
            errors.append(f"Unsupported format: {file_format}. Supported: {self.SUPPORTED_FORMATS}")
            return {
                'status': 'error',
                'message': f"Unsupported format: {file_format}",
                'data': None,
                'metadata': {},
                'errors': errors
            }
        
        return {
            'status': 'success',
            'message': 'File validation passed',
            'data': None,
            'metadata': {},
            'errors': []
        }

    # ===== SECTION 3: Format-Specific Loading =====
    # What: Load data based on file format
    # Input: file path, format, additional kwargs
    # Output: pandas DataFrame

    def _load_by_format(self, file_path: Path, file_format: str, **kwargs) -> pd.DataFrame:
        """Load file based on its format.
        
        Args:
            file_path: Path to file
            file_format: File extension
            **kwargs: Additional arguments for pandas
            
        Returns:
            pandas.DataFrame
        """
        if file_format == 'csv':
            return self._load_csv(file_path, **kwargs)
        elif file_format == 'json':
            return self._load_json(file_path, **kwargs)
        elif file_format in ['xlsx', 'xls']:
            return self._load_excel(file_path, **kwargs)
        elif file_format == 'parquet':
            return self._load_parquet(file_path, **kwargs)
        else:
            raise DataLoadError(f"Unexpected format: {file_format}")

    def _load_csv(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Load CSV file.
        
        Args:
            file_path: Path to CSV file
            **kwargs: Arguments for pd.read_csv
            
        Returns:
            pandas.DataFrame
        """
        try:
            self.logger.debug(f"Loading CSV: {file_path}")
            if 'low_memory' not in kwargs:
                kwargs['low_memory'] = False
            return pd.read_csv(file_path, **kwargs)
        except Exception as e:
            raise DataLoadError(f"Failed to load CSV: {e}")

    def _load_json(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Load JSON file.
        
        Args:
            file_path: Path to JSON file
            **kwargs: Arguments for pd.read_json
            
        Returns:
            pandas.DataFrame
        """
        try:
            self.logger.debug(f"Loading JSON: {file_path}")
            return pd.read_json(file_path, **kwargs)
        except Exception as e:
            raise DataLoadError(f"Failed to load JSON: {e}")

    def _load_excel(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Load Excel file.
        
        Args:
            file_path: Path to Excel file
            **kwargs: Arguments for pd.read_excel
            
        Returns:
            pandas.DataFrame
        """
        try:
            self.logger.debug(f"Loading Excel: {file_path}")
            return pd.read_excel(file_path, **kwargs)
        except Exception as e:
            raise DataLoadError(f"Failed to load Excel: {e}")

    def _load_parquet(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Load Parquet file.
        
        Args:
            file_path: Path to Parquet file
            **kwargs: Arguments for pd.read_parquet
            
        Returns:
            pandas.DataFrame
        """
        try:
            self.logger.debug(f"Loading Parquet: {file_path}")
            return pd.read_parquet(file_path, **kwargs)
        except Exception as e:
            raise DataLoadError(f"Failed to load Parquet: {e}")

    # ===== SECTION 4: Data Validation =====
    # What: Validate loaded data is usable
    # Input: DataFrame
    # Output: validation result dictionary

    def _validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate loaded data.
        
        Checks:
        - Data is not empty
        - Has columns
        - Is valid DataFrame
        
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': None,
                'metadata': {},
                'errors': list
            }
        """
        errors = []
        
        if df is None:
            errors.append("Data is None")
        elif df.empty:
            errors.append("Data is empty")
        elif len(df.columns) == 0:
            errors.append("No columns found in data")
        
        if errors:
            self.logger.error(f"Data validation failed: {errors}")
            return {
                'status': 'error',
                'message': 'Data validation failed',
                'data': None,
                'metadata': {},
                'errors': errors
            }
        
        self.logger.debug(f"Data validation passed")
        return {
            'status': 'success',
            'message': 'Data validation passed',
            'data': None,
            'metadata': {},
            'errors': []
        }

    # ===== SECTION 5: Metadata Extraction =====
    # What: Extract information about the data
    # Input: DataFrame, file path, format, size
    # Output: metadata dictionary

    def _extract_metadata(self, df: pd.DataFrame, file_path: Path, 
                         file_format: str, file_size_mb: float) -> Dict[str, Any]:
        """Extract comprehensive metadata from loaded data.
        
        Args:
            df: DataFrame
            file_path: File path
            file_format: File format
            file_size_mb: File size in MB
            
        Returns:
            Dictionary with file and data info
        """
        # Analyze each column
        columns_info = {}
        for col in df.columns:
            columns_info[col] = {
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].notna().sum()),
                "null_count": int(df[col].isna().sum()),
                "null_percentage": float(df[col].isna().sum() / len(df) * 100) if len(df) > 0 else 0,
            }
        
        # Calculate memory usage
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        return {
            # File information
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_format": file_format,
            "file_size_mb": round(file_size_mb, 2),
            
            # Data shape
            "rows": df.shape[0],
            "columns": df.shape[1],
            "column_names": df.columns.tolist(),
            
            # Memory
            "memory_usage_mb": round(memory_mb, 2),
            
            # Column details
            "columns_info": columns_info,
            "dtypes": df.dtypes.astype(str).to_dict(),
            
            # Data quality
            "duplicates": int(df.duplicated().sum()),
            "duplicate_percentage": float(df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0,
        }

    # ===== SECTION 6: Data Access & Utilities =====
    # What: Retrieve loaded data and information
    # Input: various
    # Output: data or info dictionary

    def get_data(self) -> Optional[pd.DataFrame]:
        """Get currently loaded data.
        
        Returns:
            Loaded DataFrame or None if no data loaded
        """
        return self.loaded_data

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata of loaded data.
        
        Returns:
            Metadata dictionary
        """
        return self.metadata

    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive information about loaded data.
        
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': None,
                'metadata': dict,
                'errors': list
            }
        """
        if self.loaded_data is None:
            return {
                'status': 'error',
                'message': 'No data loaded',
                'data': None,
                'metadata': {},
                'errors': ['No data loaded']
            }
        
        return {
            'status': 'success',
            'message': f"Data info: {self.loaded_data.shape[0]} rows, {self.loaded_data.shape[1]} columns",
            'data': None,
            'metadata': self.metadata,
            'errors': []
        }

    def get_sample(self, n_rows: int = 5) -> Dict[str, Any]:
        """Get sample of loaded data.
        
        Args:
            n_rows: Number of rows to return (default: 5)
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': list of dicts,
                'metadata': {'total_rows': int, 'sample_rows': int},
                'errors': list
            }
        """
        if self.loaded_data is None:
            return {
                'status': 'error',
                'message': 'No data loaded',
                'data': None,
                'metadata': {},
                'errors': ['No data loaded']
            }
        
        sample = self.loaded_data.head(n_rows).to_dict(orient='records')
        return {
            'status': 'success',
            'message': f"Returned {len(sample)} sample rows",
            'data': sample,
            'metadata': {
                'total_rows': len(self.loaded_data),
                'sample_rows': len(sample)
            },
            'errors': []
        }

    def validate_columns(self, required_columns: List[str]) -> Dict[str, Any]:
        """Validate that required columns exist in loaded data.
        
        Args:
            required_columns: List of column names that must exist
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': None,
                'metadata': {'required': list, 'missing': list, 'valid': bool},
                'errors': list
            }
        """
        if self.loaded_data is None:
            return {
                'status': 'error',
                'message': 'No data loaded',
                'data': None,
                'metadata': {},
                'errors': ['No data loaded']
            }
        
        missing_columns = [col for col in required_columns if col not in self.loaded_data.columns]
        is_valid = len(missing_columns) == 0
        
        return {
            'status': 'success' if is_valid else 'error',
            'message': 'All required columns found' if is_valid else f'Missing columns: {missing_columns}',
            'data': None,
            'metadata': {
                'required_columns': required_columns,
                'missing_columns': missing_columns,
                'valid': is_valid
            },
            'errors': [] if is_valid else [f"Missing: {missing_columns}"]
        }

    def get_summary(self) -> str:
        """Get human-readable summary of loaded data.
        
        Returns:
            Formatted summary string
        """
        if self.loaded_data is None:
            return "No data loaded"
        
        return (
            f"DataLoader Summary:\n"
            f"  File: {self.metadata.get('file_name', 'unknown')}\n"
            f"  Rows: {self.metadata.get('rows', 0)}\n"
            f"  Columns: {self.metadata.get('columns', 0)}\n"
            f"  Size: {self.metadata.get('file_size_mb', 0)}MB\n"
            f"  Memory: {self.metadata.get('memory_usage_mb', 0)}MB\n"
            f"  Duplicates: {self.metadata.get('duplicates', 0)}"
        )
