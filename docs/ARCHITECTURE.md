# Architecture Guide - GOAT Data Analyst

## System Overview

```
┌─────────────────────────────────────────────────────┐
│           Aggregator (Main Entry Point)             │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐   │
│  │      Operation Router & Validator             │   │
│  │  - Input validation                           │   │
│  │  - Worker selection                           │   │
│  │  - Error handling                             │   │
│  └──────────────────────────────────────────────┘   │
│                      │                                │
│      ┌───────────────┼────────────────────┐         │
│      │               │                    │         │
│      ▼               ▼                    ▼         │
│  ┌────────┐    ┌────────┐            ┌────────┐   │
│  │Statistics   │ Pivot  │            │GroupBy │   │
│  │ Worker      │ Worker │    ...     │ Worker │   │
│  └────────┘    └────────┘            └────────┘   │
│      │               │                    │         │
│      └───────────────┼────────────────────┘         │
│                      │                                │
│  ┌──────────────────▼────────────────────┐         │
│  │   Error Intelligence & Logging         │         │
│  │   - Track successes                    │         │
│  │   - Track errors                       │         │
│  │   - Quality scoring                    │         │
│  └──────────────────┬────────────────────┘         │
│                     │                                │
└─────────────────────┼────────────────────────────────┘
                      │
           ┌──────────▼──────────┐
           │  Result Aggregation │
           │  - Combine results  │
           │  - Final quality    │
           │  - Error summary    │
           └──────────┬──────────┘
                      │
                      ▼
              ┌────────────────┐
              │  Final Result  │
              │  - Success     │
              │  - Data        │
              │  - Quality     │
              │  - Errors      │
              └────────────────┘
```

---

## Component Hierarchy

### 1. Aggregator (Main Class)

**Location:** `agents/aggregator/main.py`

**Responsibilities:**
- Route operations to appropriate workers
- Validate input data and operations
- Orchestrate worker execution
- Aggregate results from multiple workers
- Track overall quality and errors

**Key Methods:**
- `aggregate(data, operations)` - Main entry point
- `_select_worker(operation_type)` - Choose worker
- `_validate_operation(operation)` - Validate spec
- `_aggregate_results(results)` - Combine results

---

### 2. BaseWorker (Abstract Base)

**Location:** `agents/aggregator/workers/base_worker.py`

**Responsibilities:**
- Define worker interface
- Implement safe execution wrapper
- Handle common error patterns
- Track quality scores
- Integrate with Error Intelligence

**Key Methods:**
- `safe_execute(**kwargs)` - Safe execution with error handling
- `execute(**kwargs)` - Override in subclasses
- `_validate_input(**kwargs)` - Input validation
- `_create_result(task_type, quality_score)` - Result creation
- `_add_error(result, error_type, message)` - Error tracking
- `_add_warning(result, message)` - Warning tracking
- `_calculate_quality_score(...)` - Quality calculation

**Error Handling:**
- Try/except wrapper around execute
- Catches and logs all exceptions
- Tracks in Error Intelligence
- Returns error result gracefully

---

### 3. Worker Implementations

**Common Pattern:**
```
Worker
├── execute() - Main logic
├── _validate_input() - Input checks
├── _run_operation() - Core operation
└── _calculate_quality_score() - Quality
```

**9 Workers Implemented:**

| Worker | Purpose | Error Types |
|--------|---------|-------------|
| StatisticsWorker | Statistical aggregations | 9 |
| PivotWorker | Pivot tables | 7 |
| GroupByWorker | GroupBy aggregations | 7 |
| CrossTabWorker | Cross-tabulations | 7 |
| ValueCountWorker | Value counts | 6 |
| LagLeadFunction | Lag/lead operations | 2+ |
| RollingAggregation | Rolling windows | 5+ |
| ExponentialWeighted | EWMA | 4+ |
| WindowFunction | Window functions | 6+ |

---

## Error Handling Architecture

### Phase 1: Input Validation
```python
def _validate_input(self, **kwargs) -> Optional[WorkerError]:
    # Check DataFrame validity
    # Check columns exist
    # Check data types
    # Check parameter ranges
    return error if invalid else None
```

### Phase 2: Safe Execution Wrapper
```python
def safe_execute(self, **kwargs) -> WorkerResult:
    try:
        # Validate input
        error = self._validate_input(**kwargs)
        if error:
            return self._create_error_result(error)
        
        # Execute operation
        result = self.execute(**kwargs)
        
        # Track success
        self.error_intelligence.track_success(...)
        return result
    
    except Exception as e:
        # Track error
        self.error_intelligence.track_error(...)
        raise
```

### Phase 3: Operation-Level Error Handling
```python
try:
    result = perform_operation()
except MemoryError:
    self.advanced_errors.append("memory_error")
    return error_result
except ValueError as ve:
    self.advanced_errors.append("operation_value_error")
    return error_result
except Exception as e:
    self.advanced_errors.append(type(e).__name__.lower())
    return error_result
```

### Phase 4: Result-Level Error Handling
```python
# Check for infinity/NaN in results
if np.isinf(result).any():
    self.advanced_errors.append("infinity_in_result")

if result.isna().any():
    self.advanced_errors.append("nan_in_result")

# Check for empty results
if result.empty:
    self.advanced_errors.append("empty_result")
```

---

## Data Flow

### Operation Flow

