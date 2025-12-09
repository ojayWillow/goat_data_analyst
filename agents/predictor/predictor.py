"""Predictor Agent - Coordinates ML model training and forecasting workers."""

from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

from core.logger import get_logger
from .workers import (
    LinearRegressionWorker,
    DecisionTreeWorker,
    TimeSeriesWorker,
    ModelValidatorWorker,
    WorkerResult,
)

logger = get_logger("Predictor")


class Predictor:
    """Predictor Agent - Trains ML models and makes predictions.
    
    Coordinates 4 specialized workers:
    1. LinearRegressionWorker - Simple linear regression
    2. DecisionTreeWorker - Tree-based predictions
    3. TimeSeriesWorker - Time series forecasting
    4. ModelValidatorWorker - Model validation & comparison
    """
    
    def __init__(self):
        """Initialize Predictor Agent with all workers."""
        self.name = "Predictor"
        self.logger = get_logger("Predictor")
        self.data: Optional[pd.DataFrame] = None
        self.prediction_results: Dict[str, WorkerResult] = {}
        
        # Initialize workers
        self.linear_regression_worker = LinearRegressionWorker()
        self.decision_tree_worker = DecisionTreeWorker()
        self.time_series_worker = TimeSeriesWorker()
        self.model_validator_worker = ModelValidatorWorker()
        
        self.logger.info("Predictor initialized with 4 workers")
    
    # ===== DATA MANAGEMENT =====
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Store DataFrame for all workers to use.
        
        Args:
            df: Input DataFrame
        """
        self.data = df.copy()
        self.prediction_results = {}
        self.logger.info(f"Data set: {df.shape}")
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Retrieve the stored DataFrame.
        
        Returns:
            Stored DataFrame or None
        """
        return self.data
    
    # ===== LINEAR REGRESSION =====
    
    def predict_linear(
        self,
        features: List[str],
        target: str,
    ) -> Dict[str, Any]:
        """Linear regression prediction.
        
        Args:
            features: List of feature column names
            target: Target column name
            
        Returns:
            Dictionary with predictions and metrics
        """
        if self.data is None:
            return {"success": False, "error": "No data set"}
        
        result = self.linear_regression_worker.safe_execute(
            df=self.data,
            features=features,
            target=target,
        )
        
        self.prediction_results["linear_regression"] = result
        return result.to_dict()
    
    # ===== DECISION TREE =====
    
    def predict_tree(
        self,
        features: List[str],
        target: str,
        mode: str = 'auto',
        max_depth: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Decision tree prediction.
        
        Args:
            features: List of feature column names
            target: Target column name
            mode: 'regression', 'classification', or 'auto'
            max_depth: Maximum tree depth
            
        Returns:
            Dictionary with predictions and feature importance
        """
        if self.data is None:
            return {"success": False, "error": "No data set"}
        
        result = self.decision_tree_worker.safe_execute(
            df=self.data,
            features=features,
            target=target,
            mode=mode,
            max_depth=max_depth,
        )
        
        self.prediction_results["decision_tree"] = result
        return result.to_dict()
    
    # ===== TIME SERIES =====
    
    def forecast_timeseries(
        self,
        series_column: str,
        periods: int = 12,
        method: str = 'auto',
        decompose: bool = True,
    ) -> Dict[str, Any]:
        """Time series forecasting.
        
        Args:
            series_column: Column name with time series data
            periods: Number of periods to forecast
            method: 'arima', 'exponential_smoothing', or 'auto'
            decompose: Whether to decompose time series
            
        Returns:
            Dictionary with forecasts and confidence intervals
        """
        if self.data is None:
            return {"success": False, "error": "No data set"}
        
        if series_column not in self.data.columns:
            return {"success": False, "error": f"Column '{series_column}' not found"}
        
        result = self.time_series_worker.safe_execute(
            series=self.data[series_column],
            periods=periods,
            method=method,
            decompose=decompose,
        )
        
        self.prediction_results["time_series"] = result
        return result.to_dict()
    
    # ===== MODEL VALIDATION =====
    
    def validate_model(
        self,
        features: List[str],
        target: str,
        model_type: str = 'linear',
        cv_folds: int = 5,
    ) -> Dict[str, Any]:
        """Validate model with cross-validation.
        
        Args:
            features: List of feature column names
            target: Target column name
            model_type: 'linear' or 'tree'
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary with validation metrics
        """
        if self.data is None:
            return {"success": False, "error": "No data set"}
        
        X = self.data[features].values
        y = self.data[target].values
        
        result = self.model_validator_worker.safe_execute(
            X=X,
            y=y,
            model_type=model_type,
            cv_folds=cv_folds,
        )
        
        self.prediction_results["validation"] = result
        return result.to_dict()
    
    # ===== SUMMARY & REPORTING =====
    
    def summary_report(self) -> Dict[str, Any]:
        """Generate summary of all predictions.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.prediction_results:
            return {"message": "No predictions yet"}
        
        successful = [k for k, v in self.prediction_results.items() if v.success]
        failed = [k for k, v in self.prediction_results.items() if not v.success]
        
        return {
            "total_predictions": len(self.prediction_results),
            "successful": len(successful),
            "failed": len(failed),
            "successful_models": successful,
            "failed_models": failed,
            "results": {
                k: v.to_dict() for k, v in self.prediction_results.items()
            },
        }
