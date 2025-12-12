"""Anomaly Detector Agent - Coordinates anomaly detection workers.

Detects anomalies using 6 different algorithms:
- Statistical: Z-score and IQR based detection
- Isolation Forest
- Local Outlier Factor (LOF)
- One-Class SVM
- Multivariate: Multivariate Gaussian detection
- Ensemble: Ensemble voting from all methods

GUIDANCE Compliance:
- Section 2.2: Agent Interface Contract
- Section 2.3: Agent Implementation Requirements

Integrated with Week 1-2 Systems:
- Structured logging with metrics
- Automatic retry with exponential backoff
- Error recovery and handling
- Error Intelligence tracking (Phase 2)
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
from .workers import (
    StatisticalWorker,
    IsolationForest,
    LOF,
    OneClassSVM,
    MultivariateWorker,
    Ensemble,
    WorkerResult,
)

logger = get_logger(__name__)
structured_logger = get_structured_logger(__name__)

# ===== CONSTANTS =====
HEALTH_THRESHOLD = 0.8
QUALITY_THRESHOLD = 0.8
MIN_QUALITY_FOR_SUCCESS = 0.5


class AnomalyDetector:
    """Anomaly Detector Agent - coordinates anomaly detection workers.
    
    Manages 6 workers:
    - StatisticalWorker: Statistical anomaly detection (Z-score, IQR)
    - IsolationForest: Isolation Forest algorithm
    - LOF: Local Outlier Factor algorithm
    - OneClassSVM: One-Class SVM algorithm
    - MultivariateWorker: Multivariate Gaussian detection
    - Ensemble: Ensemble voting method
    
    GUIDANCE Implementation:
    - Pure Coordinator pattern (doesn't implement detection)
    - Orchestrates worker execution
    - Handles errors at worker level
    - Tracks error intelligence
    - Provides health metrics
    - Supports retry with backoff
    
    Attributes:
        name: Agent identifier
        workers: Dict of registered workers
        error_tracker: ErrorIntelligence for tracking (set by orchestrator)
        data: Current DataFrame being processed
        detection_results: Results from all workers
        error_log: List of all errors encountered
    """

    def __init__(self) -> None:
        """Initialize the Anomaly Detector agent and all workers."""
        self.name = "AnomalyDetector"
        self.version = "1.0.0"
        self.logger = get_logger("AnomalyDetector")
        self.structured_logger = get_structured_logger("AnomalyDetector")
        self.data: Optional[pd.DataFrame] = None
        self.detection_results: Dict[str, WorkerResult] = {}
        self.error_log: List[Dict[str, Any]] = []
        self.error_tracker = None  # Will be set by orchestrator

        # === INITIALIZE ALL 6 WORKERS ===
        self.statistical_detector = StatisticalWorker()
        self.isolation_forest_detector = IsolationForest()
        self.lof_detector = LOF()
        self.ocsvm_detector = OneClassSVM()
        self.multivariate_detector = MultivariateWorker()
        self.ensemble_detector = Ensemble()

        # Dictionary for execute_worker() method
        self.workers: Dict[str, Any] = {
            "statistical": self.statistical_detector,
            "isolation_forest": self.isolation_forest_detector,
            "lof": self.lof_detector,
            "ocsvm": self.ocsvm_detector,
            "multivariate": self.multivariate_detector,
            "ensemble": self.ensemble_detector,
        }

        # Set error tracker for all workers (for Phase 2 integration)
        for worker in self.workers.values():
            worker.error_tracker = self.error_tracker

        self.logger.info(
            f"{self.name} initialized with {len(self.workers)} detection workers"
        )
        self.structured_logger.info("AnomalyDetector initialized", {
            "workers": len(self.workers),
            "worker_names": list(self.workers.keys())
        })

    # ===== DATA MANAGEMENT (Agent Contract) =====

    @retry_on_error(max_attempts=2, backoff=1)
    def set_data(self, df: pd.DataFrame) -> None:
        """Load input data for processing.
        
        GUIDANCE: Section 2.2 - Agent Interface Contract
        
        Args:
            df: Input DataFrame to process
            
        Raises:
            ValueError: If data is invalid or empty
            TypeError: If data is not DataFrame
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected DataFrame, got {type(df)}")
        
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        self.data = df.copy()
        self.detection_results = {}
        self.error_log = []
        
        self.logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
        self.structured_logger.info("Data set for anomaly detection", {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "numeric_cols": len(df.select_dtypes(include=['number']).columns)
        })

    @retry_on_error(max_attempts=2, backoff=1)
    def get_data(self) -> Optional[pd.DataFrame]:
        """Retrieve the stored DataFrame.
        
        Returns:
            DataFrame or None if not set
        """
        return self.data

    # ===== AGENT CONTRACT: execute_worker() =====

    @retry_on_error(max_attempts=3, backoff=2)
    def execute_worker(
        self,
        worker_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a specific worker with retry logic.
        
        GUIDANCE: Section 2.2 - Agent Interface Contract
        
        Implements:
        - Worker orchestration
        - Error handling
        - Retry logic
        - Error intelligence tracking
        
        Args:
            worker_name: Name of worker to execute (must be in self.workers)
            **kwargs: Worker-specific parameters
            
        Returns:
            {
                'success': bool,
                'result': Any,              # Worker output
                'errors': List[Dict],       # Errors encountered
                'attempts': int,            # Retry attempts made
                'quality_score': float      # 0-1 quality metric
            }
            
        Raises:
            KeyError: If worker not found
            RuntimeError: If all retries exhausted
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if worker_name not in self.workers:
            available = list(self.workers.keys())
            raise KeyError(
                f"Worker '{worker_name}' not found. "
                f"Available workers: {available}"
            )
        
        worker = self.workers[worker_name]
        self.structured_logger.info(
            f"Executing worker: {worker_name}",
            {"kwargs": str(kwargs)[:100]}
        )
        
        try:
            # Execute worker with error handling
            worker_result = worker.safe_execute(
                df=self.data,
                **kwargs
            )
            
            # Store result
            self.detection_results[worker_name] = worker_result
            
            # Track in error intelligence if available
            if self.error_tracker:
                if worker_result.success:
                    self.error_tracker.track_success(
                        worker_name=worker_name,
                        quality_score=worker_result.quality_score
                    )
                else:
                    self.error_tracker.track_error(
                        worker_name=worker_name,
                        errors=worker_result.errors,
                        quality_score=worker_result.quality_score
                    )
            
            # Log errors if any
            if worker_result.errors:
                for error in worker_result.errors:
                    self.error_log.append({
                        "worker": worker_name,
                        "error": error,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            self.structured_logger.info(
                f"Worker {worker_name} completed",
                {"success": worker_result.success, 
                 "quality": worker_result.quality_score}
            )
            
            return {
                'success': worker_result.success,
                'result': worker_result.data,
                'errors': worker_result.errors,
                'attempts': 1,
                'quality_score': worker_result.quality_score
            }
        
        except Exception as e:
            self.logger.error(f"Worker {worker_name} execution failed: {e}")
            error_record = {
                "worker": worker_name,
                "error": {"type": "execution_error", "message": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
            self.error_log.append(error_record)
            
            if self.error_tracker:
                self.error_tracker.track_error(
                    worker_name=worker_name,
                    errors=[{"type": "execution_error", "message": str(e)}],
                    quality_score=0.0
                )
            
            raise

    # ===== AGENT CONTRACT: get_results() =====

    @retry_on_error(max_attempts=2, backoff=1)
    def get_results(self) -> pd.DataFrame:
        """Return final aggregated results.
        
        GUIDANCE: Section 2.2 - Agent Interface Contract
        
        Aggregates results from all executed workers into a single
        DataFrame with anomaly flags from each detection method.
        
        Returns:
            DataFrame with original data + anomaly columns for each worker
            
        Raises:
            ValueError: If no data or results available
        """
        if self.data is None:
            raise ValueError("No data available")
        
        if not self.detection_results:
            raise ValueError("No detection results. Run detect_* methods first.")
        
        # Start with original data
        results_df = self.data.copy()
        
        # Add anomaly columns from each worker
        for worker_name, result in self.detection_results.items():
            if result.success and result.data:
                # Assuming result.data has 'anomaly' column
                if isinstance(result.data, dict) and 'anomaly' in result.data:
                    col_name = f"anomaly_{worker_name}"
                    results_df[col_name] = result.data['anomaly']
                elif isinstance(result.data, pd.DataFrame):
                    # If already DataFrame, merge it
                    for col in result.data.columns:
                        results_df[f"{worker_name}_{col}"] = result.data[col]
        
        self.logger.info(
            f"Results aggregated: {results_df.shape[0]} rows, "
            f"{results_df.shape[1]} columns"
        )
        return results_df

    # ===== AGENT CONTRACT: get_health_report() =====

    @retry_on_error(max_attempts=2, backoff=1)
    def get_health_report(self) -> Dict[str, Any]:
        """Get system health and error intelligence.
        
        GUIDANCE: Section 2.2 - Agent Interface Contract
        
        Calculates comprehensive health metrics:
        - Overall health score (0-100)
        - Per-worker health scores
        - Error statistics and patterns
        - Quality metrics
        - Recommendations for improvement
        
        Returns:
            {
                'overall_health': float,           # 0-100
                'total_errors': int,
                'error_types': Dict[str, int],
                'worker_health': Dict[str, float],
                'quality_scores': Dict[str, float],
                'recommendations': List[str],
                'timestamp': str
            }
        """
        # Count errors by type
        error_types: Dict[str, int] = {}
        for error_record in self.error_log:
            error_type = error_record['error'].get('type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Calculate per-worker health
        worker_health: Dict[str, float] = {}
        quality_scores: Dict[str, float] = {}
        
        for worker_name, result in self.detection_results.items():
            quality_scores[worker_name] = result.quality_score
            
            # Health = quality score if success, else 0
            if result.success:
                worker_health[worker_name] = result.quality_score * 100
            else:
                worker_health[worker_name] = 0.0
        
        # Calculate overall health
        if worker_health:
            overall_health = sum(worker_health.values()) / len(worker_health)
        else:
            overall_health = 50.0  # Neutral if no results yet
        
        # Generate recommendations
        recommendations: List[str] = []
        
        if overall_health < HEALTH_THRESHOLD * 100:
            recommendations.append(
                f"System health is below threshold ({overall_health:.1f}%). "
                "Review errors and worker configurations."
            )
        
        if error_types:
            most_common_error = max(error_types, key=error_types.get)
            recommendations.append(
                f"Most common error: {most_common_error} "
                f"({error_types[most_common_error]} occurrences). "
                "Consider addressing this error type."
            )
        
        low_health_workers = [
            name for name, health in worker_health.items()
            if health < QUALITY_THRESHOLD * 100
        ]
        if low_health_workers:
            recommendations.append(
                f"Workers with low health: {', '.join(low_health_workers)}. "
                "Review their configurations and input data."
            )
        
        return {
            'overall_health': overall_health,
            'total_errors': len(self.error_log),
            'error_types': error_types,
            'worker_health': worker_health,
            'quality_scores': quality_scores,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        }

    # ===== DETECTION METHODS - DELEGATE TO WORKERS =====

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_statistical(
        self,
        column: str,
        method: str = 'iqr',
        multiplier: float = 1.5,
    ) -> Dict[str, Any]:
        """Detect anomalies using Statistical methods.
        
        Args:
            column: Column to analyze
            method: Detection method ('iqr', 'zscore', 'modified_zscore')
            multiplier: IQR multiplier
            
        Returns:
            Detection result as dictionary
        """
        return self.execute_worker(
            "statistical",
            column=column,
            method=method,
            multiplier=multiplier
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_isolation_forest(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
    ) -> Dict[str, Any]:
        """Detect anomalies using Isolation Forest.
        
        Args:
            contamination: Expected fraction of outliers
            n_estimators: Number of trees
            
        Returns:
            Detection result as dictionary
        """
        return self.execute_worker(
            "isolation_forest",
            contamination=contamination,
            n_estimators=n_estimators
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_lof(self, n_neighbors: int = 20, contamination: float = 0.1) -> Dict[str, Any]:
        """Detect anomalies using Local Outlier Factor.
        
        Args:
            n_neighbors: Number of neighbors
            contamination: Expected fraction of anomalies
            
        Returns:
            Detection result as dictionary
        """
        return self.execute_worker(
            "lof",
            n_neighbors=n_neighbors,
            contamination=contamination
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_ocsvm(self, nu: float = 0.05, kernel: str = 'rbf') -> Dict[str, Any]:
        """Detect anomalies using One-Class SVM.
        
        Args:
            nu: Upper bound on fraction of anomalies
            kernel: Kernel type
            
        Returns:
            Detection result as dictionary
        """
        return self.execute_worker(
            "ocsvm",
            nu=nu,
            kernel=kernel
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_multivariate(
        self,
        covariance_type: str = 'full',
        contamination: float = 0.1,
    ) -> Dict[str, Any]:
        """Detect anomalies using Multivariate Gaussian.
        
        Args:
            covariance_type: Type of covariance matrix
            contamination: Expected fraction of anomalies
            
        Returns:
            Detection result as dictionary
        """
        return self.execute_worker(
            "multivariate",
            covariance_type=covariance_type,
            contamination=contamination
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_ensemble(self, threshold: float = 0.5) -> Dict[str, Any]:
        """Detect anomalies using ensemble voting.
        
        Args:
            threshold: Voting threshold
            
        Returns:
            Detection result as dictionary
        """
        return self.execute_worker(
            "ensemble",
            threshold=threshold
        )

    # ===== BATCH DETECTION =====

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_all(self, **kwargs) -> Dict[str, Any]:
        """Run all 6 anomaly detection methods.
        
        Args:
            **kwargs: Method-specific parameters
            
        Returns:
            Dictionary with all detection results
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("Comprehensive anomaly detection started")
        results = {}

        # Run all detections
        for worker_name in self.workers.keys():
            try:
                results[worker_name] = self.execute_worker(worker_name)
            except Exception as e:
                self.logger.warning(f"{worker_name} detection failed: {e}")
                results[worker_name] = {'success': False, 'error': str(e)}

        self.structured_logger.info("Comprehensive anomaly detection completed", {
            "methods": len(results)
        })

        return results

    # ===== REPORTING =====

    @retry_on_error(max_attempts=2, backoff=1)
    def summary_report(self) -> Dict[str, Any]:
        """Get summary of all anomaly detections.
        
        Returns:
            Dictionary with anomaly summary
        """
        successful_detections = [
            k for k, v in self.detection_results.items() if v.success
        ]
        failed_detections = [
            k for k, v in self.detection_results.items() if not v.success
        ]

        health_report = self.get_health_report()

        report = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "total_detections": len(self.detection_results),
            "successful": len(successful_detections),
            "failed": len(failed_detections),
            "successful_methods": successful_detections,
            "failed_methods": failed_detections,
            "health_report": health_report,
            "results": {
                k: v.to_dict() for k, v in self.detection_results.items()
            },
        }
        
        self.structured_logger.info("Summary report generated", {
            "total_detections": report["total_detections"],
            "successful": report["successful"],
            "failed": report["failed"]
        })

        return report

    @retry_on_error(max_attempts=2, backoff=1)
    def get_summary(self) -> str:
        """Get human-readable info about the agent state.
        
        Returns:
            Summary string
        """
        if self.data is None:
            return "AnomalyDetector: no data loaded"
        
        health_report = self.get_health_report()

        return (
            f"AnomalyDetector Summary:\n"
            f"  Rows: {self.data.shape[0]}\n"
            f"  Columns: {self.data.shape[1]}\n"
            f"  Workers: {len(self.workers)}\n"
            f"  Detections run: {len(self.detection_results)}\n"
            f"  Successful: {sum(1 for v in self.detection_results.values() if v.success)}\n"
            f"  Overall Health: {health_report['overall_health']:.1f}%\n"
            f"  Total Errors: {health_report['total_errors']}"
        )
