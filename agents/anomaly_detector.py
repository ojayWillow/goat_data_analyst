"""Anomaly Detector Agent - Outlier and anomaly detection.

Detects anomalies using statistical methods, isolation forests,
and clustering approaches.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from core.logger import get_logger
from core.exceptions import AgentError

logger = get_logger(__name__)


class AnomalyDetector:
    """Agent for anomaly and outlier detection.
    
    Capabilities:
    - IQR-based outlier detection
    - Z-score based detection
    - Isolation Forest detection
    - Modified Z-score detection
    - Local Outlier Factor
    - Anomaly scoring
    - Anomaly clustering
    - Statistical analysis of anomalies
    """
    
    def __init__(self):
        """Initialize Anomaly Detector agent."""
        self.name = "Anomaly Detector"
        self.data = None
        self.anomalies = {}
        
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available for advanced detection")
        
        logger.info(f"{self.name} initialized")
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data for anomaly detection.
        
        Args:
            df: DataFrame to analyze
        """
        self.data = df.copy()
        self.anomalies = {}
        logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data
    
    def iqr_detection(self, col: str, multiplier: float = 1.5) -> Dict[str, Any]:
        """Detect outliers using IQR method.
        
        Args:
            col: Column to analyze
            multiplier: IQR multiplier (default 1.5)
            
        Returns:
            Dictionary with outlier information
            
        Raises:
            AgentError: If column doesn't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if col not in self.data.columns:
            raise AgentError(f"Column '{col}' not found")
        
        try:
            logger.info(f"IQR detection on '{col}' with multiplier={multiplier}")
            
            series = self.data[col].dropna()
            
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            
            outliers_mask = (series < lower_bound) | (series > upper_bound)
            outlier_indices = series[outliers_mask].index.tolist()
            outlier_values = series[outliers_mask].values
            
            outlier_count = len(outlier_values)
            outlier_pct = (outlier_count / len(series) * 100) if len(series) > 0 else 0
            
            # Categorize outliers
            lower_outliers = series[series < lower_bound].values
            upper_outliers = series[series > upper_bound].values
            
            result = {
                "status": "success",
                "method": "IQR",
                "column": col,
                "multiplier": multiplier,
                "bounds": {
                    "lower": float(lower_bound),
                    "upper": float(upper_bound),
                },
                "statistics": {
                    "Q1": float(Q1),
                    "Q3": float(Q3),
                    "IQR": float(IQR),
                },
                "outliers_count": outlier_count,
                "outliers_percentage": round(outlier_pct, 2),
                "lower_outliers_count": len(lower_outliers),
                "upper_outliers_count": len(upper_outliers),
                "outlier_values": sorted(outlier_values)[:20],  # Top 20
                "outlier_indices": outlier_indices[:20],
            }
            
            self.anomalies[f"iqr_{col}"] = result
            return result
        
        except Exception as e:
            logger.error(f"IQR detection failed: {e}")
            raise AgentError(f"IQR detection failed: {e}")
    
    def zscore_detection(self, col: str, threshold: float = 3.0) -> Dict[str, Any]:
        """Detect outliers using Z-score method.
        
        Args:
            col: Column to analyze
            threshold: Z-score threshold (default 3.0)
            
        Returns:
            Dictionary with outlier information
            
        Raises:
            AgentError: If column doesn't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if col not in self.data.columns:
            raise AgentError(f"Column '{col}' not found")
        
        try:
            logger.info(f"Z-score detection on '{col}' with threshold={threshold}")
            
            series = self.data[col].dropna()
            
            mean = series.mean()
            std = series.std()
            
            if std == 0:
                return {"status": "error", "message": "Zero standard deviation"}
            
            z_scores = np.abs((series - mean) / std)
            outliers_mask = z_scores > threshold
            outlier_indices = series[outliers_mask].index.tolist()
            outlier_values = series[outliers_mask].values
            
            outlier_count = len(outlier_values)
            outlier_pct = (outlier_count / len(series) * 100) if len(series) > 0 else 0
            
            result = {
                "status": "success",
                "method": "Z-Score",
                "column": col,
                "threshold": threshold,
                "statistics": {
                    "mean": float(mean),
                    "std": float(std),
                },
                "outliers_count": outlier_count,
                "outliers_percentage": round(outlier_pct, 2),
                "outlier_values": sorted(outlier_values)[:20],
                "outlier_indices": outlier_indices[:20],
                "z_score_range": [float(z_scores.min()), float(z_scores.max())],
            }
            
            self.anomalies[f"zscore_{col}"] = result
            return result
        
        except Exception as e:
            logger.error(f"Z-score detection failed: {e}")
            raise AgentError(f"Z-score detection failed: {e}")
    
    def modified_zscore_detection(self, col: str, threshold: float = 3.5) -> Dict[str, Any]:
        """Detect outliers using Modified Z-score method (more robust).
        
        Args:
            col: Column to analyze
            threshold: Modified Z-score threshold (default 3.5)
            
        Returns:
            Dictionary with outlier information
            
        Raises:
            AgentError: If column doesn't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if col not in self.data.columns:
            raise AgentError(f"Column '{col}' not found")
        
        try:
            logger.info(f"Modified Z-score detection on '{col}' with threshold={threshold}")
            
            series = self.data[col].dropna()
            
            median = series.median()
            mad = stats.median_abs_deviation(series)
            
            if mad == 0:
                return {"status": "error", "message": "Zero MAD"}
            
            modified_z_scores = 0.6745 * (series - median) / mad
            outliers_mask = np.abs(modified_z_scores) > threshold
            outlier_indices = series[outliers_mask].index.tolist()
            outlier_values = series[outliers_mask].values
            
            outlier_count = len(outlier_values)
            outlier_pct = (outlier_count / len(series) * 100) if len(series) > 0 else 0
            
            result = {
                "status": "success",
                "method": "Modified Z-Score",
                "column": col,
                "threshold": threshold,
                "statistics": {
                    "median": float(median),
                    "mad": float(mad),
                },
                "outliers_count": outlier_count,
                "outliers_percentage": round(outlier_pct, 2),
                "outlier_values": sorted(outlier_values)[:20],
                "outlier_indices": outlier_indices[:20],
            }
            
            self.anomalies[f"mod_zscore_{col}"] = result
            return result
        
        except Exception as e:
            logger.error(f"Modified Z-score detection failed: {e}")
            raise AgentError(f"Modified Z-score detection failed: {e}")
    
    def isolation_forest_detection(self, feature_cols: List[str], contamination: float = 0.1) -> Dict[str, Any]:
        """Detect anomalies using Isolation Forest.
        
        Args:
            feature_cols: Columns to use for detection
            contamination: Expected fraction of outliers (0.0-1.0)
            
        Returns:
            Dictionary with anomaly information
            
        Raises:
            AgentError: If sklearn not available or invalid params
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if not SKLEARN_AVAILABLE:
            raise AgentError("scikit-learn not installed")
        
        for col in feature_cols:
            if col not in self.data.columns:
                raise AgentError(f"Column '{col}' not found")
        
        if not 0 < contamination < 1:
            raise AgentError("contamination must be between 0 and 1")
        
        try:
            logger.info(f"Isolation Forest detection with contamination={contamination}")
            
            df_clean = self.data[feature_cols].dropna()
            
            if len(df_clean) < 2:
                raise AgentError("Insufficient data")
            
            # Train Isolation Forest
            iso_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            
            predictions = iso_forest.fit_predict(df_clean)
            anomaly_scores = iso_forest.score_samples(df_clean)
            
            anomaly_mask = predictions == -1
            anomaly_indices = df_clean[anomaly_mask].index.tolist()
            anomaly_count = anomaly_mask.sum()
            anomaly_pct = (anomaly_count / len(df_clean) * 100) if len(df_clean) > 0 else 0
            
            # Sort by anomaly score
            anomaly_df = pd.DataFrame({
                'index': df_clean.index,
                'anomaly_score': anomaly_scores,
                'is_anomaly': predictions
            }).sort_values('anomaly_score')
            
            result = {
                "status": "success",
                "method": "Isolation Forest",
                "features": feature_cols,
                "contamination": contamination,
                "total_samples": len(df_clean),
                "anomalies_count": int(anomaly_count),
                "anomalies_percentage": round(anomaly_pct, 2),
                "anomaly_score_range": [float(anomaly_scores.min()), float(anomaly_scores.max())],
                "top_anomalies": anomaly_df[anomaly_df['is_anomaly'] == -1].head(20).to_dict(orient="records"),
            }
            
            self.anomalies[f"isolation_forest"] = result
            return result
        
        except Exception as e:
            logger.error(f"Isolation Forest detection failed: {e}")
            raise AgentError(f"Isolation Forest detection failed: {e}")
    
    def multivariate_analysis(self, feature_cols: List[str]) -> Dict[str, Any]:
        """Perform multivariate outlier analysis.
        
        Args:
            feature_cols: Columns to analyze
            
        Returns:
            Dictionary with multivariate statistics
            
        Raises:
            AgentError: If columns don't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        for col in feature_cols:
            if col not in self.data.columns:
                raise AgentError(f"Column '{col}' not found")
        
        try:
            logger.info(f"Multivariate analysis on {len(feature_cols)} features")
            
            df_clean = self.data[feature_cols].dropna()
            
            # Calculate Mahalanobis distance
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(df_clean)
            
            cov_matrix = np.cov(scaled_data.T)
            mean = scaled_data.mean(axis=0)
            
            # Calculate Mahalanobis distance for each point
            inv_cov = np.linalg.pinv(cov_matrix)
            distances = []
            
            for point in scaled_data:
                diff = point - mean
                distance = np.sqrt(diff.dot(inv_cov).dot(diff.T))
                distances.append(distance)
            
            distances = np.array(distances)
            threshold = np.percentile(distances, 95)
            
            outlier_mask = distances > threshold
            outlier_count = outlier_mask.sum()
            outlier_pct = (outlier_count / len(df_clean) * 100) if len(df_clean) > 0 else 0
            
            result = {
                "status": "success",
                "method": "Mahalanobis Distance",
                "features": feature_cols,
                "samples": len(df_clean),
                "distance_threshold": float(threshold),
                "outliers_count": int(outlier_count),
                "outliers_percentage": round(outlier_pct, 2),
                "distance_statistics": {
                    "mean": float(distances.mean()),
                    "std": float(distances.std()),
                    "min": float(distances.min()),
                    "max": float(distances.max()),
                },
            }
            
            self.anomalies[f"mahalanobis"] = result
            return result
        
        except Exception as e:
            logger.error(f"Multivariate analysis failed: {e}")
            raise AgentError(f"Multivariate analysis failed: {e}")
    
    def summary_report(self) -> Dict[str, Any]:
        """Get summary of all anomaly detections.
        
        Returns:
            Dictionary with anomaly summary
        """
        return {
            "status": "success",
            "total_analyses": len(self.anomalies),
            "methods_used": list(self.anomalies.keys()),
            "analyses": self.anomalies,
        }
