"""DataLoader Agent - Handles data ingestion from multiple file formats.

Supported formats:
- CSV
- JSON
- Excel (XLSX, XLS)
- Parquet
- SQL databases
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

from core.logger import get_logger
from core.exceptions import DataLoadError, DataValidationError

logger = get_logger(__name__)


class DataLoader:
    """Agent responsible for loading and validating data from various sources.
    
    Capabilities:
    - Load CSV files
    - Load JSON files
    - Load Excel files
    - Load Parquet files
    - Basic data validation
    - Data type inference
    - Handle missing values
    - Data shape and info reporting
    """
    
    SUPPORTED_FORMATS = ['csv', 'json', 'xlsx', 'xls', 'parquet']
    MAX_FILE_SIZE_MB = 100
    
    def __init__(self):
        """Initialize DataLoader agent."""
        self.name = "DataLoader"
        self.loaded_data = None
        self.metadata = {}
        logger.info(f"{self.name} initialized")
    
    def load(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Load data from a file.
        
        Args:
            file_path: Path to the data file
            **kwargs: Additional arguments passed to pandas read functions
            
        Returns:
            Dictionary with status, data, and metadata
            
        Raises:
            DataLoadError: If file cannot be loaded
            DataValidationError: If data validation fails
        """
        try:
            logger.info(f"Loading data from: {file_path}")
            
            # Validate file exists
            file_path = Path(file_path)
            if not file_path.exists():
                raise DataLoadError(f"File not found: {file_path}")
            
            # Validate file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                raise DataLoadError(f"File too large: {file_size_mb:.1f}MB (max: {self.MAX_FILE_SIZE_MB}MB)")
            
            # Get file format
            file_format = file_path.suffix.lower().lstrip('.')
            
            if file_format not in self.SUPPORTED_FORMATS:
                raise DataLoadError(f"Unsupported format: {file_format}. Supported: {self.SUPPORTED_FORMATS}")
            
            # Load data based on format
            if file_format == 'csv':
                df = self._load_csv(file_path, **kwargs)
            elif file_format == 'json':
                df = self._load_json(file_path, **kwargs)
            elif file_format in ['xlsx', 'xls']:
                df = self._load_excel(file_path, **kwargs)
            elif file_format == 'parquet':
                df = self._load_parquet(file_path, **kwargs)
            else:
                raise DataLoadError(f"Unexpected format: {file_format}")
            
            # Validate loaded data
            self._validate_data(df)
            
            # Store data and metadata
            self.loaded_data = df
            self.metadata = self._extract_metadata(df, file_path, file_format, file_size_mb)
            
            logger.info(f"Data loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns")
            
            return {
                "status": "success",
                "message": f"Loaded {df.shape[0]} rows and {df.shape[1]} columns",
                "data": df,
                "metadata": self.metadata,
            }
        
        except (DataLoadError, DataValidationError) as e:
            logger.error(f"Data loading error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading data: {e}")
            raise DataLoadError(f"Failed to load data: {e}")
    
    def _load_csv(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Load CSV file.
        
        Args:
            file_path: Path to CSV file
            **kwargs: Arguments for pd.read_csv
            
        Returns:
            DataFrame
        """
        try:
            logger.debug(f"Loading CSV: {file_path}")
            return pd.read_csv(file_path, **kwargs)
        except Exception as e:
            raise DataLoadError(f"Failed to load CSV: {e}")
    
    def _load_json(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Load JSON file.
        
        Args:
            file_path: Path to JSON file
            **kwargs: Arguments for pd.read_json
            
        Returns:
            DataFrame
        """
        try:
            logger.debug(f"Loading JSON: {file_path}")
            return pd.read_json(file_path, **kwargs)
        except Exception as e:
            raise DataLoadError(f"Failed to load JSON: {e}")
    
    def _load_excel(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Load Excel file.
        
        Args:
            file_path: Path to Excel file
            **kwargs: Arguments for pd.read_excel
            
        Returns:
            DataFrame
        """
        try:
            logger.debug(f"Loading Excel: {file_path}")
            return pd.read_excel(file_path, **kwargs)
        except Exception as e:
            raise DataLoadError(f"Failed to load Excel: {e}")
    
    def _load_parquet(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Load Parquet file.
        
        Args:
            file_path: Path to Parquet file
            **kwargs: Arguments for pd.read_parquet
            
        Returns:
            DataFrame
        """
        try:
            logger.debug(f"Loading Parquet: {file_path}")
            return pd.read_parquet(file_path, **kwargs)
        except Exception as e:
            raise DataLoadError(f"Failed to load Parquet: {e}")
    
    def _validate_data(self, df: pd.DataFrame) -> None:
        """Validate loaded data.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            DataValidationError: If validation fails
        """
        if df is None or df.empty:
            raise DataValidationError("Data is empty")
        
        if len(df.columns) == 0:
            raise DataValidationError("No columns found in data")
        
        logger.debug(f"Data validation passed: {df.shape[0]} rows, {df.shape[1]} columns")
    
    def _extract_metadata(self, df: pd.DataFrame, file_path: Path, file_format: str, file_size_mb: float) -> Dict[str, Any]:
        """Extract metadata from loaded data.
        
        Args:
            df: DataFrame
            file_path: File path
            file_format: File format
            file_size_mb: File size in MB
            
        Returns:
            Metadata dictionary
        """
        # Analyze columns
        columns_info = {}
        for col in df.columns:
            columns_info[col] = {
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].notna().sum()),
                "null_count": int(df[col].isna().sum()),
                "null_percentage": float(df[col].isna().sum() / len(df) * 100),
            }
        
        # Calculate memory usage
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        return {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_format": file_format,
            "file_size_mb": round(file_size_mb, 2),
            "rows": df.shape[0],
            "columns": df.shape[1],
            "column_names": df.columns.tolist(),
            "columns_info": columns_info,
            "dtypes": df.dtypes.astype(str).to_dict(),
            "memory_usage_mb": round(memory_mb, 2),
            "duplicates": int(df.duplicated().sum()),
            "duplicate_percentage": float(df.duplicated().sum() / len(df) * 100),
        }
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get currently loaded data.
        
        Returns:
            Loaded DataFrame or None
        """
        return self.loaded_data
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata of loaded data.
        
        Returns:
            Metadata dictionary
        """
        return self.metadata
    
    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive data information.
        
        Returns:
            Comprehensive data info
        """
        if self.loaded_data is None:
            return {"status": "error", "message": "No data loaded"}
        
        return {
            "status": "success",
            "metadata": self.metadata,
            "data_types": self.loaded_data.dtypes.astype(str).to_dict(),
            "null_summary": self.loaded_data.isna().sum().to_dict(),
        }
    
    def get_sample(self, n_rows: int = 5) -> Dict[str, Any]:
        """Get sample of loaded data.
        
        Args:
            n_rows: Number of rows to return
            
        Returns:
            Sample data and info
        """
        if self.loaded_data is None:
            return {"status": "error", "message": "No data loaded"}
        
        return {
            "status": "success",
            "sample": self.loaded_data.head(n_rows).to_dict(orient='records'),
            "total_rows": len(self.loaded_data),
        }
    
    def validate_columns(self, required_columns: List[str]) -> Dict[str, Any]:
        """Validate that required columns exist.
        
        Args:
            required_columns: List of column names that must exist
            
        Returns:
            Validation result
        """
        if self.loaded_data is None:
            return {"status": "error", "message": "No data loaded"}
        
        missing_columns = [col for col in required_columns if col not in self.loaded_data.columns]
        
        return {
            "status": "success" if not missing_columns else "error",
            "required_columns": required_columns,
            "missing_columns": missing_columns,
            "valid": len(missing_columns) == 0,
        }
