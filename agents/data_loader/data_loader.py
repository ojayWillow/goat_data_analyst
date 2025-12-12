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
    CSVStreaming,
    FormatDetection,
    WorkerResult,
)

logger = get_logger(__name__)
structured_logger = get_structured_logger(__name__)


class DataLoader:
    """DataLoader Agent - coordinates data loading workers with quality tracking.
    
    Manages 6 workers:
    - CSVLoaderWorker: Loads standard CSV files with quality scoring
    - JSONExcelLoaderWorker: Loads JSON and Excel with validation
    - ParquetLoaderWorker: Loads Parquet files with quality metrics
    - ValidatorWorker: Validates data with comprehensive quality analysis
    - CSVStreaming: Streams large CSVs (>500MB)
    - FormatDetection: Auto-detects formats
    
    Capabilities:
    - Load CSV files (streaming for large files)
    - Load JSON files
    - Load Excel files (XLSX, XLS)
    - Load Parquet files (with streaming)
    - Load JSONL files
    - Load HDF5 files
    - Load SQLite databases
    - Auto-detect file format
    - Validate loaded data with quality scoring
    - Extract comprehensive metadata
    - Track data quality through workflow
    """

    SUPPORTED_FORMATS = ['csv', 'json', 'xlsx', 'xls', 'parquet', 'jsonl', 'h5', 'hdf5', 'db', 'sqlite']
    MAX_FILE_SIZE_MB = 100
    MIN_QUALITY_THRESHOLD = 0.0  # Accept any quality score

    def __init__(self) -> None:
        """Initialize DataLoader agent and all workers."""
        self.name = "DataLoader"
        self.logger = get_logger("DataLoader")
        self.loaded_data: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}
        self.quality_score: float = 0.0
        self.load_history: List[Dict[str, Any]] = []

        # === INITIALIZE ALL WORKERS ===
        # Core workers with enhanced quality scoring
        self.csv_loader = CSVLoaderWorker()
        self.json_excel_loader = JSONExcelLoaderWorker()
        self.parquet_loader = ParquetLoaderWorker()
        self.validator = ValidatorWorker()
        
        # Performance/Format workers (Week 1 Day 1)
        self.csv_streaming = CSVStreaming()
        self.format_detector = FormatDetection()
        
        self.core_workers = [
            self.csv_loader,
            self.json_excel_loader,
            self.parquet_loader,
            self.validator,
        ]
        
        self.performance_workers = [
            self.csv_streaming,
            self.format_detector,
        ]

        self.logger.info("DataLoader initialized with 6 workers")
        structured_logger.info("DataLoader initialized", {
            "core_workers": len(self.core_workers),
            "performance_workers": len(self.performance_workers),
            "total_workers": len(self.core_workers) + len(self.performance_workers),
            "supported_formats": self.SUPPORTED_FORMATS,
            "quality_tracking": "enabled"
        })

    # === MAIN LOADING ===

    @retry_on_error(max_attempts=3, backoff=2)
    def load(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Load data from a file with quality tracking.
        
        Delegates to appropriate worker based on format.
        Uses CSVStreaming for >500MB CSV files.
        Uses FormatDetection for format auto-detection.
        Tracks quality scores through loading and validation pipeline.
        
        Args:
            file_path: Path to data file
            **kwargs: Additional pandas arguments
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': DataFrame or None,
                'metadata': dict,
                'quality_score': float (0.0-1.0),
                'quality_issues': list,
                'warnings': list,
                'errors': list
            }
        """
        if not file_path:
            return self._error_result("No file path provided")

        file_path = Path(file_path)
        file_format = file_path.suffix.lower().lstrip('.')

        # If format missing or unknown, use FormatDetection
        if not file_format or file_format not in self.SUPPORTED_FORMATS:
            detection_result = self.format_detector.safe_execute(file_path=str(file_path))
            if detection_result.success and detection_result.data:
                file_format = detection_result.data.get('detected_format', 'csv')
            else:
                return self._error_result(f"Unsupported or unknown format for file: {file_path}")

        # Validate file
        validation = self._validate_file(file_path, file_format)
        if not validation['valid']:
            return self._error_result(validation['message'])

        # Load based on format
        if file_format == 'csv':
            # Use CSVStreaming for >500MB files
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 500:
                load_result = self.csv_streaming.safe_execute(file_path=str(file_path))
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
            load_result = self.parquet_loader.safe_execute(file_path=str(file_path))
        elif file_format == 'jsonl':
            load_result = self._load_jsonl_worker(file_path=str(file_path))
        elif file_format in ['h5', 'hdf5']:
            load_result = self._load_hdf5_worker(file_path=str(file_path))
        elif file_format in ['db', 'sqlite']:
            load_result = self._load_sqlite_worker(file_path=str(file_path), **kwargs)
        else:
            return self._error_result(f"Unsupported format: {file_format}")

        if not load_result.success:
            self.quality_score = 0.0
            return {
                'status': 'error',
                'message': f"Failed to load {file_format} file",
                'data': None,
                'metadata': {},
                'quality_score': 0.0,
                'quality_issues': [],
                'warnings': [w for w in getattr(load_result, 'warnings', [])],
                'errors': [e['message'] for e in load_result.errors]
            }

        # Store loader quality score
        loader_quality = getattr(load_result, 'quality_score', 0.0)
        self.quality_score = loader_quality
        
        structured_logger.info("File loaded successfully", {
            "format": file_format,
            "rows": len(load_result.data) if load_result.data is not None else 0,
            "columns": len(load_result.data.columns) if load_result.data is not None else 0,
            "worker": getattr(load_result, 'worker', 'unknown'),
            "quality_score": loader_quality
        })

        # Validate data
        df = load_result.data
        validator_result = self.validator.safe_execute(
            df=df,
            file_path=str(file_path),
            file_format=file_format
        )

        # Get validator quality score
        validator_quality = getattr(validator_result, 'quality_score', 0.0)
        
        # Use validator quality if available, as it's more comprehensive
        final_quality = validator_quality if validator_result.success else loader_quality
        self.quality_score = final_quality

        quality_issues = validator_result.metadata.get('issues', []) if validator_result.success else []

        # Store data and metadata
        self.loaded_data = df
        performance_meta = {}
        if hasattr(load_result, 'metadata') and isinstance(load_result.metadata, dict):
            performance_meta.update(load_result.metadata)
        
        validator_meta = validator_result.metadata if validator_result.success else {}
        self.metadata = {**validator_meta, **performance_meta}
        
        # Add quality metrics to metadata
        self.metadata['quality_score'] = final_quality
        self.metadata['loader_quality_score'] = loader_quality
        self.metadata['validator_quality_score'] = validator_quality
        self.metadata['quality_issues'] = quality_issues

        self.logger.info(
            f"Successfully loaded {file_format}: {df.shape[0]} rows, {df.shape[1]} columns, "
            f"quality={final_quality:.2f}"
        )
        
        structured_logger.info("Validation completed", {
            "format": file_format,
            "validation_success": validator_result.success,
            "final_quality": final_quality,
            "quality_issues_count": len(quality_issues)
        })

        # Track load history
        self.load_history.append({
            'file_path': str(file_path),
            'format': file_format,
            'rows': df.shape[0],
            'columns': df.shape[1],
            'quality_score': final_quality,
            'timestamp': time.time()
        })

        return {
            'status': 'success' if validator_result.success else 'warning',
            'message': f"Loaded {df.shape[0]} rows and {df.shape[1]} columns (Quality: {final_quality:.2%})",
            'data': df,
            'metadata': self.metadata,
            'quality_score': final_quality,
            'quality_issues': quality_issues,
            'warnings': list(set([w for w in getattr(load_result, 'warnings', [])] + 
                                [w for w in getattr(validator_result, 'warnings', [])])),
            'errors': [] if validator_result.success else [e['message'] for e in validator_result.errors]
        }

    # === FORMAT LOADERS FOR OTHER FORMATS ===

    @retry_on_error(max_attempts=3, backoff=2)
    def _load_jsonl_worker(self, file_path: str) -> WorkerResult:
        """Load JSONL format.
        
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
                warnings=[],
                quality_score=1.0 if len(df) > 0 else 0.0
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
                warnings=[],
                quality_score=0.0
            )

    @retry_on_error(max_attempts=3, backoff=2)
    def _load_hdf5_worker(self, file_path: str, key: str = 'data') -> WorkerResult:
        """Load HDF5 format.
        
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
                warnings=[],
                quality_score=1.0 if len(df) > 0 else 0.0
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
                warnings=[],
                quality_score=0.0
            )

    @retry_on_error(max_attempts=3, backoff=2)
    def _load_sqlite_worker(self, file_path: str, table_name: str = 'data', query: Optional[str] = None) -> WorkerResult:
        """Load SQLite database.
        
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
                warnings=[],
                quality_score=1.0 if len(df) > 0 else 0.0
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
                warnings=[],
                quality_score=0.0
            )

    # === FILE VALIDATION & FORMAT DETECTION ===

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

    # === DATA ACCESS ===

    @retry_on_error(max_attempts=2, backoff=1)
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get currently loaded data.
        
        Returns:
            DataFrame or None
        """
        return self.loaded_data

    @retry_on_error(max_attempts=2, backoff=1)
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata of loaded data.
        
        Returns:
            Metadata dictionary
        """
        return self.metadata

    @retry_on_error(max_attempts=2, backoff=1)
    def get_quality_score(self) -> float:
        """Get quality score of loaded data.
        
        Returns:
            Quality score (0.0-1.0)
        """
        return self.quality_score

    @retry_on_error(max_attempts=2, backoff=1)
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
            'metadata': self.metadata,
            'quality_score': self.quality_score
        }

    @retry_on_error(max_attempts=2, backoff=1)
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
            'metadata': {
                'total_rows': len(self.loaded_data),
                'sample_rows': len(sample),
                'quality_score': self.quality_score
            }
        }

    @retry_on_error(max_attempts=2, backoff=1)
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

    @retry_on_error(max_attempts=2, backoff=1)
    def get_summary(self) -> str:
        """Get human-readable summary with quality metrics.
        
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
            f"  Memory: {self.metadata.get('memory_usage_mb', 0)}MB\n"
            f"  Quality Score: {self.quality_score:.2%}\n"
            f"  Quality Issues: {len(self.metadata.get('quality_issues', []))}\n"
        )

    @retry_on_error(max_attempts=2, backoff=1)
    def get_load_history(self) -> List[Dict[str, Any]]:
        """Get history of all loaded files.
        
        Returns:
            List of load history entries
        """
        return self.load_history

    # === UTILITIES ===

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
            'quality_score': 0.0,
            'quality_issues': [],
            'warnings': [],
            'errors': [message]
        }
