"""Anomaly Detector Agent - Coordinates anomaly detection workers.

Detects anomalies using 4 different algorithms:
- Local Outlier Factor (LOF)
- One-Class SVM
- Isolation Forest
- Ensemble (voting from all 3)

Integrated with Week 1 Systems:
- Structured logging with metrics
- Automatic retry with exponential backoff
- Error recovery and handling
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
from .workers import (
    LOFAnomalyDetector,
    OneClassSVMAnomalyDetector,
    IsolationForestAnomalyDetector,
    EnsembleAnomalyDetector,
    WorkerResult,
)

logger = get_logger(__name__)
structured_logger = get_structured_logger(__name__)


class AnomalyDetector:
    """Anomaly Detector Agent - coordinates anomaly detection workers.
    
    Manages 4 workers:
    - LOFAnomalyDetector: Local Outlier Factor algorithm
    - OneClassSVMAnomalyDetector: One-Class SVM algorithm
    - IsolationForestAnomalyDetector: Isolation Forest algorithm
    - EnsembleAnomalyDetector: Ensemble voting method
    
    Week 1 Day 3 Implementation:
    - Agent coordinates all workers (doesn't implement)
    - Each worker extends BaseWorker
    - Methods delegate to workers
    - Pure coordinator pattern
    """

    def __init__(self) -> None:
        """Initialize the Anomaly Detector agent and all workers."""
        self.name = "AnomalyDetector"
        self.logger = get_logger("AnomalyDetector")
        self.structured_logger = get_structured_logger("AnomalyDetector")
        self.data: Optional[pd.DataFrame] = None
        self.detection_results: Dict[str, WorkerResult] = {}

        # === INITIALIZE ALL WORKERS ===
        self.lof_detector = LOFAnomalyDetector()
        self.ocsvm_detector = OneClassSVMAnomalyDetector()
        self.isolation_forest_detector = IsolationForestAnomalyDetector()
        self.ensemble_detector = EnsembleAnomalyDetector()

        self.workers = [
            self.lof_detector,
            self.ocsvm_detector,
            self.isolation_forest_detector,
            self.ensemble_detector,
        ]

        self.logger.info("AnomalyDetector initialized with 4 detection workers")
        self.structured_logger.info("AnomalyDetector initialized", {
            "workers": 4,
            "worker_names": [
                "LOFAnomalyDetector",
                "OneClassSVMAnomalyDetector",
                "IsolationForestAnomalyDetector",
                "EnsembleAnomalyDetector"
            ]
        })

    # === DATA MANAGEMENT ===

    def set_data(self, df: pd.DataFrame) -> None:
        """Store the DataFrame for anomaly detection.
        
        Args:
            df: DataFrame to analyze
        """
        self.data = df.copy()
        self.detection_results = {}
        self.logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
        self.structured_logger.info("Data set for anomaly detection", {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "numeric_cols": len(df.select_dtypes(include=['number']).columns)
        })

    def get_data(self) -> Optional[pd.DataFrame]:
        """Retrieve the stored DataFrame.
        
        Returns:
            DataFrame or None if not set
        """
        return self.data

    # === DETECTION METHODS - DELEGATE TO WORKERS ===

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_lof(self, n_neighbors: int = 20, contamination: float = 0.1) -> Dict[str, Any]:
        """Detect anomalies using Local Outlier Factor.
        
        Args:
            n_neighbors: Number of neighbors to use
            contamination: Expected proportion of anomalies
            
        Returns:
            Detection result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("LOF detection started", {
            "n_neighbors": n_neighbors,
            "contamination": contamination
        })

        try:
            worker_result = self.lof_detector.safe_execute(
                df=self.data,
                n_neighbors=n_neighbors,
                contamination=contamination,
            )

            self.detection_results["lof"] = worker_result
            self.structured_logger.info("LOF detection completed", {"success": worker_result.success})
            
            return worker_result.to_dict()
        except Exception as e:
            self.structured_logger.error("LOF detection failed", {"error": str(e)})
            raise

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_ocsvm(self, nu: float = 0.05, kernel: str = 'rbf') -> Dict[str, Any]:
        """Detect anomalies using One-Class SVM.
        
        Args:
            nu: Upper bound on fraction of anomalies
            kernel: Kernel type ('rbf', 'linear', 'poly')
            
        Returns:
            Detection result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("One-Class SVM detection started", {
            "nu": nu,
            "kernel": kernel
        })

        try:
            worker_result = self.ocsvm_detector.safe_execute(
                df=self.data,
                nu=nu,
                kernel=kernel,
            )

            self.detection_results["ocsvm"] = worker_result
            self.structured_logger.info("One-Class SVM detection completed", {"success": worker_result.success})
            
            return worker_result.to_dict()
        except Exception as e:
            self.structured_logger.error("One-Class SVM detection failed", {"error": str(e)})
            raise

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_isolation_forest(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
    ) -> Dict[str, Any]:
        """Detect anomalies using Isolation Forest.
        
        Args:
            contamination: Expected fraction of outliers (0.0-1.0)
            n_estimators: Number of trees (default 100)
            
        Returns:
            Detection result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("Isolation Forest detection started", {
            "contamination": contamination,
            "n_estimators": n_estimators
        })

        try:
            worker_result = self.isolation_forest_detector.safe_execute(
                df=self.data,
                contamination=contamination,
                n_estimators=n_estimators,
            )

            self.detection_results["isolation_forest"] = worker_result
            self.structured_logger.info("Isolation Forest detection completed", {"success": worker_result.success})
            
            return worker_result.to_dict()
        except Exception as e:
            self.structured_logger.error("Isolation Forest detection failed", {"error": str(e)})
            raise

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_ensemble(self, threshold: float = 0.5) -> Dict[str, Any]:
        """Detect anomalies using ensemble voting method.
        
        Args:
            threshold: Voting threshold (0-1)
            
        Returns:
            Detection result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("Ensemble detection started", {"threshold": threshold})

        try:
            worker_result = self.ensemble_detector.safe_execute(
                df=self.data,
                threshold=threshold,
            )

            self.detection_results["ensemble"] = worker_result
            self.structured_logger.info("Ensemble detection completed", {"success": worker_result.success})
            
            return worker_result.to_dict()
        except Exception as e:
            self.structured_logger.error("Ensemble detection failed", {"error": str(e)})
            raise

    # === BATCH DETECTION ===

    @retry_on_error(max_attempts=3, backoff=2)
    def detect_all(
        self,
        lof_params: Optional[Dict[str, Any]] = None,
        ocsvm_params: Optional[Dict[str, Any]] = None,
        iforest_params: Optional[Dict[str, Any]] = None,
        ensemble_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run all 4 anomaly detection methods.
        
        Args:
            lof_params: Parameters for LOF
            ocsvm_params: Parameters for One-Class SVM
            iforest_params: Parameters for Isolation Forest
            ensemble_params: Parameters for Ensemble
            
        Returns:
            Dictionary with all detection results
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("Comprehensive anomaly detection started")

        results = {}

        # Default parameters
        lof_params = lof_params or {}
        ocsvm_params = ocsvm_params or {}
        iforest_params = iforest_params or {}
        ensemble_params = ensemble_params or {}

        # Run all detections
        try:
            results["lof"] = self.detect_lof(**lof_params)
        except Exception as e:
            self.logger.warning(f"LOF detection failed: {e}")

        try:
            results["ocsvm"] = self.detect_ocsvm(**ocsvm_params)
        except Exception as e:
            self.logger.warning(f"One-Class SVM detection failed: {e}")

        try:
            results["isolation_forest"] = self.detect_isolation_forest(**iforest_params)
        except Exception as e:
            self.logger.warning(f"Isolation Forest detection failed: {e}")

        try:
            results["ensemble"] = self.detect_ensemble(**ensemble_params)
        except Exception as e:
            self.logger.warning(f"Ensemble detection failed: {e}")

        self.structured_logger.info("Comprehensive anomaly detection completed", {
            "methods": len(results)
        })

        return results

    # === REPORTING ===

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

        report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_detections": len(self.detection_results),
            "successful": len(successful_detections),
            "failed": len(failed_detections),
            "successful_methods": successful_detections,
            "failed_methods": failed_detections,
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

    def get_summary(self) -> str:
        """Get human-readable info about the agent state.
        
        Returns:
            Summary string
        """
        if self.data is None:
            return "AnomalyDetector: no data loaded"

        return (
            f"AnomalyDetector Summary:\n"
            f"  Rows: {self.data.shape[0]}\n"
            f"  Columns: {self.data.shape[1]}\n"
            f"  Workers: {len(self.workers)}\n"
            f"  Detections run: {len(self.detection_results)}\n"
            f"  Successful: {sum(1 for v in self.detection_results.values() if v.success)}"
        )
