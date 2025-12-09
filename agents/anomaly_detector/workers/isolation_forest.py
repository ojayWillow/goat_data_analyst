"""Isolation Forest Worker - ML-based anomaly detection."""

import pandas as pd
import numpy as np
from typing import Any, Dict, List

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = get_logger(__name__)


class IsolationForestWorker(BaseWorker):
    """Worker that performs Isolation Forest anomaly detection.
    
    Isolation Forest is an ensemble method that isolates anomalies by randomly
    selecting features and split values. Anomalies are isolated closer to the
    root of the trees, so they require fewer splits to isolate.
    """
    
    def __init__(self):
        """Initialize IsolationForestWorker."""
        super().__init__("IsolationForestWorker")
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available - Isolation Forest detection disabled")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute Isolation Forest anomaly detection.
        
        Args:
            df: DataFrame to analyze
            feature_cols: List of columns to use for detection
            contamination: Expected fraction of outliers (0.0-1.0, default 0.1)
            n_estimators: Number of trees (default 100)
            random_state: Random seed (default 42)
            
        Returns:
            WorkerResult with anomaly detection results
        """
        return self.safe_execute(**kwargs)
    
    def execute(self, **kwargs) -> WorkerResult:
        """Actual implementation of Isolation Forest detection."""
        df = kwargs.get('df')
        feature_cols = kwargs.get('feature_cols', [])
        contamination = kwargs.get('contamination', 0.1)
        n_estimators = kwargs.get('n_estimators', 100)
        random_state = kwargs.get('random_state', 42)
        
        # Create empty result
        result = self._create_result(
            task_type="isolation_forest_detection",
            quality_score=1.0
        )
        
        # Validate sklearn availability
        if not SKLEARN_AVAILABLE:
            self._add_error(result, ErrorType.SKLEARN_UNAVAILABLE, "scikit-learn not installed")
            result.success = False
            return result
        
        # Validate inputs
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        if not feature_cols:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "No feature columns specified")
            result.success = False
            return result
        
        # Validate feature columns exist
        missing_cols = [col for col in feature_cols if col not in df.columns]
        if missing_cols:
            self._add_error(result, ErrorType.INVALID_COLUMN, f"Columns not found: {missing_cols}")
            result.success = False
            return result
        
        # Validate contamination parameter
        if not (0 < contamination < 1):
            self._add_error(result, ErrorType.INVALID_PARAMETER, "contamination must be between 0 and 1")
            result.success = False
            return result
        
        try:
            # Extract features and drop NaNs
            df_clean = df[feature_cols].dropna()
            
            if len(df_clean) < 2:
                self._add_error(result, ErrorType.INSUFFICIENT_DATA, "Insufficient data after removing NaNs")
                result.success = False
                return result
            
            # Train Isolation Forest
            iso_forest = IsolationForest(
                contamination=contamination,
                n_estimators=n_estimators,
                random_state=random_state,
                n_jobs=-1
            )
            
            predictions = iso_forest.fit_predict(df_clean)
            anomaly_scores = iso_forest.score_samples(df_clean)
            
            # Identify anomalies
            anomaly_mask = predictions == -1
            anomaly_indices = df_clean[anomaly_mask].index.tolist()
            anomaly_count = anomaly_mask.sum()
            anomaly_pct = (anomaly_count / len(df_clean) * 100) if len(df_clean) > 0 else 0
            
            # Create anomaly dataframe with scores
            anomaly_df = pd.DataFrame({
                'index': df_clean.index,
                'anomaly_score': anomaly_scores,
                'is_anomaly': predictions
            }).sort_values('anomaly_score')
            
            top_anomalies = anomaly_df[anomaly_df['is_anomaly'] == -1].head(20).to_dict(orient="records")
            
            result.data = {
                "method": "Isolation Forest",
                "features": feature_cols,
                "total_samples": len(df_clean),
                "anomalies_count": int(anomaly_count),
                "anomalies_percentage": round(anomaly_pct, 2),
                "contamination": contamination,
                "n_estimators": n_estimators,
                "anomaly_score_range": [float(anomaly_scores.min()), float(anomaly_scores.max())],
                "anomaly_score_mean": float(anomaly_scores.mean()),
                "anomaly_score_std": float(anomaly_scores.std()),
                "top_anomalies": top_anomalies,
            }
            
            logger.info(f"Isolation Forest: {anomaly_count} anomalies ({anomaly_pct:.2f}%)")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, str(e))
            result.success = False
            return result
