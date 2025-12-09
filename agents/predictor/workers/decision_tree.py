"""Decision Tree - Tree-based regression and classification."""

from .base import Base, WorkerResult, ErrorType
from core.logger import get_logger
import pandas as pd
import numpy as np

logger = get_logger(__name__)


class DecisionTree(Base):
    """Worker for decision tree predictions.
    
    Performs decision tree modeling and provides:
    - Feature importance (which features matter most)
    - Predictions for regression
    - Tree depth and node count
    - Performance metrics
    """
    
    def __init__(self):
        super().__init__("DecisionTree")
        self.model = None
        self.feature_names = None
        self.mode = None  # 'regression' or 'classification'
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute decision tree fitting.
        
        Args:
            df: DataFrame with features and target
            features: List of feature column names
            target: Target column name
            mode: 'regression' or 'classification' (auto-detect if not provided)
            max_depth: Maximum tree depth (default: None for unlimited)
            min_samples_split: Minimum samples to split (default: 2)
            
        Returns:
            WorkerResult with feature importance and predictions
        """
        result = self._create_result(
            task_type="decision_tree",
            quality_score=1.0
        )
        
        # Extract inputs
        df = kwargs.get('df')
        features = kwargs.get('features')
        target = kwargs.get('target')
        mode = kwargs.get('mode', 'auto')
        max_depth = kwargs.get('max_depth', None)
        min_samples_split = kwargs.get('min_samples_split', 2)
        
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
        if len(df) < 3:  # Need at least 3 samples for tree
            self._add_error(
                result,
                ErrorType.INSUFFICIENT_DATA,
                f"Need at least 3 rows, got {len(df)}"
            )
            result.success = False
            return result
        
        # TRAINING
        try:
            from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
            
            X = df[features].values
            y = df[target].values
            
            # Auto-detect mode
            if mode == 'auto':
                # If target is numeric with many unique values -> regression
                # If target is categorical or few unique values -> classification
                unique_values = len(np.unique(y))
                is_numeric = pd.api.types.is_numeric_dtype(y)
                self.mode = 'regression' if (is_numeric and unique_values > 10) else 'classification'
            else:
                self.mode = mode
            
            # Create and train model
            if self.mode == 'regression':
                self.model = DecisionTreeRegressor(
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    random_state=42
                )
            else:
                self.model = DecisionTreeClassifier(
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    random_state=42
                )
            
            self.model.fit(X, y)
            self.feature_names = list(features)
            
            # Make predictions
            y_pred = self.model.predict(X)
            
            # Calculate metrics
            if self.mode == 'regression':
                residuals = y - y_pred
                rmse = np.sqrt(np.mean(residuals ** 2))
                mae = np.mean(np.abs(residuals))
                ss_res = np.sum(residuals ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r2_score = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                accuracy = None
            else:
                accuracy = np.mean(y_pred == y)
                r2_score = None
                rmse = None
                mae = None
            
            # Feature importance
            feature_importance = {
                name: float(imp) for name, imp in zip(features, self.model.feature_importances_)
            }
            # Sort by importance
            feature_importance = dict(sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            ))
            
            # Store results
            result.data = {
                "model_type": "Decision Tree",
                "mode": self.mode,
                "tree_depth": int(self.model.get_depth()),
                "num_nodes": int(self.model.tree_.node_count),
                "num_leaves": int(self.model.get_n_leaves()),
                "feature_importance": feature_importance,
                "predictions": y_pred.tolist(),
                "num_samples": len(df),
                "num_features": len(features),
            }
            
            # Add mode-specific metrics
            if self.mode == 'regression':
                result.data["r2_score"] = float(r2_score)
                result.data["rmse"] = float(rmse)
                result.data["mae"] = float(mae)
                result.quality_score = min(r2_score, 1.0) if r2_score else 0
            else:
                result.data["accuracy"] = float(accuracy)
                result.quality_score = float(accuracy)
            
            result.success = True
            
            self.logger.info(
                f"Decision tree trained: depth={result.data['tree_depth']}, "
                f"leaves={result.data['num_leaves']}"
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
                f"Training failed: {str(e)}"
            )
            result.success = False
            self.logger.error(f"Training error: {e}")
        
        return result
