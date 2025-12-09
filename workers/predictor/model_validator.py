"""ModelValidator Worker - Model validation, cross-validation, and comparison."""

from workers.base_worker import BaseWorker, WorkerResult, ErrorType
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import cross_val_score
from scipy import stats
import numpy as np


class ModelValidatorWorker(BaseWorker):
    """Worker for model validation and comparison.
    
    Returns cross-validation scores, residual analysis, model comparison.
    """
    
    def __init__(self):
        super().__init__("ModelValidator")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute model validation.
        
        Args:
            X: Feature matrix (2D array or list)
            y: Target values (1D array or list)
            model_type: 'linear', 'tree', or None for auto-detect
            cv_folds: Number of cross-validation folds (default 5)
            
        Returns:
            WorkerResult with cross-validation scores, residuals analysis, model comparison
        """
        X = kwargs.get('X')
        y = kwargs.get('y')
        model_type = kwargs.get('model_type', None)
        cv_folds = kwargs.get('cv_folds', 5)
        
        result = self._create_result(
            task_type="model_validation",
            quality_score=1.0
        )
        
        # Validate inputs
        if X is None or y is None:
            self._add_error(result, ErrorType.MISSING_DATA, "X or y is None")
            result.success = False
            return result
        
        try:
            X = np.array(X, dtype=float)
            y = np.array(y, dtype=float)
            
            if X.ndim != 2:
                self._add_error(result, ErrorType.INVALID_PARAMETER, "X must be 2D array")
                result.success = False
                return result
            
            if len(X) != len(y):
                self._add_error(result, ErrorType.INVALID_PARAMETER, "X and y have different lengths")
                result.success = False
                return result
            
            if len(X) < cv_folds:
                self._add_error(
                    result,
                    ErrorType.INSUFFICIENT_DATA,
                    f"Need at least {cv_folds} samples for {cv_folds}-fold CV"
                )
                result.success = False
                return result
            
            # Auto-detect model type if needed
            if model_type is None:
                model_type = 'linear'
            
            result.data['model_type'] = model_type
            
            # Get or create model
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
            
            result.data['cross_validation'] = {
                'r2_scores': cv_scores.tolist(),
                'mean_r2': float(cv_scores.mean()),
                'std_r2': float(cv_scores.std()),
                'folds': cv_folds,
            }
            
            # Fit model for residual analysis
            model.fit(X, y)
            y_pred = model.predict(X)
            residuals = y - y_pred
            
            # Residual analysis
            result.data['residual_analysis'] = {
                'mean': float(np.mean(residuals)),
                'std': float(np.std(residuals)),
                'min': float(np.min(residuals)),
                'max': float(np.max(residuals)),
                'skewness': float(stats.skew(residuals)),
                'kurtosis': float(stats.kurtosis(residuals)),
            }
            
            # Check normality
            _, p_value = stats.normaltest(residuals)
            result.data['residual_analysis']['normality_p_value'] = float(p_value)
            result.data['residual_analysis']['residuals_normal'] = p_value > 0.05
            
            # Overall metrics
            result.data['overall_metrics'] = {
                'mean_absolute_error': float(np.mean(np.abs(residuals))),
                'mean_squared_error': float(np.mean(residuals ** 2)),
                'root_mean_squared_error': float(np.sqrt(np.mean(residuals ** 2))),
                'r2_score': float(model.score(X, y)),
            }
            
            result.success = True
            
        except Exception as e:
            self._add_error(result, ErrorType.PROCESSING_ERROR, f"Validation failed: {str(e)}")
            result.success = False
        
        return result
