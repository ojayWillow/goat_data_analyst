"""Model Validator Worker - Model validation and comparison."""

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

logger = get_logger(__name__)


class ModelValidatorWorker(BaseWorker):
    """Worker for model validation and comparison.
    
    Performs cross-validation and model quality checks:
    - Cross-validation scores
    - Residual analysis
    - Model assumption checking
    - Model comparison
    """
    
    def __init__(self):
        super().__init__("ModelValidatorWorker")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute model validation.
        
        Args:
            X: Feature matrix
            y: Target values
            model_type: 'linear' or 'tree' (default: 'linear')
            cv_folds: Number of CV folds (default: 5)
            
        Returns:
            WorkerResult with validation metrics
        """
        result = self._create_result(
            task_type="model_validation",
            quality_score=1.0
        )
        
        # Extract inputs
        X = kwargs.get('X')
        y = kwargs.get('y')
        model_type = kwargs.get('model_type', 'linear')
        cv_folds = kwargs.get('cv_folds', 5)
        
        # VALIDATION
        if X is None or y is None:
            self._add_error(result, ErrorType.MISSING_DATA, "X or y not provided")
            result.success = False
            return result
        
        # Convert to numpy arrays
        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, pd.Series):
            y = y.values
        
        if len(X) != len(y):
            self._add_error(result, ErrorType.INVALID_PARAMETER, "X and y length mismatch")
            result.success = False
            return result
        
        if len(X) < cv_folds + 1:
            self._add_error(
                result,
                ErrorType.INSUFFICIENT_DATA,
                f"Need at least {cv_folds + 1} samples, got {len(X)}"
            )
            result.success = False
            return result
        
        # VALIDATION
        try:
            try:
                from sklearn.linear_model import LinearRegression
                from sklearn.tree import DecisionTreeRegressor
                from sklearn.model_selection import cross_val_score, cross_validate
            except ImportError:
                self._add_error(result, ErrorType.MODEL_ERROR, "scikit-learn not available")
                result.success = False
                return result
            
            # Create model
            if model_type == 'linear':
                model = LinearRegression()
            elif model_type == 'tree':
                model = DecisionTreeRegressor(random_state=42)
            else:
                self._add_error(result, ErrorType.INVALID_PARAMETER, f"Unknown model_type: {model_type}")
                result.success = False
                return result
            
            # Cross-validation
            cv_scores = cross_val_score(model, X, y, cv=cv_folds, scoring='r2')
            cv_results = cross_validate(
                model, X, y, cv=cv_folds,
                scoring=['r2', 'neg_mean_absolute_error', 'neg_mean_squared_error'],
                return_train_score=True
            )
            
            # Train on all data for additional analysis
            model.fit(X, y)
            y_pred = model.predict(X)
            residuals = y - y_pred
            
            # Calculate residual statistics
            residual_mean = float(np.mean(residuals))
            residual_std = float(np.std(residuals))
            residual_skew = float(pd.Series(residuals).skew())
            residual_kurtosis = float(pd.Series(residuals).kurtosis())
            
            # Calculate R2 and other metrics
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2_score = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            rmse = np.sqrt(np.mean(residuals ** 2))
            mae = np.mean(np.abs(residuals))
            
            # Store results
            result.data = {
                "model_type": model_type,
                "cross_validation": {
                    "cv_folds": cv_folds,
                    "r2_scores": cv_scores.tolist(),
                    "r2_mean": float(np.mean(cv_scores)),
                    "r2_std": float(np.std(cv_scores)),
                    "train_r2": float(np.mean(cv_results['train_r2'])),
                    "test_r2": float(np.mean(cv_results['test_r2'])),
                    "mae_mean": float(np.mean(-cv_results['test_neg_mean_absolute_error'])),
                    "rmse_mean": float(np.sqrt(np.mean(-cv_results['test_neg_mean_squared_error']))),
                },
                "overall_metrics": {
                    "r2_score": float(r2_score),
                    "rmse": float(rmse),
                    "mae": float(mae),
                    "samples": len(X),
                    "features": X.shape[1],
                },
                "residual_analysis": {
                    "mean": residual_mean,
                    "std": residual_std,
                    "skewness": residual_skew,
                    "kurtosis": residual_kurtosis,
                    "min": float(np.min(residuals)),
                    "max": float(np.max(residuals)),
                    "q1": float(np.percentile(residuals, 25)),
                    "median": float(np.percentile(residuals, 50)),
                    "q3": float(np.percentile(residuals, 75)),
                },
                "predictions": y_pred.tolist(),
                "residuals": residuals.tolist(),
            }
            
            result.quality_score = float(r2_score)
            result.success = True
            
            self.logger.info(
                f"Model validation complete: R2={r2_score:.4f}, CV R2={np.mean(cv_scores):.4f}"
            )
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.PROCESSING_ERROR,
                f"Validation failed: {str(e)}"
            )
            result.success = False
            self.logger.error(f"Validation error: {e}")
        
        return result
