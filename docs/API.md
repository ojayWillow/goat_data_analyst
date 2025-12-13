# API Reference - GOAT Data Analyst

## Aggregator Main Class

### `Aggregator()`

Main entry point for aggregation operations.

```python
from agents.aggregator.main import Aggregator

agg = Aggregator()
```

#### Methods

### `aggregate(data, operations) -> AggregationResult`

Execute aggregation operations on DataFrame.

**Parameters:**
- `data` (pd.DataFrame): Input data to aggregate
- `operations` (List[Dict]): List of operation specifications

**Returns:**
- `AggregationResult`: Result with success flag, quality score, and data

**Example:**
```python
result = agg.aggregate(
    data=df,
    operations=[
        {
            "type": "statistics",
            "column": "sales",
            "functions": ["mean", "std", "sum"]
        }
    ]
)
```

---

## Worker Classes

### StatisticsWorker

Computes statistical aggregations.

```python
from agents.aggregator.workers.statistics import StatisticsWorker

worker = StatisticsWorker()
result = worker.safe_execute(
    df=df,
    column="values",
    functions=["mean", "std", "min", "max"]
)
```

#### Parameters
- `df` (pd.DataFrame): Input data
- `column` (str): Column to analyze
- `functions` (List[str]): Statistical functions to compute
  - Valid: "mean", "median", "std", "sum", "min", "max", "var", "count"

#### Returns
- `WorkerResult`: Contains computed statistics

#### Errors Tracked
- infinity_values, unexpected_nan, std_nan
- infinity_to_zero, nan_to_zero
- conversion_error, value_error, memory_error, overflow_error

---

### PivotWorker

Creates pivot tables.

```python
from agents.aggregator.workers.pivot import PivotWorker

worker = PivotWorker()
result = worker.safe_execute(
    df=df,
    index="date",
    columns="category",
    values="amount",
    aggfunc="sum"
)
```

#### Parameters
- `df` (pd.DataFrame): Input data
- `index` (str): Column for pivot index
- `columns` (str): Column for pivot columns
- `values` (str, optional): Column to aggregate
- `aggfunc` (str): Aggregation function (sum, mean, min, max, count)

#### Returns
- `WorkerResult`: Pivot table result

#### Errors Tracked
- pivot_value_error, memory_error, series_conversion_error
- reset_index_error, empty_pivot, infinity_in_result, nan_in_result

---

### GroupByWorker

Performs groupby aggregations.

```python
from agents.aggregator.workers.groupby import GroupByWorker

worker = GroupByWorker()
result = worker.safe_execute(
    df=df,
    by=["category", "region"],
    agg={"sales": "sum", "quantity": "mean"}
)
```

#### Parameters
- `df` (pd.DataFrame): Input data
- `by` (str or List[str]): Column(s) to group by
- `agg` (Dict[str, str] or str): Aggregation specification
  - Dict format: {"column": "function"}
  - String format: applies function to all numeric columns

#### Returns
- `WorkerResult`: Grouped aggregation result

#### Errors Tracked
- groupby_error, invalid_agg_specs, aggregation_value_error
- memory_error, empty_result, infinity_in_result, nan_in_result

---

### CrossTabWorker

Creates cross-tabulations.

```python
from agents.aggregator.workers.crosstab import CrossTabWorker

worker = CrossTabWorker()
result = worker.safe_execute(
    df=df,
    rows="product",
    columns="region",
    values="sales",
    aggfunc="sum"
)
```

#### Parameters
- `df` (pd.DataFrame): Input data
- `rows` (str): Column for rows
- `columns` (str): Column for columns
- `values` (str, optional): Column to aggregate
- `aggfunc` (str): Aggregation function

#### Returns
- `WorkerResult`: Cross-tabulation result

#### Errors Tracked
- crosstab_value_error, memory_error, series_conversion
- conversion_error, empty_result, infinity_in_result, nan_in_result

---

### ValueCountWorker

Counts unique values.

```python
from agents.aggregator.workers.value_count import ValueCountWorker

worker = ValueCountWorker()
result = worker.safe_execute(
    df=df,
    column="category",
    top_n=10
)
```

#### Parameters
- `df` (pd.DataFrame): Input data
- `column` (str): Column to count values
- `top_n` (int, default=10): Number of top values to return

#### Returns
- `WorkerResult`: Value counts with percentages

