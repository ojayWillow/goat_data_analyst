"""DataLoader Agent - Coordinates data loading workers.

Loads and validates data from multiple file formats:
CSV, JSON, Excel (XLSX, XLS), Parquet
"""

from typing import Any, Dict, Optional, List
from pathlib import Path
import pandas as pd

from core.logger import get_logger
from .workers import (
    CSVLoaderWorker,
    JSONExcelLoaderWorker,
    ValidatorWorker,
    WorkerResult,
)

logger = get_logger(__name__)


class DataLoader:
    """DataLoader Agent - coordinates data loading workers.
    
    Capabilities:
    - Load CSV files
    - Load JSON files
    - Load Excel files (XLSX, XLS)
    - Validate loaded data
    - Extract metadata
    """

    SUPPORTED_FORMATS = ['csv', 'json', 'xlsx', 'xls']
    MAX_FILE_SIZE_MB = 100

    def __init__(self) -> None:
        """Initialize DataLoader agent and all workers."""
        self.name = "DataLoader"
        self.logger = get_logger("DataLoader")
        self.loaded_data: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}

        # === STEP 1: INITIALIZE ALL WORKERS ===
        self.csv_loader = CSVLoaderWorker()
        self.json_excel_loader = JSONExcelLoaderWorker()
        self.validator = ValidatorWorker()

        self.logger.info("DataLoader initialized with 3 workers")

    # === SECTION 1: MAIN LOADING ===

    def load(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Load data from a file.
        
        Args:
            file_path: Path to data file
            **kwargs: Additional pandas arguments
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': DataFrame or None,
                'metadata': dict,
                'errors': list
            }
        """
        if not file_path:
            return self._error_result("No file path provided")

        file_path = Path(file_path)
        file_format = file_path.suffix.lower().lstrip('.')

        # Validate file
        validation = self._validate_file(file_path, file_format)
        if not validation['valid']:
            return self._error_result(validation['message'])

        # Load based on format
        if file_format == 'csv':
            load_result = self.csv_loader.safe_execute(file_path=str(file_path))
        elif file_format == 'json':
            load_result = self.json_excel_loader.safe_execute(
                file_path=str(file_path),
                file_format='json'
            )
        elif file_format in ['xlsx', 'xls']:
            load_result = self.json_excel_loader.safe_execute(
                file_path=str(file_path),
                file_format=file_format
            )
        else:
            return self._error_result(f"Unsupported format: {file_format}")

        if not load_result.success:
            return {
                'status': 'error',
                'message': f"Failed to load {file_format} file",
                'data': None,
                'metadata': {},
                'errors': [e['message'] for e in load_result.errors]
            }

        # Validate data
        df = load_result.data
        validator_result = self.validator.safe_execute(
            df=df,
            file_path=str(file_path),
            file_format=file_format
        )

        if not validator_result.success:
            return {
                'status': 'error',
                'message': "Data validation failed",
                'data': None,
                'metadata': {},
                'errors': [e['message'] for e in validator_result.errors]
            }

        # Store data and metadata
        self.loaded_data = df
        self.metadata = validator_result.metadata

        self.logger.info(f"Successfully loaded {file_format}: {df.shape[0]} rows, {df.shape[1]} columns")

        return {
            'status': 'success',
            'message': f"Loaded {df.shape[0]} rows and {df.shape[1]} columns",
            'data': df,
            'metadata': self.metadata,
            'errors': []
        }

    # === SECTION 2: FILE VALIDATION ===

    def _validate_file(self, file_path: Path, file_format: str) -> Dict[str, Any]:
        """Validate file before loading.
        
        Args:
            file_path: Path object
            file_format: File extension
            
        Returns:
            {'valid': bool, 'message': str}
        """
        # Check exists
        if not file_path.exists():
            return {'valid': False, 'message': f"File not found: {file_path}"}

        # Check size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            return {'valid': False, 'message': f"File too large: {file_size_mb:.1f}MB (max: {self.MAX_FILE_SIZE_MB}MB)"}

        # Check format
        if file_format not in self.SUPPORTED_FORMATS:
            return {'valid': False, 'message': f"Unsupported format: {file_format}. Supported: {self.SUPPORTED_FORMATS}"}

        return {'valid': True, 'message': 'OK'}

    # === SECTION 3: DATA ACCESS ===

    def get_data(self) -> Optional[pd.DataFrame]:
        """Get currently loaded data.
        
        Returns:
            DataFrame or None
        """
        return self.loaded_data

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata of loaded data.
        
        Returns:
            Metadata dictionary
        """
        return self.metadata

    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive information.
        
        Returns:
            Info dictionary
        """
        if self.loaded_data is None:
            return {'status': 'error', 'message': 'No data loaded', 'metadata': {}}

        return {
            'status': 'success',
            'message': f"{self.loaded_data.shape[0]} rows, {self.loaded_data.shape[1]} columns",
            'metadata': self.metadata
        }

    def get_sample(self, n_rows: int = 5) -> Dict[str, Any]:
        """Get sample of loaded data.
        
        Args:
            n_rows: Number of rows
            
        Returns:
            Sample data dictionary
        """
        if self.loaded_data is None:
            return {'status': 'error', 'data': None}

        sample = self.loaded_data.head(n_rows).to_dict(orient='records')
        return {
            'status': 'success',
            'data': sample,
            'metadata': {'total_rows': len(self.loaded_data), 'sample_rows': len(sample)}
        }

    def validate_columns(self, required_columns: List[str]) -> Dict[str, Any]:
        """Validate required columns exist.
        
        Args:
            required_columns: List of column names
            
        Returns:
            Validation result dictionary
        """
        if self.loaded_data is None:
            return {'status': 'error', 'valid': False, 'missing': required_columns}

        missing = [col for col in required_columns if col not in self.loaded_data.columns]
        is_valid = len(missing) == 0

        return {
            'status': 'success' if is_valid else 'error',
            'valid': is_valid,
            'missing': missing
        }

    def get_summary(self) -> str:
        """Get human-readable summary.
        
        Returns:
            Summary string
        """
        if self.loaded_data is None:
            return "No data loaded"

        return (
            f"DataLoader Summary:\n"
            f"  File: {self.metadata.get('file_name', 'unknown')}\n"
            f"  Rows: {self.metadata.get('rows', 0)}\n"
            f"  Columns: {self.metadata.get('columns', 0)}\n"
            f"  Size: {self.metadata.get('file_size_mb', 0)}MB\n"
            f"  Memory: {self.metadata.get('memory_usage_mb', 0)}MB"
        )

    # === SECTION 4: UTILITIES ===

    def _error_result(self, message: str) -> Dict[str, Any]:
        """Create error result dictionary.
        
        Args:
            message: Error message
            
        Returns:
            Error result dictionary
        """
        return {
            'status': 'error',
            'message': message,
            'data': None,
            'metadata': {},
            'errors': [message]
        }
