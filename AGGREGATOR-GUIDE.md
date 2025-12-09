# Aggregator Agent Architecture - Complete Beginner's Guide

## Table of Contents
1. [High-Level Overview](#high-level-overview)
2. [File Structure](#file-structure)
3. [How Workers Are Created](#how-workers-are-created)
4. [How the Agent Works](#how-the-agent-works)
5. [How They Talk to Each Other](#how-they-talk-to-each-other)
6. [Code Examples](#code-examples)
7. [Data Flow Diagram](#data-flow-diagram)

---

## High-Level Overview

### The Big Picture

Think of the **Aggregator** like a **restaurant**:

```
RESTAURANT (Agent)
│
├─ CHEF 1 (GroupByWorker)     - Specializes in grouping dishes
├─ CHEF 2 (PivotWorker)       - Specializes in rearranging plates
├─ CHEF 3 (CrossTabWorker)    - Specializes in cross-combinations
├─ CHEF 4 (RollingWorker)     - Specializes in time-based recipes
├─ CHEF 5 (StatisticsWorker)  - Specializes in stats/analysis
└─ CHEF 6 (ValueCountWorker)  - Specializes in counting ingredients

CUSTOMER (Your Code)
│
└─ Calls: "I need groupby on sales"
     ↓
RESTAURANT (Agent)
│
└─ Routes to: CHEF 1 (GroupByWorker)
     ↓
CHEF 1 does the work
     ↓
Returns result to RESTAURANT
     ↓
RESTAURANT gives result to CUSTOMER
```

---

## File Structure

```
agents/aggregator/                           ← MAIN AGENT FOLDER
│
├── aggregator.py                            ← AGENT FILE (coordinator)
│   │
│   └── Contains class: Aggregator
│       - Holds the DataFrame
│       - Owns all worker instances
│       - Provides public methods (groupby, pivot, etc.)
│       - Routes requests to workers
│
├── __init__.py                              ← EXPORTS THE AGENT
│   │
│   └── Makes: from agents.aggregator import Aggregator
│
└── workers/                                 ← WORKERS FOLDER (specialists)
    │
    ├── base_worker.py                       ← BASE CLASS (template)
    │   │
    │   ├── Class: BaseWorker (abstract)
    │   ├── Class: WorkerResult (standardized output)
    │   └── Class: ErrorType (error definitions)
    │
    ├── groupby.py                           ← SPECIALIST 1
    │   └── Class: GroupByWorker (extends BaseWorker)
    │
    ├── pivot.py                             ← SPECIALIST 2
    │   └── Class: PivotWorker (extends BaseWorker)
    │
    ├── crosstab.py                          ← SPECIALIST 3
    │   └── Class: CrossTabWorker (extends BaseWorker)
    │
    ├── rolling.py                           ← SPECIALIST 4
    │   └── Class: RollingWorker (extends BaseWorker)
    │
    ├── statistics.py                        ← SPECIALIST 5
    │   └── Class: StatisticsWorker (extends BaseWorker)
    │
    ├── value_count.py                       ← SPECIALIST 6
    │   └── Class: ValueCountWorker (extends BaseWorker)
    │
    └── __init__.py                          ← EXPORTS ALL WORKERS
        └── Makes: from .workers import GroupByWorker, etc.
```

---

## How Workers Are Created

### Step 1: Create a Worker File

**File: `agents/aggregator/workers/groupby.py`**

```python
"""GroupBy Worker - Handles grouping and aggregation operations."""

import pandas as pd
from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class GroupByWorker(BaseWorker):
    """Worker that performs groupby operations."""
    
    def __init__(self):
        # Call parent class to initialize
        super().__init__("GroupByWorker")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute the groupby task.
        
        Args:
            df: DataFrame to group
            group_cols: Column(s) to group by
            agg_specs: Aggregation specs (sum, mean, etc.)
        
        Returns:
            WorkerResult with grouped data
        """
        return self.safe_execute(**kwargs)
    
    def execute(self, **kwargs) -> WorkerResult:
        """Actual implementation of groupby."""
        df = kwargs.get('df')
        group_cols = kwargs.get('group_cols')
        agg_specs = kwargs.get('agg_specs')
        
        # Create empty result
        result = self._create_result(
            task_type="groupby_aggregation",
            quality_score=1.0
        )
        
        # Validate data exists
        if df is None or df.empty:
            self._add_error(
                result,
                ErrorType.MISSING_DATA,
                "No data provided",
                severity="error"
            )
            result.success = False
            return result
        
        try:
            # DO THE WORK: group and aggregate
            grouped = df.groupby(group_cols).agg(agg_specs).reset_index()
            
            # STORE RESULT
            result.data = {
                "grouped_data": grouped.to_dict(orient='records'),
                "groups_count": len(grouped),
            }
            
            logger.info(f"Grouped into {len(grouped)} groups")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, str(e))
            result.success = False
            return result
```

### Key Components

1. **Import the base class:**
   ```python
   from .base_worker import BaseWorker, WorkerResult, ErrorType
   ```

2. **Extend BaseWorker:**
   ```python
   class GroupByWorker(BaseWorker):
   ```

3. **Initialize with parent:**
   ```python
   def __init__(self):
       super().__init__("GroupByWorker")
   ```

4. **Implement execute method:**
   ```python
   def execute(self, **kwargs) -> WorkerResult:
       # Get inputs
       df = kwargs.get('df')
       
       # Create result container
       result = self._create_result(...)
       
       # Validate
       if df is None: 
           self._add_error(result, ...)
       
       # Do work
       grouped = df.groupby(...).agg(...)
       
       # Store result
       result.data = {...}
       
       # Return standardized result
       return result
   ```

---

## How the Agent Works

### The Agent File

**File: `agents/aggregator/aggregator.py`**

```python
"""Aggregator Agent - Coordinates aggregation workers."""

from typing import Any, Dict, Optional
import pandas as pd

from core.logger import get_logger
from .workers.groupby import GroupByWorker
from .workers.pivot import PivotWorker
from .workers.crosstab import CrossTabWorker
from .workers.rolling import RollingWorker
from .workers.statistics import StatisticsWorker
from .workers.value_count import ValueCountWorker


class Aggregator:
    """Aggregator Agent - the coordinator."""

    def __init__(self) -> None:
        """Initialize the agent and all its workers."""
        self.name = "Aggregator"
        self.logger = get_logger("Aggregator")
        self.data: Optional[pd.DataFrame] = None

        # === STEP 1: CREATE ALL WORKERS ===
        self.groupby_worker = GroupByWorker()         # Create worker 1
        self.pivot_worker = PivotWorker()             # Create worker 2
        self.crosstab_worker = CrossTabWorker()       # Create worker 3
        self.rolling_worker = RollingWorker()         # Create worker 4
        self.statistics_worker = StatisticsWorker()   # Create worker 5
        self.value_count_worker = ValueCountWorker()  # Create worker 6

        self.logger.info("Aggregator initialized")

    # === SECTION 1: DATA MANAGEMENT ===
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Store the DataFrame for all workers to use."""
        self.data = df.copy()
        self.logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")

    def get_data(self) -> Optional[pd.DataFrame]:
        """Retrieve the stored DataFrame."""
        return self.data

    # === SECTION 2: PUBLIC METHODS (routes to workers) ===
    
    def groupby(self, group_cols, agg_specs) -> Dict[str, Any]:
        """High-level API to call GroupByWorker.
        
        Steps:
        1. Call the worker's safe_execute method
        2. Pass the DataFrame and parameters
        3. Worker does the work
        4. Convert result to dictionary
        5. Return to caller
        """
        # STEP 1: Call worker
        worker_result = self.groupby_worker.safe_execute(
            df=self.data,
            group_cols=group_cols,
            agg_specs=agg_specs,
        )
        
        # STEP 2: Convert to dict and return
        return worker_result.to_dict()

    def pivot(self, index: str, columns: str, values: str, 
              aggfunc: str = "sum") -> Dict[str, Any]:
        """High-level API to call PivotWorker."""
        worker_result = self.pivot_worker.safe_execute(
            df=self.data,
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc,
        )
        return worker_result.to_dict()

    # ... similar methods for crosstab, rolling, statistics, value_counts ...

    def get_summary(self) -> str:
        """Get human-readable info about the agent state."""
        if self.data is None:
            return "Aggregator: no data loaded"
        
        return (
            f"Aggregator Summary:\n"
            f"  Rows: {self.data.shape[0]}\n"
            f"  Columns: {self.data.shape[1]}"
        )
```

### Agent Responsibilities

| Responsibility | How |
|---|---|
| **Hold data** | `self.data = df` |
| **Own workers** | `self.groupby_worker = GroupByWorker()` |
| **Route requests** | `self.groupby_worker.safe_execute(...)` |
| **Return results** | `return worker_result.to_dict()` |
| **Logging** | `self.logger.info(...)` |

---

## How They Talk to Each Other

### Communication Flow

```
STEP 1: YOU (calling code)
│
└─ agg.groupby(group_cols=["City"], agg_specs={"Price": "sum"})

STEP 2: AGENT (aggregator.py)
│
└─ def groupby(self, group_cols, agg_specs):
       worker_result = self.groupby_worker.safe_execute(
           df=self.data,
           group_cols=group_cols,
           agg_specs=agg_specs
       )

STEP 3: WORKER (groupby.py)
│
└─ def safe_execute(self, **kwargs):
       return self.execute(**kwargs)
   
   def execute(self, **kwargs):
       df = kwargs.get('df')
       group_cols = kwargs.get('group_cols')
       agg_specs = kwargs.get('agg_specs')
       
       # DO WORK
       grouped = df.groupby(group_cols).agg(agg_specs)
       
       # CREATE RESULT
       result = self._create_result(...)
       result.data = {"grouped_data": grouped.to_dict(...)}
       
       return result

STEP 4: AGENT (unwrap result)
│
└─ return worker_result.to_dict()

STEP 5: YOU (receive result)
│
└─ {
     "worker": "GroupByWorker",
     "task_type": "groupby_aggregation",
     "success": true,
     "data": {...},
     "errors": [],
     "quality_score": 1.0,
     ...
   }
```

### The Protocol

**Workers always return the same structure:**

```python
# From base_worker.py - WorkerResult class
{
    "worker": "GroupByWorker",              # Which worker did this
    "task_type": "groupby_aggregation",     # What task was it
    "success": True,                        # Did it work?
    "data": {...},                          # The actual result
    "errors": [],                           # Any errors?
    "warnings": [],                         # Any warnings?
    "quality_score": 0.95,                  # How good? (0-1)
    "metadata": {...},                      # Extra info
    "timestamp": "2025-12-09T11:15:44",     # When?
    "execution_time_ms": 125                # How long?
}
```

---

## Code Examples

### Example 1: Simple GroupBy

```python
from agents.aggregator import Aggregator
import pandas as pd

# CREATE DATA
df = pd.DataFrame({
    "City": ["NYC", "NYC", "LA", "LA"],
    "Price": [100, 200, 150, 250],
    "Day": ["Mon", "Tue", "Mon", "Tue"]
})

# CREATE AGENT
agg = Aggregator()

# GIVE DATA TO AGENT
agg.set_data(df)

# ASK AGENT TO GROUP BY CITY AND SUM PRICES
result = agg.groupby(
    group_cols="City",
    agg_specs={"Price": "sum"}
)

# CHECK RESULT
print(f"Success: {result['success']}")
print(f"Data: {result['data']}")
```

**Output:**
```
Success: True
Data: {
    'grouped_data': [
        {'City': 'LA', 'Price': 400},
        {'City': 'NYC', 'Price': 300}
    ],
    'groups_count': 2
}
```

### Example 2: Pivot Table

```python
# ASK AGENT FOR PIVOT TABLE
result = agg.pivot(
    index="City",
    columns="Day",
    values="Price",
    aggfunc="sum"
)

print(result['data']['pivot_data'])
```

**Output:**
```
[
    {'City': 'LA', 'Mon': 150, 'Tue': 250},
    {'City': 'NYC', 'Mon': 100, 'Tue': 200}
]
```

### Example 3: Check Results

```python
# Get the standardized result
result = agg.value_counts(column="City", top_n=5)

# All results have this structure
print(f"Worker used: {result['worker']}")           # ValueCountWorker
print(f"Success: {result['success']}")              # True/False
print(f"Quality score: {result['quality_score']}")  # 0.0 - 1.0
print(f"Time taken: {result['execution_time_ms']}ms")
print(f"Errors: {result['errors']}")                # Empty if success
print(f"Data: {result['data']}")                    # Actual result
```

---

## Data Flow Diagram

### Visual Flow

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR CODE                            │
│  agg = Aggregator()                                     │
│  agg.set_data(df)                                       │
│  result = agg.groupby(...)                              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│              AGENT (aggregator.py)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │ self.data = df                                  │   │
│  │ self.groupby_worker = GroupByWorker()           │   │
│  │ self.pivot_worker = PivotWorker()               │   │
│  │ self.crosstab_worker = CrossTabWorker()         │   │
│  │ self.rolling_worker = RollingWorker()           │   │
│  │ self.statistics_worker = StatisticsWorker()     │   │
│  │ self.value_count_worker = ValueCountWorker()    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  def groupby(self, group_cols, agg_specs):             │
│      → Routes to GroupByWorker                         │
│      → Returns worker_result.to_dict()                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│          WORKER (groupby.py)                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │ class GroupByWorker(BaseWorker):                │   │
│  │                                                 │   │
│  │ def execute(self, **kwargs):                    │   │
│  │     df = kwargs.get('df')                       │   │
│  │     group_cols = kwargs.get('group_cols')       │   │
│  │     agg_specs = kwargs.get('agg_specs')         │   │
│  │                                                 │   │
│  │     # VALIDATE                                  │   │
│  │     if df is None:                              │   │
│  │         result.success = False                  │   │
│  │                                                 │   │
│  │     # DO WORK                                   │   │
│  │     grouped = df.groupby(group_cols).agg()      │   │
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
│            RESULT (standardized format)                 │
│  {                                                      │
│    "worker": "GroupByWorker",                           │
│    "success": True,                                     │
│    "data": {"grouped_data": [...]},                     │
│    "errors": [],                                        │
│    "quality_score": 1.0,                                │
│    "execution_time_ms": 45                              │
│  }                                                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│                    YOUR CODE                            │
│  print(result['data']['grouped_data'])                  │
│  print(result['success'])                               │
│  print(result['execution_time_ms'])                     │
└─────────────────────────────────────────────────────────┘
```

### Why This Design?

| Benefit | Why It Matters |
|---------|---|
| **Separation of Concerns** | Agent handles data, workers do the work |
| **Easy to test** | Each worker can be tested independently |
| **Easy to maintain** | Change one worker without affecting others |
| **Easy to extend** | Add new worker by copying a template |
| **Clear responsibilities** | Each class has ONE job |
| **Consistent interface** | All workers return same structure |
| **Error handling** | Errors don't crash the whole system |
| **Logging** | Every step is logged for debugging |

---

## Summary Table

| Component | Location | Purpose | Inheritance |
|---|---|---|---|
| **Aggregator** | `aggregator.py` | Coordinator, owns all workers, public API | None (main class) |
| **BaseWorker** | `workers/base_worker.py` | Template for all workers | ABC (abstract) |
| **GroupByWorker** | `workers/groupby.py` | Groups and aggregates data | BaseWorker |
| **PivotWorker** | `workers/pivot.py` | Creates pivot tables | BaseWorker |
| **CrossTabWorker** | `workers/crosstab.py` | Cross-tabulation | BaseWorker |
| **RollingWorker** | `workers/rolling.py` | Rolling aggregations | BaseWorker |
| **StatisticsWorker** | `workers/statistics.py` | Summary statistics | BaseWorker |
| **ValueCountWorker** | `workers/value_count.py` | Value counting | BaseWorker |
| **WorkerResult** | `workers/base_worker.py` | Standardized output | Dataclass |

---

## Quick Reference

**To use the Aggregator:**

```python
# 1. Import
from agents.aggregator import Aggregator

# 2. Create instance
agg = Aggregator()

# 3. Load data
agg.set_data(your_dataframe)

# 4. Call any method
result = agg.groupby(group_cols=["col1"], agg_specs={"col2": "sum"})
result = agg.pivot(index="col1", columns="col2", values="col3")
result = agg.value_counts(column="col1")

# 5. Get results (all have same structure)
if result['success']:
    data = result['data']
    print(f"Time: {result['execution_time_ms']}ms")
else:
    print(f"Error: {result['errors']}")
```

---

This is the **Aggregator pattern** - scalable, maintainable, and beginner-friendly!