#### Errors Tracked
- value_count_type_error, value_conversion_error
- result_building_error, nunique_error, empty_result, memory_error

---

### LagLeadFunction

Lag and lead operations.

```python
from agents.aggregator.workers.lag_lead_function import LagLeadFunction

worker = LagLeadFunction()
result = worker.safe_execute(
    df=df,
    lag_periods=1,
    lead_periods=1,
    columns=["price", "volume"]
)
```

#### Parameters
- `df` (pd.DataFrame): Input data (must be sorted by time)
- `lag_periods` (int, default=1): Number of periods to lag (0-100)
- `lead_periods` (int, default=0): Number of periods to lead (0-100)
- `columns` (List[str], optional): Numeric columns to apply to

#### Returns
- `WorkerResult`: DataFrame with lag/lead columns added

#### Errors Tracked
- shift_error, memory_error

---

## Result Objects

### WorkerResult

Base result object returned by all workers.

```python
class WorkerResult:
    success: bool           # Operation succeeded
    quality_score: float    # 0.0-1.0 quality metric
    task_type: str          # Operation type
    data: Dict[str, Any]    # Result data and metadata
    errors: List[WorkerError]  # Errors encountered
    warnings: List[str]     # Warnings
```

**Attributes:**
- `success` (bool): True if operation completed successfully
- `quality_score` (float): Quality score 0.0-1.0
- `data` (Dict): Operation-specific result data
- `errors` (List): Error objects
- `warnings` (List): Warning messages

**Example:**
```python
if result.success:
    print(f"Quality: {result.quality_score:.2%}")
    print(f"Data: {result.data}")
else:
    for error in result.errors:
        print(f"Error: {error.message}")
```

### WorkerError

Error details.

```python
class WorkerError:
    error_type: ErrorType   # Error category
    message: str           # Error message
    severity: str          # "error", "critical"
    details: Dict          # Additional details
    suggestion: str        # How to fix
```

---

## Enums

### ErrorType

```python
from agents.aggregator.workers.base_worker import ErrorType

class ErrorType(Enum):
    INVALID_PARAMETER = "invalid_parameter"
    MISSING_DATA = "missing_data"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    COMPUTATION_ERROR = "computation_error"
    MEMORY_ERROR = "memory_error"
    UNKNOWN_ERROR = "unknown_error"
```

---

## Utility Classes

### ValidationUtils

Input validation utilities.

```python
from agents.aggregator.workers.validation_utils import ValidationUtils

# Validate DataFrame
error = ValidationUtils.validate_dataframe(df)

# Validate columns exist
error = ValidationUtils.validate_columns_exist(
    df, ["col1", "col2"], "context_name"
)

# Validate numeric columns
error = ValidationUtils.validate_numeric_columns(df, ["col1"])
```

---

## Error Intelligence

### ErrorIntelligence

Track errors and success metrics.

```python
from agents.error_intelligence.main import ErrorIntelligence

error_intel = ErrorIntelligence()

# Track success
error_intel.track_success(
    agent_name="aggregator",
    worker_name="StatisticsWorker",
    operation="mean_calculation",
    context={"success": True, "quality_score": 0.95}
)

# Track error
error_intel.track_error(
    agent_name="aggregator",
    worker_name="StatisticsWorker",
    error_type="MemoryError",
    error_message="Insufficient memory",
    context={"rows": 10000}
)
```

---

## Common Patterns

### Safe Execution Pattern

All workers support safe execution:

```python
worker = StatisticsWorker()
result = worker.safe_execute(
    df=df,
    column="values",
    functions=["mean", "std"]
)

if result.success:
    stats = result.data["statistics"]
else:
    for error in result.errors:
        print(error.message)
        print(error.suggestion)
```

### Chained Operations

```python
agg = Aggregator()
result = agg.aggregate(
    data=df,
    operations=[
        {"type": "group_by", "by": "category", "agg": "sum"},
        {"type": "pivot", "index": "month", "columns": "category"},
    ]
)
```

---

## Quality Score Interpretation

```
0.9-1.0:  Excellent - No data quality issues
0.8-0.9:  Good - Minor issues handled gracefully
0.7-0.8:  Fair - Moderate data quality issues
0.6-0.7:  Poor - Significant issues
<0.6:     Critical - Data quality severely impacted
```

---

## Version

**API Version:** 1.0.0  
**Last Updated:** 2025-12-13
