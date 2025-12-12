"""Model Validator Worker - Cross-validation and model evaluation."""

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

logger = get_logger(__name__)


class ModelValidatorWorker(BaseWorker):
    """Worker for model validation and evaluation.
    
    Performs cross-validation and provides:
    - Cross-validation scores
    - Model comparison metrics
    - Generalization estimates
    - Overfitting detection
    """
    
    def __init__(self):
        super().__init__("ModelValidatorWorker")
        self.cv_results = None
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute model validation.
        
        Wraps entire task with try-except for proper error tracking.
        
        Args:
            df: DataFrame with features and target
            features: List of feature column names
            target: Target column name
            model: Pre-trained model to validate
            cv_folds: Number of cross-validation folds (default: 5)
            
        Returns:
            WorkerResult with validation metrics
        """
        try:
            result = self._run_model_validation(**kwargs)
            
            # Track success AFTER entire task completes
            self.error_intelligence.track_success(
                agent_name="predictor",
                worker_name="ModelValidatorWorker",
                operation="model_validation",
                context={
                    k: v for k, v in kwargs.items() 
                    if k not in ('df', 'model') and not isinstance(v, (pd.DataFrame, object))
                }
            )
            
            return result
            
        except Exception as e:
            # Track error ONLY in exception handler
            self.error_intelligence.track_error(
                agent_name="predictor",
                worker_name="ModelValidatorWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    k: v for k, v in kwargs.items() 
                    if k not in ('df', 'model') and not isinstance(v, (pd.DataFrame, object))
                }
            )
            raise
    
    def _run_model_validation(self, **kwargs) -> WorkerResult:
        """Perform actual model validation work.
        
        This method contains all the actual validation logic.
        execute() wraps this with try-except for error tracking.
        """
        result = self._create_result(
            task_type="model_validation",
            quality_score=1.0
        )
        
        # Extract inputs
        df = kwargs.get('df')
        features = kwargs.get('features')
        target = kwargs.get('target')
        model = kwargs.get('model')
        cv_folds = kwargs.get('cv_folds', 5)
        
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
        
        if model is None:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "No model provided for validation")
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
        
        # Check CV folds
        if cv_folds < 2 or cv_folds > len(df):
            self._add_error(
                result,
                ErrorType.INVALID_PARAMETER,
                f"CV folds must be 2-{len(df)}, got {cv_folds}"
            )
            result.success = False
            return result
        
        # CROSS-VALIDATION
        try:
            from sklearn.model_selection import cross_val_score, cross_validate
            
            X = df[features].values
            y = df[target].values
            
            # Determine scoring metric based on model type
            try:
                # Try to detect if it's regression or classification
                model_class_name = model.__class__.__name__.lower()
                is_classifier = 'classifier' in model_class_name
                is_regressor = 'regressor' in model_class_name
                
                if is_classifier:
                    scoring = 'accuracy'
                    primary_metric = 'accuracy'
                elif is_regressor:
                    scoring = 'r2'
                    primary_metric = 'r2'
                else:
                    # Default to r2 for generic models
                    scoring = 'r2'
                    primary_metric = 'r2'
            except:
                scoring = 'r2'
                primary_metric = 'r2'
            
            # Perform cross-validation
            cv_scores = cross_val_score(
                model, X, y,
                cv=cv_folds,
                scoring=scoring
            )
            
            # Get detailed metrics
            scoring_dict = {
                'primary': scoring,
            }
            if is_regressor or primary_metric == 'r2':
                scoring_dict['mae'] = 'neg_mean_absolute_error'
                scoring_dict['mse'] = 'neg_mean_squared_error'
            
            cv_results = cross_validate(
                model, X, y,
                cv=cv_folds,
                scoring=scoring_dict,
                return_train_score=True
            )
            
            # Calculate statistics
            cv_mean = np.mean(cv_scores)
            cv_std = np.std(cv_scores)
            
            # Check for overfitting
            train_scores = cv_results.get('train_primary', [])
            test_scores = cv_results.get('test_primary', cv_scores)
            
            if len(train_scores) > 0:
                train_mean = np.mean(train_scores)
                overfitting_ratio = train_mean - cv_mean if train_mean > cv_mean else 0
            else:
                train_mean = None
                overfitting_ratio = None
            
            # Determine validation status
            is_overfitted = False
            validation_status = "VALID"
            
            if overfitting_ratio is not None and overfitting_ratio > 0.15:
                is_overfitted = True
                validation_status = "OVERFITTED"
            elif cv_mean < 0.5 and primary_metric != 'accuracy':
                validation_status = "POOR_PERFORMANCE"
            elif cv_std > cv_mean * 0.5:
                validation_status = "UNSTABLE"
            
            # Store results
            result.data = {
                "model_type": model.__class__.__name__,
                "validation_status": validation_status,
                "cv_folds": cv_folds,
                "cv_mean": float(cv_mean),
                "cv_std": float(cv_std),
                "cv_scores": cv_scores.tolist(),
                "primary_metric": primary_metric,
                "is_overfitted": bool(is_overfitted),
                "num_samples": len(df),
                "num_features": len(features),
            }
            
            if train_mean is not None:
                result.data["train_mean"] = float(train_mean)
                result.data["overfitting_ratio"] = float(overfitting_ratio)
            
            # Quality score based on CV performance
            if primary_metric == 'accuracy':
                result.quality_score = max(0, min(cv_mean, 1.0))
            else:
                # For regression, higher R2 is better (scaled 0-1)
                result.quality_score = max(0, min((cv_mean + 1) / 2, 1.0))
            
            result.success = True
            
            self.logger.info(
                f"Model validation complete: {primary_metric}={cv_mean:.4f}±{cv_std:.4f}, "
                f"status={validation_status}"
            )
            
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
                f"Validation failed: {str(e)}"
            )
            result.success = False
            self.logger.error(f"Validation error: {e}")
        
        return result