```
Input DataFrame
      │
      ▼
┌──────────────────┐
│ Input Validation │
│ - Schema check   │
│ - Column check   │
│ - Type check     │
└──────────┬───────┘
           │
      ┌────▼────┐
      │ Valid?  │
      └────┬────┘
           │
      ┌────┴────┐
      │          │
   No │          │ Yes
      │          │
      ▼          ▼
  Error      Execute
  Result      Worker
      │          │
      │          ▼
      │    ┌──────────────┐
      │    │ Core Logic   │
      │    │ - Statistics │
      │    │ - Aggregation│
      │    │ - Pivot, etc │
      │    └──────┬───────┘
      │           │
      │           ▼
      │    ┌──────────────┐
      │    │Check Results │
      │    │ - Infinity   │
      │    │ - NaN        │
      │    │ - Empty      │
      │    └──────┬───────┘
      │           │
      │           ▼
      │    ┌──────────────┐
      │    │Quality Score │
      │    │Calculation   │
      │    └──────┬───────┘
      │           │
      └───────┬───┘
              │
              ▼
        ┌──────────┐
        │ Result   │
        └──────────┘
```

### Result Object Structure

```python
WorkerResult
├── success: bool
├── quality_score: float (0.0-1.0)
├── task_type: str
├── data: Dict
│   ├── rows_processed: int
│   ├── null_count: int
│   ├── advanced_errors_encountered: int
│   ├── advanced_error_types: List[str]
│   └── ... (operation-specific fields)
├── errors: List[WorkerError]
│   ├── error_type: ErrorType
│   ├── message: str
│   ├── severity: str
│   ├── details: Dict
│   └── suggestion: str
└── warnings: List[str]
```

---

## Quality Scoring

### Scoring Formula

```
Base Quality = rows_processed / (rows_processed + rows_failed)

Penalties:
  null_penalty = min(0.15, null_count * 0.001)
  error_penalty = min(0.2, error_count * 0.05)
  dup_penalty = varies by worker

Final Quality = max(0, min(1, Base - null - error - dup))
```

### Quality Interpretation

```
0.9-1.0:  Excellent
│
├─ No data quality issues
├─ All operations successful
├─ No infinity/NaN values
└─ No advanced errors

0.8-0.9:  Good
│
├─ Minor null values (5-10%)
├─ 1-2 minor errors
├─ Handled gracefully
└─ Acceptable for production

0.7-0.8:  Fair
│
├─ Moderate nulls (10-15%)
├─ Multiple errors
├─ Quality reduced but usable
└─ Review needed

<0.7:    Poor
│
├─ High null/error rate
├─ Data quality severely impacted
└─ Recommend data cleaning
```

---

## Error Intelligence Integration

### Success Tracking

```python
self.error_intelligence.track_success(
    agent_name="aggregator",
    worker_name="StatisticsWorker",
    operation="mean_calculation",
    context={
        "success": True,
        "quality_score": 0.95,
        "advanced_errors": 0,
        "error_types": [],
        # Worker-specific fields
    }
)
```

### Error Tracking

```python
self.error_intelligence.track_error(
    agent_name="aggregator",
    worker_name="StatisticsWorker",
    error_type="MemoryError",
    error_message="Insufficient memory",
    context={
        "rows_processed": 5000,
        "rows_failed": 5000,
        "advanced_errors": 1,
    }
)
```

---

## Type System

### Error Type Enum

```python
class ErrorType(Enum):
    INVALID_PARAMETER = "invalid_parameter"
    MISSING_DATA = "missing_data"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    COMPUTATION_ERROR = "computation_error"
    MEMORY_ERROR = "memory_error"
    UNKNOWN_ERROR = "unknown_error"
```

### Worker Result Structure

```python
@dataclass
class WorkerResult:
    success: bool
    quality_score: float
    task_type: str
    data: Dict[str, Any]
    errors: List['WorkerError']
    warnings: List[str]
```

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Statistics | O(n) | Single pass |
| GroupBy | O(n log n) | Sorting + aggregation |
| Pivot | O(n log n) | Grouping + reshaping |
| CrossTab | O(n log n) | Similar to pivot |
| ValueCount | O(n) | Counting |
| Lag/Lead | O(n) | Single pass |

### Space Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Statistics | O(f) | f = number of functions |
| GroupBy | O(g) | g = number of groups |
| Pivot | O(r×c) | r rows, c columns in result |
| CrossTab | O(r×c) | Result size |
| ValueCount | O(u) | u = unique values |

---

## Extension Points

### Adding New Workers

1. **Inherit from BaseWorker:**
   ```python
   class NewWorker(BaseWorker):
       def __init__(self):
           super().__init__("NewWorker")
           self.advanced_errors = []
   ```

2. **Implement required methods:**
   ```python
   def _validate_input(self, **kwargs) -> Optional[WorkerError]:
       # Validation logic
   
   def execute(self, **kwargs) -> WorkerResult:
       # Core logic with error handling
   ```

3. **Add error tracking:**
   ```python
   context = {
       "success": result.success,
       "advanced_errors": len(self.advanced_errors),
   }
   if self.advanced_errors:
       context["error_types"] = list(set(self.advanced_errors))
   
   self.error_intelligence.track_success(
       agent_name="aggregator",
       worker_name="NewWorker",
       operation="operation",
       context=context
   )
   ```

4. **Register in Aggregator:**
   ```python
   def _select_worker(self, operation_type: str):
       workers = {
           "new_operation": NewWorker,
           # ... other workers
       }
   ```

---

## Version History

**v1.0.0** (2025-12-13)
- All 9 workers complete
- Phase 1-3 quality standards
- Comprehensive error handling
- Error Intelligence integration

---

**Last Updated:** 2025-12-13
