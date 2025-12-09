"""LinearRegression Worker - Simple regression predictions with coefficients."""

from workers.base_worker import BaseWorker, WorkerResult, ErrorType
from sklearn.linear_model import LinearRegression
import pandas as pd
import numpy as np


class LinearRegressionWorker(BaseWorker):
    """Worker for linear regression predictions.
    
    Returns predictions, R² score, coefficients, residuals, and intercept.
    """
    
    def __init__(self):
        super().__init__("LinearRegression")
        self.model = None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute linear regression.
        
        Args:
            df: DataFrame with features and target
            features: List of feature column names
            target: Target column name
            
        Returns:
            WorkerResult with r2_score, coefficients, intercept, predictions, residuals
        """
        df = kwargs.get('df')
        features = kwargs.get('features')
        target = kwargs.get('target')
        
        result = self._create_result(
            task_type="linear_regression",
            quality_score=1.0
        )
        
        # Validate inputs
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        if not features or len(features) == 0:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "No features provided")
            result.success = False
            return result
        
        if target is None:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "No target column specified")
            result.success = False
            return result
        
        # Check columns exist
        missing_cols = [col for col in features + [target] if col not in df.columns]
        if missing_cols:
            self._add_error(result, ErrorType.INVALID_COLUMN, f"Missing columns: {missing_cols}")
            result.success = False
            return result
        
        # Train model
        try:
            X = df[features].values
            y = df[target].values
            
            self.model = LinearRegression()
            self.model.fit(X, y)
            
            # Generate predictions
            predictions = self.model.predict(X)
            residuals = y - predictions
            
            # Store results
            result.data = {
                "r2_score": float(self.model.score(X, y)),
                "coefficients": dict(zip(features, [float(c) for c in self.model.coef_])),
                "intercept": float(self.model.intercept_),
                "predictions": predictions.tolist(),
                "residuals": residuals.tolist(),
                "mean_absolute_error": float(np.mean(np.abs(residuals))),
                "mean_squared_error": float(np.mean(residuals ** 2)),
            }
            result.success = True
            result.quality_score = min(1.0, self.model.score(X, y) + 0.1)  # Clamp at 1.0
            
        except Exception as e:
            self._add_error(result, ErrorType.PROCESSING_ERROR, f"Regression failed: {str(e)}")
            result.success = False
        
        return result
