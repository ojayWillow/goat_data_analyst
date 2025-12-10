"""DataLoader Agent - Coordinates data loading workers.

Loads and validates data from multiple file formats:
CSV, JSON, Excel (XLSX, XLS), Parquet, JSONL, HDF5, SQLite
"""

from typing import Any, Dict, Optional, List
from pathlib import Path
import pandas as pd
import os
import sqlite3
import time

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from .workers import (
    CSVLoaderWorker,
    JSONExcelLoaderWorker,
    ParquetLoaderWorker,
    ValidatorWorker,
    WorkerResult,
)

logger = get_logger(__name__)
structured_logger = get_structured_logger(__name__)


class DataLoader:
    """DataLoader Agent - coordinates data loading workers.
    
    Capabilities:
    - Load CSV files (streaming for large files)
    - Load JSON files
    - Load Excel files (XLSX, XLS)
    - Load Parquet files (with streaming)
    - Load JSONL files
    - Load HDF5 files
    - Load SQLite databases
    - Validate loaded data
    - Extract metadata
    """

    SUPPORTED_FORMATS = ['csv', 'json', 'xlsx', 'xls', 'parquet', 'jsonl', 'h5', 'hdf5', 'db', 'sqlite']
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
        self.parquet_loader = ParquetLoaderWorker()
        self.validator = ValidatorWorker()

        self.logger.info("DataLoader initialized with 4 workers")
        structured_logger.info("DataLoader initialized", {
            "workers": 4,
            "supported_formats": self.SUPPORTED_FORMATS
        })

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

        # If format missing or unknown, try to auto-detect
        if not file_format or file_format not in self.SUPPORTED_FORMATS:
            detected = self._detect_format(file_path)
            if detected:
                file_format = detected
            else:
                return self._error_result(f"Unsupported or unknown format for file: {file_path}")

        # Validate file
        validation = self._validate_file(file_path, file_format)
        if not validation['valid']:
            return self._error_result(validation['message'])

        # Load based on format
        if file_format == 'csv':
            # Decide streaming vs normal based on size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 500:  # large file threshold
                load_result = self._load_csv_streaming(file_path=str(file_path))
            else:
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
        elif file_format == 'parquet':
            # Use streaming by default for parquet
            load_result = self._load_parquet_streaming(file_path=str(file_path), **kwargs)
        elif file_format == 'jsonl':
            load_result = self._load_jsonl_worker(file_path=str(file_path))
        elif file_format in ['h5', 'hdf5']:
            load_result = self._load_hdf5_worker(file_path=str(file_path))
        elif file_format in ['db', 'sqlite']:
            load_result = self._load_sqlite_worker(file_path=str(file_path), **kwargs)
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
        # Attach basic performance metadata if available
        performance_meta = {}
        if hasattr(load_result, 'metadata') and isinstance(load_result.metadata, dict):
            performance_meta.update(load_result.metadata)
        self.metadata = {**validator_result.metadata, **performance_meta}

        self.logger.info(f"Successfully loaded {file_format}: {df.shape[0]} rows, {df.shape[1]} columns")
        structured_logger.info("File loaded successfully", {
            "format": file_format,
            "rows": df.shape[0],
            "columns": df.shape[1]
        })

        return {
            'status': 'success',
            'message': f"Loaded {df.shape[0]} rows and {df.shape[1]} columns",
            'data': df,
            'metadata': self.metadata,
            'errors': []
        }

    # === SECTION 2: WEEK 2 FORMAT LOADERS + PERFORMANCE HELPERS ===

    @retry_on_error(max_attempts=3, backoff=2)
    def _load_jsonl_worker(self, file_path: str) -> WorkerResult:
        """Load JSONL format using worker pattern.
        
        Args:
            file_path: Path to JSONL file
            
        Returns:
            WorkerResult with loaded DataFrame
        """
        structured_logger.info("Loading JSONL file", {
            "filepath": file_path,
            "format": "jsonl"
        })
        
        start_time = time.time()
        try:
            df = pd.read_json(file_path, lines=True)
            duration = time.time() - start_time
            structured_logger.info("JSONL loaded successfully", {
                "shape": str(df.shape),
                "columns": len(df.columns),
                "duration_sec": round(duration, 3)
            })
            return WorkerResult(
                worker="DataLoaderJSONL",
                task_type="load_jsonl",
                success=True,
                data=df,
                errors=[],
                warnings=[]
            )
        except Exception as e:
            structured_logger.error("Failed to load JSONL", {
                "filepath": file_path,
                "error": str(e)
            })
            return WorkerResult(
                worker="DataLoaderJSONL",
                task_type="load_jsonl",
                success=False,
                data=None,
                errors=[{"message": str(e), "type": "load_error"}],
                warnings=[]
            )

    @retry_on_error(max_attempts=3, backoff=2)
    def _load_hdf5_worker(self, file_path: str, key: str = 'data') -> WorkerResult:
        """Load HDF5 format using worker pattern.
        
        Args:
            file_path: Path to HDF5 file
            key: HDF5 key/group name
            
        Returns:
            WorkerResult with loaded DataFrame
        """
        structured_logger.info("Loading HDF5 file", {
            "filepath": file_path,
            "format": "hdf5",
            "key": key
        })
        
        start_time = time.time()
        try:
            df = pd.read_hdf(file_path, key)
            duration = time.time() - start_time
            structured_logger.info("HDF5 loaded successfully", {
                "shape": str(df.shape),
                "columns": len(df.columns),
                "duration_sec": round(duration, 3)
            })
            return WorkerResult(
                worker="DataLoaderHDF5",
                task_type="load_hdf5",
                success=True,
                data=df,
                errors=[],
                warnings=[]
            )
        except Exception as e:
            structured_logger.error("Failed to load HDF5", {
                "filepath": file_path,
                "error": str(e)
            })
            return WorkerResult(
                worker="DataLoaderHDF5",
                task_type="load_hdf5",
                success=False,
                data=None,
                errors=[{"message": str(e), "type": "load_error"}],
                warnings=[]
            )

    @retry_on_error(max_attempts=3, backoff=2)
    def _load_sqlite_worker(self, file_path: str, table_name: str = 'data', query: Optional[str] = None) -> WorkerResult:
        """Load SQLite database using worker pattern.
        
        Args:
            file_path: Path to SQLite database file
            table_name: Table name to load
            query: Optional SQL query to execute
            
        Returns:
            WorkerResult with loaded DataFrame
        """
        structured_logger.info("Loading SQLite database", {
            "filepath": file_path,
            "format": "sqlite",
            "table": table_name,
            "query": query
        })
        
        start_time = time.time()
        try:
            conn = sqlite3.connect(file_path)
            
            if query:
                df = pd.read_sql(query, conn)
            else:
                df = pd.read_sql(f'SELECT * FROM {table_name}', conn)
            
            conn.close()
            duration = time.time() - start_time
            
            structured_logger.info("SQLite loaded successfully", {
                "shape": str(df.shape),
                "columns": len(df.columns),
                "duration_sec": round(duration, 3)
            })
            return WorkerResult(
                worker="DataLoaderSQLite",
                task_type="load_sqlite",
                success=True,
                data=df,
                errors=[],
                warnings=[]
            )
        except Exception as e:
            structured_logger.error("Failed to load SQLite", {
                "filepath": file_path,
                "error": str(e)
            })
            return WorkerResult(
                worker="DataLoaderSQLite",
                task_type="load_sqlite",
                success=False,
                data=None,
                errors=[{"message": str(e), "type": "load_error"}],
                warnings=[]
            )

    @retry_on_error(max_attempts=3, backoff=2)
    def _load_parquet_streaming(self, file_path: str, columns: Optional[List[str]] = None, chunk_size: int = 50000) -> WorkerResult:
        """Load Parquet format with streaming/chunking support.
        
        Args:
            file_path: Path to Parquet file
            columns: Optional columns to read
            chunk_size: Number of rows per chunk
            
        Returns:
            WorkerResult with loaded DataFrame
        """
        structured_logger.info("Loading Parquet file with streaming", {
            "filepath": file_path,
            "format": "parquet",
            "columns": columns,
            "chunk_size": chunk_size
        })
        
        try:
            import pyarrow.parquet as pq
            
            start_time = time.time()
            parquet_file = pq.ParquetFile(file_path)
            
            batches = []
            for batch in parquet_file.iter_batches(batch_size=chunk_size, columns=columns):
                batches.append(batch.to_pandas())
            
            if batches:
                df = pd.concat(batches, ignore_index=True)
            else:
                df = pd.DataFrame()
            
            duration = time.time() - start_time
            structured_logger.info("Parquet loaded successfully", {
                "shape": str(df.shape),
                "columns": len(df.columns),
                "batches_read": len(batches),
                "duration_sec": round(duration, 3)
            })
            return WorkerResult(
                worker="DataLoaderParquet",
                task_type="load_parquet_streaming",
                success=True,
                data=df,
                errors=[],
                warnings=[],
            )
        except Exception as e:
            structured_logger.error("Failed to load Parquet", {
                "filepath": file_path,
                "error": str(e)
            })
            return WorkerResult(
                worker="DataLoaderParquet",
                task_type="load_parquet_streaming",
                success=False,
                data=None,
                errors=[{"message": str(e), "type": "load_error"}],
                warnings=[]
            )

    @retry_on_error(max_attempts=3, backoff=2)
    def _load_csv_streaming(self, file_path: str, chunk_size: int = 100000) -> WorkerResult:
        """Stream large CSV files in chunks with robust error handling.
        
        Args:
            file_path: Path to CSV file
            chunk_size: Number of rows per chunk
            
        Returns:
            WorkerResult with loaded DataFrame
        """
        structured_logger.info("Loading CSV file with streaming", {
            "filepath": file_path,
            "format": "csv",
            "chunk_size": chunk_size
        })

        start_time = time.time()
        chunks = []
        total_rows = 0
        bad_lines = 0

        try:
            # Use pandas streaming with bad line handling and encoding tolerance
            for chunk in pd.read_csv(
                file_path,
                chunksize=chunk_size,
                on_bad_lines='skip',  # Skip corrupt lines
                encoding_errors='ignore',  # Ignore encoding issues
            ):
                rows = len(chunk)
                total_rows += rows
                chunks.append(chunk)
            
            if chunks:
                df = pd.concat(chunks, ignore_index=True)
            else:
                df = pd.DataFrame()

            duration = time.time() - start_time
            structured_logger.info("CSV streamed successfully", {
                "shape": str(df.shape),
                "total_rows": total_rows,
                "duration_sec": round(duration, 3),
                "chunk_size": chunk_size,
                "bad_lines": bad_lines
            })

            return WorkerResult(
                worker="CSVStreaming",
                task_type="load_csv_stream",
                success=True,
                data=df,
                errors=[],
                warnings=[],
            )
        except Exception as e:
            structured_logger.error("Failed to stream CSV", {
                "filepath": file_path,
                "error": str(e)
            })
            return WorkerResult(
                worker="CSVStreaming",
                task_type="load_csv_stream",
                success=False,
                data=None,
                errors=[{"message": str(e), "type": "load_error"}],
                warnings=[],
            )

    # === SECTION 3: FILE VALIDATION & FORMAT DETECTION ===

    def _validate_file(self, file_path: Path, file_format: str) -> Dict[str, Any]:
        """Validate file before loading.
        
        Args:
            file_path: Path object
            file_format: File extension
            
        Returns:
            {'valid': bool, 'message': str}
        """
        if not file_path.exists():
            return {'valid': False, 'message': f"File not found: {file_path}"}

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            return {'valid': False, 'message': f"File too large: {file_size_mb:.1f}MB (max: {self.MAX_FILE_SIZE_MB}MB)"}

        if file_format not in self.SUPPORTED_FORMATS:
            return {'valid': False, 'message': f"Unsupported format: {file_format}. Supported: {self.SUPPORTED_FORMATS}"}

        return {'valid': True, 'message': 'OK'}

    def _detect_format(self, file_path: Path) -> Optional[str]:
        """Auto-detect file format by inspecting file contents.
        
        This is a best-effort heuristic used when file extension is missing or unreliable.
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)

            # Parquet magic bytes
            if header[:4] == b'PAR1':
                return 'parquet'

            # Excel (ZIP based) magic bytes
            if header[:2] == b'PK':
                return 'xlsx'

            # SQLite header
            if header.startswith(b'SQLite format'):
                return 'sqlite'

            # JSON likely starts with { or [
            stripped = header.lstrip()
            if stripped.startswith(b'{') or stripped.startswith(b'['):
                return 'json'

            # Fallback: assume CSV
            return 'csv'
        except Exception as e:
            structured_logger.error("Failed to auto-detect file format", {
                "filepath": str(file_path),
                "error": str(e)
            })
            return None

    # === SECTION 4: DATA ACCESS ===

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

    # === SECTION 5: UTILITIES ===

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
