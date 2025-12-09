# Predictor Agent Architecture - Complete Guide

## Table of Contents
1. [High-Level Overview](#high-level-overview)
2. [File Structure](#file-structure)
3. [Workers Overview](#workers-overview)
4. [How the Agent Works](#how-the-agent-works)
5. [Worker Architecture](#worker-architecture)
6. [Code Examples](#code-examples)
7. [API Reference](#api-reference)

---

## High-Level Overview

### The Big Picture

Think of the **Predictor** like a **Machine Learning Consultant**:

```
ML CONSULTANT (Agent)
│
├─ SPECIALIST 1 (LinearRegressionWorker)    - Simple linear models
├─ SPECIALIST 2 (DecisionTreeWorker)        - Tree-based predictions
├─ SPECIALIST 3 (TimeSeriesWorker)          - Time series forecasting
└─ SPECIALIST 4 (ModelValidatorWorker)      - Model validation

DATA OWNER (Your Code)
│
└─ Asks: "Predict this column"
     ↓
ML CONSULTANT
│
└─ Routes to appropriate specialist(s)
     ↓
Each specialist does the work
     ↓
Returns standardized result
     ↓
ML CONSULTANT aggregates and returns
```

---

## File Structure

```
agents/predictor/                           ← MAIN AGENT FOLDER
│
├── predictor.py                            ← AGENT FILE (coordinator)
│   │
│   └── Contains class: Predictor
│       - Holds the DataFrame
│       - Owns all worker instances
│       - Provides public methods
│       - Routes requests to workers
│
├── __init__.py                             ← EXPORTS THE AGENT
│   │
│   └── Makes: from agents.predictor import Predictor
│
└── workers/                                ← WORKERS FOLDER (specialists)
    │
    ├── base_worker.py                      ← BASE CLASS (template)
    │   ├── Class: BaseWorker (abstract)
    │   ├── Class: WorkerResult (standardized output)
    │   └── Class: ErrorType (error definitions)
    │
    ├── linear_regression_worker.py         ← SPECIALIST 1
    │   └── Class: LinearRegressionWorker
    │       - Fits linear regression models
    │       - Returns: predictions, R², coefficients
    │
    ├── decision_tree_worker.py             ← SPECIALIST 2
    │   └── Class: DecisionTreeWorker
    │       - Fits decision tree models
    │       - Returns: predictions, feature importance, tree depth
    │
    ├── time_series_worker.py               ← SPECIALIST 3
    │   └── Class: TimeSeriesWorker
    │       - ARIMA and exponential smoothing
    │       - Returns: forecasts, confidence intervals, decomposition
    │
    ├── model_validator_worker.py           ← SPECIALIST 4
    │   └── Class: ModelValidatorWorker
    │       - Cross-validation and diagnostics
    │       - Returns: CV scores, residual analysis
    │
    └── __init__.py                         ← EXPORTS ALL WORKERS
        └── Makes: from .workers import X
```

---

## Workers Overview

### Worker 1: LinearRegressionWorker
**Purpose:** Simple linear regression

**What it does:**
- Fits a linear model: y = b₀ + b₁x₁ + b₂x₂ + ...
- Calculates R² (goodness of fit)
- Returns feature coefficients (importance)
- Computes residuals and metrics (RMSE, MAE)

**Returns:**
```python
{
    "r2_score": 0.95,
    "rmse": 0.12,
    "mae": 0.10,
    "coefficients": {"feature1": 2.34, "feature2": -1.23},
    "intercept": 0.45,
    "predictions": [1.2, 2.3, 1.1, ...],
    "residuals": [0.1, -0.05, 0.02, ...],
}
```

### Worker 2: DecisionTreeWorker
**Purpose:** Tree-based predictions

**What it does:**
- Fits a decision tree (regression or classification)
- Auto-detects task type from data
- Extracts feature importance
- Returns tree structure info (depth, leaves)

**Returns:**
```python
{
    "mode": "regression",
    "tree_depth": 5,
    "num_leaves": 12,
    "feature_importance": {"feature1": 0.6, "feature2": 0.4},
    "predictions": [1.2, 2.3, 1.1, ...],
    "r2_score": 0.92,
    "rmse": 0.15,
}
```

### Worker 3: TimeSeriesWorker
**Purpose:** Time series forecasting

**What it does:**
- ARIMA forecasting (Auto Regressive Integrated Moving Average)
- Fallback: Exponential smoothing
- Decomposes into trend, seasonal, residual
- Provides confidence intervals

**Returns:**
```python
{
    "forecast_data": {
        "method": "ARIMA(1,1,1)",
        "forecast": [1.2, 1.3, 1.25, ...],
        "confidence_interval_lower": [1.0, 1.1, 1.0, ...],
        "confidence_interval_upper": [1.4, 1.5, 1.5, ...],
    },
    "decomposition": {
        "trend": [1.0, 1.05, 1.1, ...],
        "seasonal": [0.1, 0.2, 0.15, ...],
        "residual": [0.05, -0.05, 0.0, ...],
    },
}
```

### Worker 4: ModelValidatorWorker
**Purpose:** Model quality assessment

**What it does:**
- Cross-validation (5-fold by default)
- Residual analysis (normality, outliers)
- Compares train vs test performance
- Checks model assumptions

**Returns:**
```python
{
    "cross_validation": {
        "cv_folds": 5,
        "r2_scores": [0.94, 0.93, 0.95, 0.92, 0.94],
        "r2_mean": 0.936,
        "r2_std": 0.012,
        "train_r2": 0.98,
        "test_r2": 0.93,
    },
    "residual_analysis": {
        "mean": -0.001,
        "std": 0.15,
        "skewness": 0.05,
        "kurtosis": 0.2,
    },
}
```

---

## How the Agent Works

### Agent Responsibilities

```python
class Predictor:
    def __init__(self):
        # STEP 1: Initialize workers
        self.linear_regression_worker = LinearRegressionWorker()
        self.decision_tree_worker = DecisionTreeWorker()
        self.time_series_worker = TimeSeriesWorker()
        self.model_validator_worker = ModelValidatorWorker()
    
    def set_data(self, df):
        # STEP 2: Store data
        self.data = df.copy()
    
    def predict_linear(self, features, target):
        # STEP 3: Call worker
        result = self.linear_regression_worker.safe_execute(
            df=self.data,
            features=features,
            target=target,
        )
        # STEP 4: Store and return
        self.prediction_results["linear"] = result
        return result.to_dict()
```

### Agent Responsibilities

| Responsibility | How |
|---|---|
| **Hold data** | `self.data = df` |
| **Own workers** | `self.linear_regression_worker = ...` |
| **Route requests** | `self.worker.safe_execute(...)` |
| **Store results** | `self.prediction_results[key] = result` |
| **Return results** | `return worker_result.to_dict()` |
| **Logging** | `self.logger.info(...)` |

---

## Worker Architecture

### Every Worker Follows This Pattern

```python
class NewWorker(BaseWorker):
    def __init__(self):
        super().__init__("NewWorker")
    
    def execute(self, **kwargs) -> WorkerResult:
        # 1. CREATE RESULT
        result = self._create_result(
            task_type="your_task",
            quality_score=1.0
        )
        
        # 2. EXTRACT INPUTS
        data = kwargs.get('data')
        param = kwargs.get('param')
        
        # 3. VALIDATE
        if data is None:
            self._add_error(result, ErrorType.MISSING_DATA, "msg")
            result.success = False
            return result
        
        # 4. DO WORK
        try:
            # Your logic here
            result.data = {"key": "value"}
            result.success = True
        except Exception as e:
            self._add_error(result, ErrorType.PROCESSING_ERROR, str(e))
            result.success = False
        
        # 5. RETURN
        return result
```

### Standardized Result Format

```python
{
    "worker": "LinearRegressionWorker",
    "task_type": "linear_regression",
    "success": true,
    "data": {                          # Task-specific results
        "r2_score": 0.95,
        "coefficients": {...},
        # ... more data
    },
    "errors": [],                      # Any errors?
    "warnings": [],                    # Any warnings?
    "quality_score": 0.95,             # How good? (0-1)
    "metadata": {},                    # Extra info
    "timestamp": "2025-12-09T11:20:00",# When?
    "execution_time_ms": 125           # How long?
}
```

---

## Code Examples

### Example 1: Simple Linear Prediction

```python
from agents.predictor import Predictor
import pandas as pd

# Create data
df = pd.DataFrame({
    "feature1": [1, 2, 3, 4, 5],
    "feature2": [2, 4, 6, 8, 10],
    "target": [3, 6, 9, 12, 15],
})

# Create agent
predictor = Predictor()
predictor.set_data(df)

# Predict
result = predictor.predict_linear(
    features=["feature1", "feature2"],
    target="target"
)

# Check result
if result['success']:
    print(f"R2 Score: {result['data']['r2_score']}")
    print(f"Coefficients: {result['data']['coefficients']}")
else:
    print(f"Error: {result['errors']}")
```

### Example 2: Decision Tree with Feature Importance

```python
# Tree prediction
result = predictor.predict_tree(
    features=["feature1", "feature2"],
    target="target",
    mode="auto",  # Auto-detect regression/classification
    max_depth=5
)

if result['success']:
    print(f"Tree Depth: {result['data']['tree_depth']}")
    print(f"Feature Importance: {result['data']['feature_importance']}")
    print(f"Accuracy/R2: {result['data'].get('accuracy', result['data'].get('r2_score'))}")
```

### Example 3: Time Series Forecasting

```python
# Create time series data
ts_df = pd.DataFrame({
    "time": range(60),
    "value": [1, 2, 1.5, 3, 2.5, 4, 3.5, 5, ...],  # Trending data
})

predictor.set_data(ts_df)

# Forecast
result = predictor.forecast_timeseries(
    series_column="value",
    periods=12,  # Forecast 12 periods ahead
    method="auto",  # Auto ARIMA or exponential smoothing
    decompose=True  # Include trend/seasonal decomposition
)

if result['success']:
    forecast = result['data']['forecast_data']['forecast']
    lower_ci = result['data']['forecast_data']['confidence_interval_lower']
    upper_ci = result['data']['forecast_data']['confidence_interval_upper']
    
    # Plot: forecast ± confidence interval
    for i, (f, l, u) in enumerate(zip(forecast, lower_ci, upper_ci)):
        print(f"Period {i+1}: {f:.2f} [{l:.2f}, {u:.2f}]")
```

### Example 4: Model Validation

```python
# Validate linear regression model
result = predictor.validate_model(
    features=["feature1", "feature2"],
    target="target",
    model_type="linear",
    cv_folds=5  # 5-fold cross-validation
)

if result['success']:
    cv_data = result['data']['cross_validation']
    print(f"CV R2 Mean: {cv_data['r2_mean']:.4f}")
    print(f"CV R2 Std: {cv_data['r2_std']:.4f}")
    print(f"Train R2: {cv_data['train_r2']:.4f}")
    print(f"Test R2: {cv_data['test_r2']:.4f}")
    
    # Check for overfitting
    if cv_data['train_r2'] - cv_data['test_r2'] > 0.1:
        print("⚠️ Possible overfitting detected!")
```

### Example 5: Full Analysis Pipeline

```python
from agents.predictor import Predictor
import pandas as pd

# Load data
df = pd.read_csv('data.csv')
predictor = Predictor()
predictor.set_data(df)

# Try different models
print("\n=== Model Comparison ===")

# Linear
linear_result = predictor.predict_linear(
    features=['X1', 'X2', 'X3'],
    target='y'
)
linear_r2 = linear_result['data']['r2_score']
print(f"Linear R2: {linear_r2:.4f}")

# Tree
tree_result = predictor.predict_tree(
    features=['X1', 'X2', 'X3'],
    target='y'
)
tree_r2 = tree_result['data']['r2_score']
print(f"Tree R2: {tree_r2:.4f}")

# Validation
val_result = predictor.validate_model(
    features=['X1', 'X2', 'X3'],
    target='y'
)
val_r2 = val_result['data']['overall_metrics']['r2_score']
print(f"Validated R2: {val_r2:.4f}")

# Summary
summary = predictor.summary_report()
print(f"\nSummary: {summary['total_predictions']} models trained")
print(f"Successful: {summary['successful']}")
```

---

## API Reference

### Predictor Agent Methods

#### `set_data(df: pd.DataFrame) -> None`
Store DataFrame for predictions.

#### `get_data() -> pd.DataFrame`
Retrieve stored DataFrame.

#### `predict_linear(features, target) -> Dict`
Linear regression prediction.
- **Args**:
  - `features` (List[str]): Feature column names
  - `target` (str): Target column name
- **Returns**: Dict with r2_score, coefficients, predictions, residuals

#### `predict_tree(features, target, mode='auto', max_depth=None) -> Dict`
Decision tree prediction.
- **Args**:
  - `features` (List[str]): Feature column names
  - `target` (str): Target column name
  - `mode` (str): 'regression', 'classification', or 'auto'
  - `max_depth` (int): Maximum tree depth
- **Returns**: Dict with feature_importance, tree_depth, predictions

#### `forecast_timeseries(series_column, periods=12, method='auto', decompose=True) -> Dict`
Time series forecasting.
- **Args**:
  - `series_column` (str): Column with time series data
  - `periods` (int): Number of periods to forecast
  - `method` (str): 'arima', 'exponential_smoothing', or 'auto'
  - `decompose` (bool): Include decomposition
- **Returns**: Dict with forecast, confidence_intervals, decomposition

#### `validate_model(features, target, model_type='linear', cv_folds=5) -> Dict`
Model validation and cross-validation.
- **Args**:
  - `features` (List[str]): Feature column names
  - `target` (str): Target column name
  - `model_type` (str): 'linear' or 'tree'
  - `cv_folds` (int): Number of cross-validation folds
- **Returns**: Dict with cross_validation scores and residual_analysis

#### `summary_report() -> Dict`
Generate summary of all predictions.
- **Returns**: Dict with total_predictions, successful, failed, results

---

## Summary Table

| Component | Location | Purpose | Status |
|-----------|----------|---------|--------|
| **Predictor** | `predictor.py` | Coordinator, owns workers | ✅ |
| **LinearRegressionWorker** | `workers/linear_regression_worker.py` | Linear regression | ✅ |
| **DecisionTreeWorker** | `workers/decision_tree_worker.py` | Tree-based ML | ✅ |
| **TimeSeriesWorker** | `workers/time_series_worker.py` | Forecasting | ✅ |
| **ModelValidatorWorker** | `workers/model_validator_worker.py` | Validation | ✅ |
| **Test Suite** | `tests/test_predictor.py` | 30+ tests | ✅ |

---

## Quick Start

```python
# 1. Import
from agents.predictor import Predictor
import pandas as pd

# 2. Create instance
predictor = Predictor()

# 3. Load data
df = pd.read_csv('data.csv')
predictor.set_data(df)

# 4. Predict
result = predictor.predict_linear(
    features=['col1', 'col2'],
    target='target'
)

# 5. Check results
if result['success']:
    print(f"R2: {result['data']['r2_score']}")
else:
    print(f"Error: {result['errors']}")
```

---

**Status: Production Ready! 🚀**

4 workers, 30+ tests, full documentation.

Ready to integrate with other agents!
