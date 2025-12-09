"""Linear Regression - Simple linear model predictions."""

from .base import Base, WorkerResult, ErrorType
from core.logger import get_logger
import pandas as pd
import numpy as np

logger = get_logger(__name__)


class LinearRegression(Base):
    """Worker for linear regression predictions.
    
    Performs simple linear regression on data and provides:
    - Model coefficients (feature importance)
    - R² score (model quality)
    - Predictions on training data
    - Residuals for error analysis
    """
    
    def __init__(self):
        super().__init__("LinearRegression")
        self.model = None
        self.feature_names = None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute linear regression fitting.
        
        Args:
            df: DataFrame with features and target
            features: List of feature column names
            target: Target column name
            
        Returns:
            WorkerResult with model metrics and predictions
        """
        result = self._create_result(
            task_type="linear_regression",
            quality_score=1.0
        )
        
        # Extract inputs
        df = kwargs.get('df')
        features = kwargs.get('features')
        target = kwargs.get('target')
        
        # VALIDATION
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        if not isinstance(features, (list, tuple)) or len(features) == 0:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "Features must be non-empty list")
            result.success = False
            return result
        
        if target is None:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "Target column not specified")
            result.success = False
            return result
        
        # Check columns exist
        missing_cols = [col for col in features + [target] if col not in df.columns]
        if missing_cols:
            self._add_error(
                result,
                ErrorType.INVALID_COLUMN,
                f"Missing columns: {missing_cols}"
            )
            result.success = False
            return result
        
        # Check data size
        if len(df) < len(features) + 1:
            self._add_error(
                result,
                ErrorType.INSUFFICIENT_DATA,
                f"Need at least {len(features) + 1} rows, got {len(df)}"
            )
            result.success = False
            return result
        
        # TRAINING
        try:
            from sklearn.linear_model import LinearRegression as SKLinearRegression
            
            X = df[features].values
            y = df[target].values
            
            # Train model
            self.model = SKLinearRegression()
            self.model.fit(X, y)
            self.feature_names = list(features)
            
            # Make predictions
            y_pred = self.model.predict(X)
            
            # Calculate metrics
            residuals = y - y_pred
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2_score = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            rmse = np.sqrt(np.mean(residuals ** 2))
            mae = np.mean(np.abs(residuals))
            
            # Store results
            result.data = {
                "model_type": "Linear Regression",
                "r2_score": float(r2_score),
                "rmse": float(rmse),
                "mae": float(mae),
                "coefficients": {name: float(coef) for name, coef in zip(features, self.model.coef_)},
                "intercept": float(self.model.intercept_),
                "predictions": y_pred.tolist(),
                "residuals": residuals.tolist(),
                "num_samples": len(df),
                "num_features": len(features),
            }
            result.quality_score = min(r2_score, 1.0)
            result.success = True
            
            self.logger.info(f"Linear regression trained: R²={r2_score:.4f}, RMSE={rmse:.4f}")
            
        except ImportError:
            self._add_error(
                result,
                ErrorType.MODEL_ERROR,
                "scikit-learn not available"
            )
            result.success = False
        except Exception as e:
            self._add_error(
                result,
                ErrorType.PROCESSING_ERROR,
                f"Training failed: {str(e)}"
            )
            result.success = False
            self.logger.error(f"Training error: {e}")
        
        return result
