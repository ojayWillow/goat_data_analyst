# Anomaly Detector Agent Architecture - Complete Guide

## Table of Contents
1. [High-Level Overview](#high-level-overview)
2. [File Structure](#file-structure)
3. [How Workers Are Created](#how-workers-are-created)
4. [How the Agent Works](#how-the-agent-works)
5. [How They Talk to Each Other](#how-they-talk-to-each-other)
6. [Detection Methods](#detection-methods)
7. [Code Examples](#code-examples)
8. [Data Flow Diagram](#data-flow-diagram)

---

## High-Level Overview

### The Big Picture

Think of the **Anomaly Detector** like a **security team**:

```
SECURITY TEAM (Agent)
│
├─ ANALYST 1 (StatisticalWorker)    - IQR, Z-score, Modified Z-score
├─ ANALYST 2 (IsolationForestWorker) - ML-based detection
└─ ANALYST 3 (MultivariateWorker)    - Multivariate distance analysis

DATA OWNER (Your Code)
│
└─ Calls: "Find anomalies in this dataset"
     ↓
SECURITY TEAM (Agent)
│
└─ Routes to: ANALYST 1, 2, or 3
     ↓
Each analyst does the work
     ↓
Returns result to SECURITY TEAM
     ↓
SECURITY TEAM gives result to DATA OWNER
```

---

## File Structure

```
agents/anomaly_detector/                    ← MAIN AGENT FOLDER
│
├── anomaly_detector.py                      ← AGENT FILE (coordinator)
│   │
│   └── Contains class: AnomalyDetector
│       - Holds the DataFrame
│       - Owns all worker instances
│       - Provides public methods
│       - Routes requests to workers
│
├── __init__.py                              ← EXPORTS THE AGENT
│   │
│   └── Makes: from agents.anomaly_detector import AnomalyDetector
│
└── workers/                                 ← WORKERS FOLDER (specialists)
    │
    ├── base_worker.py                       ← BASE CLASS (template)
    │   │
    │   ├── Class: BaseWorker (abstract)
    │   ├── Class: WorkerResult (standardized output)
    │   └── Class: ErrorType (error definitions)
    │
    ├── statistical.py                       ← SPECIALIST 1
    │   └── Class: StatisticalWorker (extends BaseWorker)
    │       Methods:
    │       - _iqr_detection()
    │       - _zscore_detection()
    │       - _modified_zscore_detection()
    │
    ├── isolation_forest.py                  ← SPECIALIST 2
    │   └── Class: IsolationForestWorker (extends BaseWorker)
    │       Methods:
    │       - ML-based anomaly detection using Isolation Forest
    │
    ├── multivariate.py                      ← SPECIALIST 3
    │   └── Class: MultivariateWorker (extends BaseWorker)
    │       Methods:
    │       - Mahalanobis distance analysis
    │
    └── __init__.py                          ← EXPORTS ALL WORKERS
        └── Makes: from .workers import StatisticalWorker, etc.
```

---

## How Workers Are Created

### Step 1: Extend BaseWorker

```python
from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)

class StatisticalWorker(BaseWorker):
    """Worker that performs statistical anomaly detection."""
    
    def __init__(self):
        super().__init__("StatisticalWorker")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute the detection task.
        
        Args:
            df: DataFrame to analyze
            column: Column to detect anomalies in
            method: 'iqr', 'zscore', or 'modified_zscore'
            multiplier: IQR multiplier (for IQR method)
            threshold: Z-score threshold (for zscore method)
            mod_threshold: Modified Z-score threshold
            
        Returns:
            WorkerResult with detection results
        """
        return self.safe_execute(**kwargs)
    
    def execute(self, **kwargs) -> WorkerResult:  # Actual implementation
        """Actual implementation of statistical detection."""
        df = kwargs.get('df')
        column = kwargs.get('column')
        method = kwargs.get('method', 'iqr')
        
        # Create result container
        result = self._create_result(
            task_type=f"statistical_{method}_detection",
            quality_score=1.0
        )
        
        # Validate inputs
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        if column not in df.columns:
            self._add_error(result, ErrorType.INVALID_COLUMN, f"Column '{column}' not found")
            result.success = False
            return result
        
        # Route to appropriate detection method
        if method == 'iqr':
            return self._iqr_detection(df, column, kwargs.get('multiplier', 1.5))
        elif method == 'zscore':
            return self._zscore_detection(df, column, kwargs.get('threshold', 3.0))
        # ... etc
```

### Key Pattern

1. **Import BaseWorker** - Get the template
2. **Extend BaseWorker** - Inherit the pattern
3. **Initialize with parent** - Call `super().__init__(name)`
4. **Implement execute()** - The detection logic
5. **Use helper methods** - `_create_result()`, `_add_error()`, `_add_warning()`
6. **Return standardized result** - Always return `WorkerResult`

---

## How the Agent Works

### The Agent File

```python
class AnomalyDetector:
    """Anomaly Detector Agent - coordinates detection workers."""
    
    def __init__(self) -> None:
        """Initialize agent and all workers."""
        self.name = "Anomaly Detector"
        self.logger = get_logger("AnomalyDetector")
        self.data: Optional[pd.DataFrame] = None
        self.detection_results: Dict[str, WorkerResult] = {}

        # === STEP 1: CREATE ALL WORKERS ===
        self.statistical_worker = StatisticalWorker()
        self.isolation_forest_worker = IsolationForestWorker()
        self.multivariate_worker = MultivariateWorker()

        logger.info("AnomalyDetector initialized")

    # === SECTION 1: DATA MANAGEMENT ===
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Store DataFrame for all workers to use."""
        self.data = df.copy()
        self.detection_results = {}
        logger.info(f"Data set: {df.shape}")

    def get_data(self) -> Optional[pd.DataFrame]:
        """Retrieve the stored DataFrame."""
        return self.data

    # === SECTION 2: PUBLIC METHODS (routes to workers) ===
    
    def detect_iqr(self, column: str, multiplier: float = 1.5) -> Dict[str, Any]:
        """High-level API to detect outliers using IQR.
        
        Steps:
        1. Call the worker's safe_execute method
        2. Pass the DataFrame and parameters
        3. Worker does the work
        4. Convert result to dictionary
        5. Return to caller
        """
        # STEP 1: Call worker
        worker_result = self.statistical_worker.safe_execute(
            df=self.data,
            column=column,
            method="iqr",
            multiplier=multiplier,
        )
        
        # STEP 2: Store result
        self.detection_results[f"iqr_{column}"] = worker_result
        
        # STEP 3: Convert to dict and return
        return worker_result.to_dict()
```

### Agent Responsibilities

| Responsibility | How |
|---|---|
| **Hold data** | `self.data = df` |
| **Own workers** | `self.statistical_worker = StatisticalWorker()` |
| **Route requests** | `self.statistical_worker.safe_execute(...)` |
| **Store results** | `self.detection_results[key] = result` |
| **Return results** | `return worker_result.to_dict()` |
| **Logging** | `self.logger.info(...)` |

---

## How They Talk to Each Other

### Communication Flow

```
STEP 1: YOU (calling code)
│
└─ detector.detect_iqr(column="Price", multiplier=1.5)

STEP 2: AGENT (anomaly_detector.py)
│
└─ def detect_iqr(self, column, multiplier):
       worker_result = self.statistical_worker.safe_execute(
           df=self.data,
           column=column,
           method="iqr",
           multiplier=multiplier,
       )
       self.detection_results[f"iqr_{column}"] = worker_result
       return worker_result.to_dict()

STEP 3: WORKER (statistical.py)
│
└─ def safe_execute(self, **kwargs):
       return self.execute(**kwargs)
   
   def execute(self, **kwargs):
       df = kwargs.get('df')
       column = kwargs.get('column')
       method = kwargs.get('method')
       multiplier = kwargs.get('multiplier')
       
       # VALIDATE
       if df is None:
           result.success = False
       
       # DO WORK
       Q1 = df[column].quantile(0.25)
       Q3 = df[column].quantile(0.75)
       IQR = Q3 - Q1
       lower = Q1 - multiplier * IQR
       upper = Q3 + multiplier * IQR
       outliers = df[(df[column] < lower) | (df[column] > upper)]
       
       # STORE RESULT
       result.data = {
           "method": "IQR",
           "outliers_count": len(outliers),
           "bounds": {"lower": lower, "upper": upper},
           # ... more data
       }
       result.success = True
       
       # RETURN STANDARDIZED RESULT
       return result (WorkerResult)

STEP 4: AGENT (unwrap result)
│
└─ return worker_result.to_dict()

STEP 5: YOU (receive result)
│
└─ {
     "worker": "StatisticalWorker",
     "task_type": "statistical_iqr_detection",
     "success": true,
     "data": {
       "method": "IQR",
       "outliers_count": 25,
       "outliers_percentage": 2.1,
       "bounds": {"lower": -150, "upper": 5000},
       # ... more data
     },
     "errors": [],
     "execution_time_ms": 45,
     # ... more metadata
   }
```

### The Protocol

**Workers always return the same structure:**

```python
# From base_worker.py - WorkerResult class
{
    "worker": "StatisticalWorker",
    "task_type": "statistical_iqr_detection",
    "success": True,
    "data": {                          # Actual detection results
        "method": "IQR",
        "column": "Price",
        "outliers_count": 25,
        "outliers_percentage": 2.1,
        "bounds": {"lower": -150, "upper": 5000},
        # ... method-specific data
    },
    "errors": [],                      # Any errors?
    "warnings": [],                    # Any warnings?
    "quality_score": 0.95,             # How good? (0-1)
    "metadata": {},                    # Extra info
    "timestamp": "2025-12-09T11:15:44",# When?
    "execution_time_ms": 45            # How long?
}
```

---

## Detection Methods

### 1. Statistical Detection (StatisticalWorker)

#### IQR (Interquartile Range)
- **What**: Finds outliers beyond 1.5× the IQR from Q1 and Q3
- **Use case**: General-purpose outlier detection
- **Parameters**:
  - `column`: Column to analyze
  - `multiplier`: IQR multiplier (default 1.5)
- **Output**: Outlier count, bounds, values

#### Z-Score
- **What**: Finds values >3 standard deviations from mean
- **Use case**: Normally distributed data
- **Parameters**:
  - `column`: Column to analyze
  - `threshold`: Z-score threshold (default 3.0)
- **Output**: Outlier count, Z-score range

#### Modified Z-Score
- **What**: Robust version using median and MAD
- **Use case**: Skewed or non-normal data
- **Parameters**:
  - `column`: Column to analyze
  - `threshold`: Modified Z-score threshold (default 3.5)
- **Output**: Outlier count, robust statistics

### 2. ML Detection (IsolationForestWorker)

#### Isolation Forest
- **What**: Isolates anomalies using random trees
- **Use case**: Multivariate anomalies, complex patterns
- **Parameters**:
  - `feature_cols`: Columns to use
  - `contamination`: Expected outlier fraction (default 0.1)
  - `n_estimators`: Number of trees (default 100)
- **Output**: Anomaly scores, top anomalies, count

### 3. Multivariate Detection (MultivariateWorker)

#### Mahalanobis Distance
- **What**: Accounts for correlations between variables
- **Use case**: Multivariate outlier detection
- **Parameters**:
  - `feature_cols`: Columns to analyze
  - `percentile`: Threshold percentile (default 95)
- **Output**: Distance statistics, outlier indices, count

---

## Code Examples

### Example 1: Simple IQR Detection

```python
from agents.anomaly_detector import AnomalyDetector
import pandas as pd

# CREATE DATA
df = pd.DataFrame({
    "Price": [100, 200, 150, 250, 5000, 120],  # 5000 is outlier
    "Quantity": [1, 2, 3, 1, 2, 1]
})

# CREATE AGENT
detector = AnomalyDetector()

# GIVE DATA TO AGENT
detector.set_data(df)

# ASK AGENT TO DETECT OUTLIERS
result = detector.detect_iqr(
    column="Price",
    multiplier=1.5
)

# CHECK RESULT
if result['success']:
    print(f"Outliers found: {result['data']['outliers_count']}")
    print(f"Outlier values: {result['data']['outlier_values']}")
    print(f"Bounds: {result['data']['bounds']}")
else:
    print(f"Error: {result['errors']}")
```

**Output:**
```
Outliers found: 1
Outlier values: [5000]
Bounds: {'lower': -387.5, 'upper': 437.5}
```

### Example 2: ML-Based Detection

```python
# Isolation Forest on multiple features
result = detector.detect_isolation_forest(
    feature_cols=["Price", "Quantity"],
    contamination=0.1  # Expect ~10% anomalies
)

print(f"Anomalies: {result['data']['anomalies_count']}")
print(f"Anomaly score range: {result['data']['anomaly_score_range']}")
print(f"Top anomalies: {result['data']['top_anomalies'][:3]}")
```

### Example 3: Multivariate Analysis

```python
# Mahalanobis distance
result = detector.detect_multivariate(
    feature_cols=["Price", "Quantity"],
    percentile=95  # Top 5% as outliers
)

print(f"Multivariate outliers: {result['data']['outliers_count']}")
print(f"Distance stats: {result['data']['distance_statistics']}")
```

### Example 4: Batch Detection

```python
# Run all statistical methods on a column
results = detector.detect_all_statistical(
    column="Price",
    iqr_multiplier=1.5,
    zscore_threshold=3.0,
    mod_zscore_threshold=3.5
)

for method, result in results.items():
    print(f"{method}: {result['data']['outliers_count']} outliers")
```

### Example 5: Complete Analysis

```python
# Run ALL detection methods
results = detector.detect_all(
    statistical_cols=["Price", "Quantity"],
    ml_feature_cols=["Price", "Quantity"],
    multivariate_cols=["Price", "Quantity"],
    contamination=0.1
)

# Get summary
summary = detector.summary_report()
print(f"Total detections: {summary['total_detections']}")
print(f"Successful: {summary['successful']}")
print(f"Methods: {summary['successful_methods']}")
```

---

## Data Flow Diagram

### Visual Flow

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR CODE                            │
│  detector = AnomalyDetector()                           │
│  detector.set_data(df)                                  │
│  result = detector.detect_iqr(...)                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│          AGENT (anomaly_detector.py)                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ self.data = df                                  │   │
│  │ self.statistical_worker = StatisticalWorker()   │   │
│  │ self.isolation_forest_worker = ...              │   │
│  │ self.multivariate_worker = ...                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  def detect_iqr(self, column, multiplier):             │
│      → Routes to StatisticalWorker                     │
│      → Returns worker_result.to_dict()                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│       WORKER (statistical.py)                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │ class StatisticalWorker(BaseWorker):            │   │
│  │                                                 │   │
│  │ def execute(self, **kwargs):                    │   │
│  │     df = kwargs.get('df')                       │   │
│  │     column = kwargs.get('column')               │   │
│  │     method = kwargs.get('method')               │   │
│  │                                                 │   │
│  │     # VALIDATE                                  │   │
│  │     if df is None:                              │   │
│  │         result.success = False                  │   │
│  │                                                 │   │
│  │     # DO WORK                                   │   │
│  │     Q1 = df[column].quantile(0.25)              │   │
│  │     Q3 = df[column].quantile(0.75)              │   │
│  │     IQR = Q3 - Q1                               │   │
│  │     outliers = ...                              │   │
│  │                                                 │   │
│  │     # STORE RESULT                              │   │
│  │     result.data = {...}                         │   │
│  │     result.success = True                       │   │
│  │                                                 │   │
│  │     # RETURN STANDARDIZED RESULT                │   │
│  │     return result (WorkerResult)                │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│         RESULT (standardized format)                    │
│  {                                                      │
│    "worker": "StatisticalWorker",                       │
│    "task_type": "statistical_iqr_detection",            │
│    "success": True,                                     │
│    "data": {"outliers_count": 25, ...},                │
│    "errors": [],                                        │
│    "execution_time_ms": 45                              │
│  }                                                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│                    YOUR CODE                            │
│  print(result['data']['outliers_count'])                │
│  print(result['success'])                               │
│  print(result['execution_time_ms'])                     │
└─────────────────────────────────────────────────────────┘
```

### Why This Design?

| Benefit | Why It Matters |
|---------|---|
| **Separation of Concerns** | Agent handles coordination, workers do detection |
| **Easy to test** | Each worker tested independently |
| **Easy to maintain** | Change one detection method without affecting others |
| **Easy to extend** | Add new detection method by creating new worker |
| **Clear responsibilities** | Each class has ONE job |
| **Consistent interface** | All workers return same structure |
| **Error handling** | Errors don't crash the whole system |
| **Logging** | Every step is logged |

---

## Summary Table

| Component | Location | Purpose | Inheritance |
|---|---|---|---|
| **AnomalyDetector** | `anomaly_detector.py` | Coordinator, owns workers, public API | None (main class) |
| **BaseWorker** | `workers/base_worker.py` | Template for all workers | ABC (abstract) |
| **StatisticalWorker** | `workers/statistical.py` | IQR/Z-score/Modified Z-score detection | BaseWorker |
| **IsolationForestWorker** | `workers/isolation_forest.py` | ML-based anomaly detection | BaseWorker |
| **MultivariateWorker** | `workers/multivariate.py` | Mahalanobis distance detection | BaseWorker |
| **WorkerResult** | `workers/base_worker.py` | Standardized output format | Dataclass |
| **ErrorType** | `workers/base_worker.py` | Error definitions | Enum |

---

## Quick Reference

**To use the AnomalyDetector:**

```python
# 1. Import
from agents.anomaly_detector import AnomalyDetector

# 2. Create instance
detector = AnomalyDetector()

# 3. Load data
detector.set_data(your_dataframe)

# 4. Call any method
result = detector.detect_iqr(column="col1", multiplier=1.5)
result = detector.detect_zscore(column="col1")
result = detector.detect_isolation_forest(feature_cols=["col1", "col2"])
result = detector.detect_multivariate(feature_cols=["col1", "col2"])

# 5. Get results (all have same structure)
if result['success']:
    data = result['data']
    print(f"Anomalies: {data['outliers_count']}")
    print(f"Time: {result['execution_time_ms']}ms")
else:
    print(f"Error: {result['errors']}")
```

---

This is the **Anomaly Detector pattern** - scalable, testable, and production-ready!
