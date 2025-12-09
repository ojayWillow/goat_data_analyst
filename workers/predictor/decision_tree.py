"""DecisionTree Worker - Tree-based regression and classification predictions."""

from workers.base_worker import BaseWorker, WorkerResult, ErrorType
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.metrics import accuracy_score, mean_squared_error
import pandas as pd
import numpy as np


class DecisionTreeWorker(BaseWorker):
    """Worker for decision tree predictions.
    
    Returns predictions, feature importance, tree depth, accuracy/MSE.
    """
    
    def __init__(self):
        super().__init__("DecisionTree")
        self.model = None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute decision tree prediction.
        
        Args:
            df: DataFrame with features and target
            features: List of feature column names
            target: Target column name
            mode: 'regression' or 'classification' (auto-detected if not specified)
            max_depth: Maximum tree depth (optional)
            
        Returns:
            WorkerResult with predictions, feature_importance, tree_depth, etc.
        """
        df = kwargs.get('df')
        features = kwargs.get('features')
        target = kwargs.get('target')
        mode = kwargs.get('mode', 'auto')
        max_depth = kwargs.get('max_depth', None)
        
        result = self._create_result(
            task_type="decision_tree",
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
        
        # Detect mode if auto
        if mode == 'auto':
            unique_vals = df[target].nunique()
            if unique_vals <= 20 and df[target].dtype in ['int64', 'int32', 'object']:
                mode = 'classification'
            else:
                mode = 'regression'
        
        # Train model
        try:
            X = df[features].values
            y = df[target].values
            
            if len(df) < 3:
                self._add_error(result, ErrorType.INSUFFICIENT_DATA, "Need at least 3 samples")
                result.success = False
                return result
            
            if mode == 'classification':
                self.model = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
            else:
                self.model = DecisionTreeRegressor(max_depth=max_depth, random_state=42)
            
            self.model.fit(X, y)
            
            # Generate predictions
            predictions = self.model.predict(X)
            
            # Feature importance
            feature_importance = dict(zip(
                features,
                [float(f) for f in self.model.feature_importances_]
            ))
            
            # Store results
            result.data = {
                "mode": mode,
                "predictions": predictions.tolist(),
                "feature_importance": feature_importance,
                "tree_depth": int(self.model.get_depth()),
                "num_leaves": int(self.model.get_n_leaves()),
            }
            
            # Add mode-specific metrics
            if mode == 'classification':
                result.data['accuracy'] = float(accuracy_score(y, predictions))
            else:
                result.data['mse'] = float(mean_squared_error(y, predictions))
                result.data['rmse'] = float(np.sqrt(mean_squared_error(y, predictions)))
            
            result.success = True
            
        except Exception as e:
            self._add_error(result, ErrorType.PROCESSING_ERROR, f"Tree failed: {str(e)}")
            result.success = False
        
        return result
