"""JSON & Excel Loader Worker - Handles JSON and Excel file loading."""

import pandas as pd
from pathlib import Path
from typing import Any, Dict

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class JSONExcelLoaderWorker(BaseWorker):
    """Worker that loads JSON and Excel files."""
    
    def __init__(self):
        """Initialize JSONExcelLoaderWorker."""
        super().__init__("JSONExcelLoaderWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute JSON/Excel loading.
        
        Args:
            file_path: Path to file (JSON, XLSX, XLS)
            file_format: 'json', 'xlsx', or 'xls'
            **kwargs: Additional pandas arguments
            
        Returns:
            WorkerResult with loaded data
        """
        try:
            result = self._run_json_excel_load(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="data_loader",
                worker_name="JSONExcelLoaderWorker",
                operation="json_excel_loading",
                context={"file_path": kwargs.get('file_path'), "file_format": kwargs.get('file_format')}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="data_loader",
                worker_name="JSONExcelLoaderWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"file_path": kwargs.get('file_path'), "file_format": kwargs.get('file_format')}
            )
            raise
    
    def _run_json_excel_load(self, **kwargs) -> WorkerResult:
        """Perform JSON/Excel loading."""
        file_path = kwargs.get('file_path')
        file_format = kwargs.get('file_format', '').lower()
        
        result = self._create_result(task_type=f"{file_format}_loading")
        
        # Validate inputs
        if not file_path:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "No file path provided")
            result.success = False
            return result
        
        if not file_format:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "No file format provided")
            result.success = False
            return result
        
        file_path = Path(file_path)
        
        # Check file exists
        if not file_path.exists():
            self._add_error(result, ErrorType.FILE_NOT_FOUND, f"File not found: {file_path}")
            result.success = False
            return result
        
        try:
            if file_format == 'json':
                df = pd.read_json(file_path)
            elif file_format in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                self._add_error(result, ErrorType.UNSUPPORTED_FORMAT, f"Unsupported format: {file_format}")
                result.success = False
                return result
            
            if df.empty:
                self._add_error(result, ErrorType.EMPTY_DATA, f"{file_format.upper()} file is empty")
                result.success = False
                return result
            
            result.data = df
            result.metadata = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "file_size_mb": file_path.stat().st_size / (1024 * 1024),
            }
            
            logger.info(f"{file_format.upper()} loaded: {len(df)} rows, {len(df.columns)} columns")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Failed to load {file_format}: {e}")
            result.success = False
            return result
