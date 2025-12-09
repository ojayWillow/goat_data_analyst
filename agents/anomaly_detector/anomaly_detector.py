"""Anomaly Detector Agent - Coordinates anomaly detection workers.

Detects anomalies using statistical methods, isolation forests,
and multivariate analysis.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from core.exceptions import AgentError
from .workers import (
    StatisticalWorker,
    IsolationForestWorker,
    MultivariateWorker,
    WorkerResult,
)

logger = get_logger(__name__)


class AnomalyDetector:
    """Anomaly Detector Agent - coordinates anomaly detection workers.
    
    Capabilities:
    - Statistical detection: IQR, Z-score, Modified Z-score
    - ML detection: Isolation Forest
    - Multivariate detection: Mahalanobis distance
    - Summary reporting of all detections
    """

    def __init__(self) -> None:
        """Initialize the Anomaly Detector agent and all workers."""
        self.name = "Anomaly Detector"
        self.logger = get_logger("AnomalyDetector")
        self.data: Optional[pd.DataFrame] = None
        self.detection_results: Dict[str, WorkerResult] = {}

        # === SECTION 1: INITIALIZE ALL WORKERS ===
        self.statistical_worker = StatisticalWorker()
        self.isolation_forest_worker = IsolationForestWorker()
        self.multivariate_worker = MultivariateWorker()

        self.logger.info("AnomalyDetector initialized with 3 detection workers")

    # === SECTION 2: DATA MANAGEMENT ===

    def set_data(self, df: pd.DataFrame) -> None:
        """Store the DataFrame for anomaly detection.
        
        Args:
            df: DataFrame to analyze
        """
        self.data = df.copy()
        self.detection_results = {}
        self.logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")

    def get_data(self) -> Optional[pd.DataFrame]:
        """Retrieve the stored DataFrame.
        
        Returns:
            DataFrame or None if not set
        """
        return self.data

    # === SECTION 3: STATISTICAL DETECTION METHODS ===

    def detect_iqr(
        self,
        column: str,
        multiplier: float = 1.5,
    ) -> Dict[str, Any]:
        """Detect outliers using IQR method.
        
        Args:
            column: Column to analyze
            multiplier: IQR multiplier (default 1.5)
            
        Returns:
            Detection result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        worker_result = self.statistical_worker.safe_execute(
            df=self.data,
            column=column,
            method="iqr",
            multiplier=multiplier,
        )

        self.detection_results[f"iqr_{column}"] = worker_result
        return worker_result.to_dict()

    def detect_zscore(
        self,
        column: str,
        threshold: float = 3.0,
    ) -> Dict[str, Any]:
        """Detect outliers using Z-score method.
        
        Args:
            column: Column to analyze
            threshold: Z-score threshold (default 3.0)
            
        Returns:
            Detection result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        worker_result = self.statistical_worker.safe_execute(
            df=self.data,
            column=column,
            method="zscore",
            threshold=threshold,
        )

        self.detection_results[f"zscore_{column}"] = worker_result
        return worker_result.to_dict()

    def detect_modified_zscore(
        self,
        column: str,
        threshold: float = 3.5,
    ) -> Dict[str, Any]:
        """Detect outliers using Modified Z-score method (more robust).
        
        Args:
            column: Column to analyze
            threshold: Modified Z-score threshold (default 3.5)
            
        Returns:
            Detection result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        worker_result = self.statistical_worker.safe_execute(
            df=self.data,
            column=column,
            method="modified_zscore",
            mod_threshold=threshold,
        )

        self.detection_results[f"mod_zscore_{column}"] = worker_result
        return worker_result.to_dict()

    # === SECTION 4: ML DETECTION METHODS ===

    def detect_isolation_forest(
        self,
        feature_cols: List[str],
        contamination: float = 0.1,
        n_estimators: int = 100,
    ) -> Dict[str, Any]:
        """Detect anomalies using Isolation Forest.
        
        Args:
            feature_cols: Columns to use for detection
            contamination: Expected fraction of outliers (0.0-1.0)
            n_estimators: Number of trees (default 100)
            
        Returns:
            Detection result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        worker_result = self.isolation_forest_worker.safe_execute(
            df=self.data,
            feature_cols=feature_cols,
            contamination=contamination,
            n_estimators=n_estimators,
        )

        self.detection_results["isolation_forest"] = worker_result
        return worker_result.to_dict()

    # === SECTION 5: MULTIVARIATE DETECTION METHODS ===

    def detect_multivariate(
        self,
        feature_cols: List[str],
        percentile: int = 95,
    ) -> Dict[str, Any]:
        """Perform multivariate outlier detection (Mahalanobis distance).
        
        Args:
            feature_cols: Columns to analyze
            percentile: Percentile threshold for outliers (default 95)
            
        Returns:
            Detection result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        worker_result = self.multivariate_worker.safe_execute(
            df=self.data,
            feature_cols=feature_cols,
            percentile=percentile,
        )

        self.detection_results["multivariate"] = worker_result
        return worker_result.to_dict()

    # === SECTION 6: BATCH DETECTION METHODS ===

    def detect_all_statistical(
        self,
        column: str,
        iqr_multiplier: float = 1.5,
        zscore_threshold: float = 3.0,
        mod_zscore_threshold: float = 3.5,
    ) -> Dict[str, Any]:
        """Run all statistical detection methods on a column.
        
        Args:
            column: Column to analyze
            iqr_multiplier: IQR multiplier
            zscore_threshold: Z-score threshold
            mod_zscore_threshold: Modified Z-score threshold
            
        Returns:
            Dictionary with results from all methods
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        results = {
            "iqr": self.detect_iqr(column, iqr_multiplier),
            "zscore": self.detect_zscore(column, zscore_threshold),
            "modified_zscore": self.detect_modified_zscore(column, mod_zscore_threshold),
        }

        return results

    def detect_all(
        self,
        statistical_cols: List[str],
        ml_feature_cols: List[str],
        multivariate_cols: Optional[List[str]] = None,
        contamination: float = 0.1,
    ) -> Dict[str, Any]:
        """Run all detection methods (statistical, ML, multivariate).
        
        Args:
            statistical_cols: Columns for statistical detection
            ml_feature_cols: Columns for Isolation Forest
            multivariate_cols: Columns for multivariate (default: ml_feature_cols)
            contamination: Contamination for Isolation Forest
            
        Returns:
            Dictionary with all detection results
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        if multivariate_cols is None:
            multivariate_cols = ml_feature_cols

        results = {}

        # Statistical detection on each column
        for col in statistical_cols:
            if col in self.data.columns:
                results[f"statistical_{col}"] = self.detect_all_statistical(col)

        # Isolation Forest on feature columns
        if ml_feature_cols:
            results["isolation_forest"] = self.detect_isolation_forest(
                ml_feature_cols,
                contamination,
            )

        # Multivariate detection
        if multivariate_cols:
            results["multivariate"] = self.detect_multivariate(multivariate_cols)

        return results

    # === SECTION 7: REPORTING ===

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

        return {
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
            f"  Detections run: {len(self.detection_results)}\n"
            f"  Successful: {sum(1 for v in self.detection_results.values() if v.success)}"
        )
