"""Predictor Agent - Coordinates ML model training and forecasting workers.

Integrated with Week 1 Systems:
- Structured logging with metrics
- Automatic retry with exponential backoff
- Error recovery and handling
"""

from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
from .workers import (
    LinearRegression,
    DecisionTree,
    TimeSeries,
    ModelValidator,
    WorkerResult,
)

logger = get_logger("Predictor")
structured_logger = get_structured_logger("Predictor")


class Predictor:
    """Predictor Agent - Trains ML models and makes predictions.
    
    Coordinates 4 specialized workers:
    1. LinearRegression - Simple linear regression
    2. DecisionTree - Tree-based predictions
    3. TimeSeries - Time series forecasting
    4. ModelValidator - Model validation & comparison
    
    Week 1 Integration:
    - Structured logging with metrics at each step
    - Automatic retry on transient failures
    - Error recovery and detailed error messages
    """
    
    def __init__(self):
        """Initialize Predictor Agent with all workers."""
        self.name = "Predictor"
        self.logger = get_logger("Predictor")
        self.structured_logger = get_structured_logger("Predictor")
        self.data: Optional[pd.DataFrame] = None
        self.prediction_results: Dict[str, WorkerResult] = {}
        
        # Initialize workers
        self.linear_regression_worker = LinearRegression()
        self.decision_tree_worker = DecisionTree()
        self.time_series_worker = TimeSeries()
        self.model_validator_worker = ModelValidator()
        
        self.logger.info("Predictor initialized with 4 workers")
        self.structured_logger.info("Predictor initialized", {
            "workers": 4,
            "worker_names": [
                "LinearRegression",
                "DecisionTree",
                "TimeSeries",
                "ModelValidator"
            ]
        })
    
    # ===== DATA MANAGEMENT =====
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Store DataFrame for all workers to use.
        
        Args:
            df: Input DataFrame
        """
        self.data = df.copy()
        self.prediction_results = {}
        self.logger.info(f"Data set: {df.shape}")
        self.structured_logger.info("Data set for prediction", {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "dtypes": dict(df.dtypes.astype(str).value_counts())
        })
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Retrieve the stored DataFrame.
        
        Returns:
            Stored DataFrame or None
        """
        return self.data
    
    # ===== LINEAR REGRESSION =====
    
    @retry_on_error(max_attempts=3, backoff=2)
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
            error_msg = "No data set"
            self.structured_logger.error("Linear regression prediction failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Linear regression started", {
            "features": len(features),
            "target": target,
            "rows": self.data.shape[0]
        })
        
        try:
            result = self.linear_regression_worker.safe_execute(
                df=self.data,
                features=features,
                target=target,
            )
            
            self.prediction_results["linear_regression"] = result
            
            self.structured_logger.info("Linear regression completed", {
                "success": result.success,
                "features": len(features)
            })
            
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Linear regression failed", {
                "features": len(features),
                "error": str(e)
            })
            raise AgentError(f"Prediction failed: {e}")
    
    # ===== DECISION TREE =====
    
    @retry_on_error(max_attempts=3, backoff=2)
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
            error_msg = "No data set"
            self.structured_logger.error("Decision tree prediction failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Decision tree prediction started", {
            "features": len(features),
            "target": target,
            "mode": mode,
            "max_depth": max_depth
        })
        
        try:
            result = self.decision_tree_worker.safe_execute(
                df=self.data,
                features=features,
                target=target,
                mode=mode,
                max_depth=max_depth,
            )
            
            self.prediction_results["decision_tree"] = result
            
            self.structured_logger.info("Decision tree prediction completed", {
                "success": result.success,
                "features": len(features),
                "mode": mode
            })
            
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Decision tree prediction failed", {
                "features": len(features),
                "error": str(e)
            })
            raise AgentError(f"Prediction failed: {e}")
    
    # ===== TIME SERIES =====
    
    @retry_on_error(max_attempts=3, backoff=2)
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
            error_msg = "No data set"
            self.structured_logger.error("Time series forecasting failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        if series_column not in self.data.columns:
            error_msg = f"Column '{series_column}' not found"
            self.structured_logger.error("Time series forecasting failed", {
                "error": error_msg,
                "column": series_column
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Time series forecasting started", {
            "series_column": series_column,
            "periods": periods,
            "method": method,
            "decompose": decompose
        })
        
        try:
            result = self.time_series_worker.safe_execute(
                series=self.data[series_column],
                periods=periods,
                method=method,
                decompose=decompose,
            )
            
            self.prediction_results["time_series"] = result
            
            self.structured_logger.info("Time series forecasting completed", {
                "success": result.success,
                "periods": periods,
                "method": method
            })
            
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Time series forecasting failed", {
                "series_column": series_column,
                "periods": periods,
                "error": str(e)
            })
            raise AgentError(f"Forecasting failed: {e}")
    
    # ===== MODEL VALIDATION =====
    
    @retry_on_error(max_attempts=3, backoff=2)
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
            error_msg = "No data set"
            self.structured_logger.error("Model validation failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Model validation started", {
            "features": len(features),
            "target": target,
            "model_type": model_type,
            "cv_folds": cv_folds
        })
        
        try:
            X = self.data[features].values
            y = self.data[target].values
            
            result = self.model_validator_worker.safe_execute(
                X=X,
                y=y,
                model_type=model_type,
                cv_folds=cv_folds,
            )
            
            self.prediction_results["validation"] = result
            
            self.structured_logger.info("Model validation completed", {
                "success": result.success,
                "model_type": model_type,
                "cv_folds": cv_folds
            })
            
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Model validation failed", {
                "features": len(features),
                "model_type": model_type,
                "error": str(e)
            })
            raise AgentError(f"Validation failed: {e}")
    
    # ===== SUMMARY & REPORTING =====
    
    def summary_report(self) -> Dict[str, Any]:
        """Generate summary of all predictions.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.prediction_results:
            result = {"message": "No predictions yet", "status": "empty"}
            self.structured_logger.info("Summary report generated (empty)", {
                "status": "no_predictions"
            })
            return result
        
        successful = [k for k, v in self.prediction_results.items() if v.success]
        failed = [k for k, v in self.prediction_results.items() if not v.success]
        
        result = {
            "status": "success",
            "total_predictions": len(self.prediction_results),
            "successful": len(successful),
            "failed": len(failed),
            "successful_models": successful,
            "failed_models": failed,
            "results": {
                k: v.to_dict() for k, v in self.prediction_results.items()
            },
        }
        
        self.structured_logger.info("Summary report generated", {
            "total_predictions": result["total_predictions"],
            "successful": result["successful"],
            "failed": result["failed"]
        })
        
        return result
