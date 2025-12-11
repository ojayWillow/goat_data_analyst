# Error Intelligence Implementation Guide

## Overview

This guide explains how to integrate the **Error Intelligence system** into any agent and its workers. The system tracks successes, failures, health metrics, and provides intelligent recommendations across the entire GOAT Data Analyst platform.

The **Aggregator** agent has been successfully integrated as a reference implementation. This guide allows you to replicate the pattern in other agents.

---

## Architecture Overview

### Core Components

1. **ErrorIntelligence** (Main Orchestrator)
   - Location: `agents/error_intelligence/main.py`
   - Coordinates all tracking and analysis
   - Singleton instance shared across system

2. **ErrorTracker** (Data Collection - SINGLETON)
   - Location: `agents/error_intelligence/workers/error_tracker.py`
   - Captures successes and failures
   - **SINGLETON PATTERN**: All instances share same data
   - Prevents duplicate tracking

3. **Supporting Workers**
   - **PatternAnalyzer**: Identifies error patterns
   - **WorkerHealth**: Calculates health scores (HEALTHY/DEGRADED/BROKEN)
   - **FixRecommender**: Suggests fixes based on patterns
   - **LearningEngine**: Records successful fixes for future use

### Data Flow

```
Agent Worker
    ↓
track_success() / track_error()
    ↓
ErrorIntelligence.track_*()
    ↓
ErrorTracker (Singleton)
    ↓
Patterns → Health → Recommendations → Learned Fixes
```

---

## Step-by-Step Implementation

### Step 1: Import ErrorIntelligence in Your Worker

In your worker's `__init__()` method, add:

```python
from agents.error_intelligence.main import ErrorIntelligence

class YourWorker(BaseWorker):
    def __init__(self):
        super().__init__("YourWorkerName")
        self.error_intelligence = ErrorIntelligence()  # Single instance per worker
```

**Key Point**: Each worker gets ONE ErrorIntelligence instance. The ErrorTracker inside is a singleton, so all instances share the same tracking data.

---

### Step 2: Track Success in Your Worker's Execute Method

Wrap your worker's execution in try-except and call `track_success()`:

```python
def execute(self, **kwargs) -> WorkerResult:
    """Execute the worker's task."""
    try:
        result = self._run_task(**kwargs)
        
        # Track success AFTER successful execution
        self.error_intelligence.track_success(
            agent_name="your_agent_name",  # e.g., "aggregator", "processor"
            worker_name="YourWorkerName",   # e.g., "StatisticsWorker"
            operation="task_description",   # e.g., "summary_statistics"
            context={"key": value}          # Optional: Include relevant context
        )
        
        return result
        
    except Exception as e:
        # Track error if exception occurs
        self.error_intelligence.track_error(
            agent_name="your_agent_name",
            worker_name="YourWorkerName",
            error_type=type(e).__name__,
            error_message=str(e),
            context={"key": value}
        )
        raise
```

**Example from Aggregator (StatisticsWorker)**:

```python
def execute(self, **kwargs) -> WorkerResult:
    try:
        result = self._run_statistics(**kwargs)
        
        self.error_intelligence.track_success(
            agent_name="aggregator",
            worker_name="StatisticsWorker",
            operation="summary_statistics",
            context={"group_column": kwargs.get('group_column')}
        )
        
        return result
        
    except Exception as e:
        self.error_intelligence.track_error(
            agent_name="aggregator",
            worker_name="StatisticsWorker",
            error_type=type(e).__name__,
            error_message=str(e),
            context={"group_column": kwargs.get('group_column')}
        )
        raise
```

---

### Step 3: Verify ErrorType Enum

Make sure you're using valid ErrorType values from `agents/aggregator/workers/base_worker.py`:

```python
class ErrorType(Enum):
    """Standard error types across all workers."""
    DATA_VALIDATION_ERROR = "data_validation_error"
    COMPUTATION_ERROR = "computation_error"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    MISSING_DATA = "missing_data"
    INVALID_PARAMETER = "invalid_parameter"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"
```

Use these in your `_add_error()` calls:

```python
self._add_error(result, ErrorType.COMPUTATION_ERROR, "Error message")
# NOT: ErrorType.LOAD_ERROR (doesn't exist)
```

---

### Step 4: Create Tests

Create a test file following the pattern from `scripts/test_error_intelligence_aggregator.py`:

```python
from agents.your_agent.workers.your_worker import YourWorker
from agents.error_intelligence.main import ErrorIntelligence

def test_error_tracking_in_your_agent():
    """Test that your workers properly track errors."""
    print("\n=== Test: Error tracking in your_agent ===")
    ei = ErrorIntelligence()
    ei.error_tracker.clear()  # Start fresh
    
    worker = YourWorker()
    
    # Execute with sample data
    result = worker.execute(param1=value1, param2=value2)
    
    # Verify tracking
    patterns = ei.error_tracker.get_patterns()
    assert patterns["your_agent_name"]["successes"] > 0
    
    print(f"✓ Error tracking working")
    print(f"  - Successes tracked: {patterns['your_agent_name']['successes']}")
```

**CRITICAL**: Always call `ei.error_tracker.clear()` at the start of tests to ensure clean state.

---

## Implementation Checklist for New Agent

### Pre-Implementation
- [ ] Agent folder exists: `agents/your_agent/`
- [ ] Workers folder exists: `agents/your_agent/workers/`
- [ ] Base worker defined: `agents/your_agent/workers/base_worker.py`

### Implementation
- [ ] Import ErrorIntelligence in each worker
- [ ] Add `self.error_intelligence = ErrorIntelligence()` in `__init__()`
- [ ] Wrap execute() with try-except
- [ ] Call `track_success()` on success
- [ ] Call `track_error()` on failure
- [ ] Use valid ErrorType enum values
- [ ] Update context with relevant data

### Testing
- [ ] Create test file: `scripts/test_error_intelligence_[agent_name].py`
- [ ] Test successful tracking
- [ ] Test error tracking
- [ ] Verify health calculation
- [ ] Test edge cases

### Documentation
- [ ] Update this guide with agent-specific examples
- [ ] Add docstrings explaining tracking
- [ ] Document ErrorType choices

---

## Integration Points by Agent Type

### For Data Processing Agents (e.g., Loader, Explorer)

```python
self.error_intelligence.track_success(
    agent_name="loader",
    worker_name="CSVWorker",
    operation="load_csv",
    context={
        "file_size": file_size,
        "row_count": row_count,
        "columns": len(df.columns)
    }
)
```

### For Analysis Agents (e.g., Analyzer, Processor)

```python
self.error_intelligence.track_success(
    agent_name="analyzer",
    worker_name="CorrelationWorker",
    operation="compute_correlations",
    context={
        "columns_analyzed": len(numeric_cols),
        "correlation_threshold": threshold
    }
)
```

### For Report/Output Agents (e.g., Reporter, Visualizer)

```python
self.error_intelligence.track_success(
    agent_name="reporter",
    worker_name="PDFGenerator",
    operation="generate_report",
    context={
        "report_type": "executive_summary",
        "pages_generated": page_count
    }
)
```

---

## Common Patterns

### Pattern 1: Worker with Validation

```python
def execute(self, **kwargs) -> WorkerResult:
    try:
        # Validation
        if not self._validate_input(**kwargs):
            raise ValueError("Invalid input")
        
        # Processing
        result = self._run_processing(**kwargs)
        
        # Track success
        self.error_intelligence.track_success(
            agent_name="your_agent",
            worker_name=self.worker_name,
            operation="processing_operation",
            context=kwargs
        )
        
        return result
        
    except Exception as e:
        self.error_intelligence.track_error(
            agent_name="your_agent",
            worker_name=self.worker_name,
            error_type=type(e).__name__,
            error_message=str(e),
            context=kwargs
        )
        raise
```

### Pattern 2: Worker with Multiple Operations

```python
def execute(self, **kwargs) -> WorkerResult:
    try:
        # Operation 1
        result1 = self._operation_1(**kwargs)
        self.error_intelligence.track_success(
            agent_name="your_agent",
            worker_name=self.worker_name,
            operation="operation_1",
            context={**kwargs, "result": "success"}
        )
        
        # Operation 2
        result2 = self._operation_2(**kwargs)
        self.error_intelligence.track_success(
            agent_name="your_agent",
            worker_name=self.worker_name,
            operation="operation_2",
            context={**kwargs, "result": "success"}
        )
        
        return combine_results(result1, result2)
        
    except Exception as e:
        self.error_intelligence.track_error(
            agent_name="your_agent",
            worker_name=self.worker_name,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise
```

### Pattern 3: Worker with Conditional Tracking

```python
def execute(self, **kwargs) -> WorkerResult:
    try:
        result = self._run_task(**kwargs)
        
        # Only track if result meets quality threshold
        if result.quality_score >= 0.8:
            self.error_intelligence.track_success(
                agent_name="your_agent",
                worker_name=self.worker_name,
                operation="task_operation",
                context={"quality_score": result.quality_score}
            )
        else:
            # Track as degraded
            self.error_intelligence.track_error(
                agent_name="your_agent",
                worker_name=self.worker_name,
                error_type="LOW_QUALITY",
                error_message=f"Quality score: {result.quality_score}",
                context={"quality_score": result.quality_score}
            )
        
        return result
        
    except Exception as e:
        self.error_intelligence.track_error(...)
        raise
```

---

## Health Score Interpretation

The system calculates health based on success/failure ratios:

| Success Rate | Status | Color |
|---|---|---|
| ≥ 90% | HEALTHY | 🟢 Green |
| 70-89% | DEGRADED | 🟡 Yellow |
| < 70% | BROKEN | 🔴 Red |

Example:
```python
patterns = ei.error_tracker.get_patterns()
health = ei.get_worker_health()

# Health structure:
health["your_agent"]["agent_health"]["status"]  # HEALTHY/DEGRADED/BROKEN
health["your_agent"]["workers"]["WorkerName"]["status"]
```

---

## Testing Your Implementation

### Test 1: Verify Singleton Pattern

```python
def test_singleton_pattern():
    """Verify ErrorTracker is shared across instances."""
    ei1 = ErrorIntelligence()
    ei2 = ErrorIntelligence()
    
    ei1.error_tracker.clear()
    ei1.error_tracker.track_success("agent", "worker", "op")
    
    # Both should see the same data
    assert ei1.error_tracker.get_patterns() == ei2.error_tracker.get_patterns()
    assert ei1.error_tracker is ei2.error_tracker  # Same instance
```

### Test 2: Verify Tracking Works

```python
def test_success_tracking():
    """Verify successful operations are tracked."""
    ei = ErrorIntelligence()
    ei.error_tracker.clear()
    
    ei.track_success("test_agent", "test_worker", "test_op")
    
    patterns = ei.error_tracker.get_patterns()
    assert patterns["test_agent"]["successes"] == 1
    assert patterns["test_agent"]["workers"]["test_worker"]["successes"] == 1
```

### Test 3: Verify Health Calculation

```python
def test_health_calculation():
    """Verify health scores are calculated correctly."""
    ei = ErrorIntelligence()
    ei.error_tracker.clear()
    
    # 9 successes, 1 failure = 90% = HEALTHY
    for i in range(9):
        ei.track_success("agent", "worker", "op")
    ei.track_error("agent", "worker", "ERROR", "Test error")
    
    health = ei.get_worker_health()
    assert health["agent"]["agent_health"]["status"] == "HEALTHY"
    assert health["agent"]["agent_health"]["success_rate"] == 90.0
```

---

## Troubleshooting

### Issue: `KeyError: 'agent_name'` in Tests

**Cause**: ErrorTracker was not cleared before test, or tracking wasn't called.

**Fix**:
```python
ei = ErrorIntelligence()
ei.error_tracker.clear()  # Always clear first!
# Then track something...
ei.track_success(...)
```

### Issue: Multiple Workers Show Same Stats

**Cause**: ErrorTracker is a singleton (by design), so all workers share data.

**Solution**: This is intentional. Use `ei.error_tracker.get_patterns()["agent_name"]["workers"]` to see per-worker stats.

### Issue: Worker Not Tracking Errors

**Cause**: Exception is caught but not re-raised, or tracking call is missing.

**Fix**:
```python
except Exception as e:
    self.error_intelligence.track_error(...)  # Must call tracking
    raise  # Must re-raise!
```

---

## Quick Start Template

Copy this template for a new agent:

```python
"""[AgentName] Worker - [Description]."""

from typing import Optional, Dict, Any
from agents.error_intelligence.main import ErrorIntelligence
from agents.aggregator.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class [WorkerName](BaseWorker):
    """Worker that performs [specific task]."""
    
    def __init__(self):
        """Initialize worker."""
        super().__init__("[WorkerName]")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute the worker's task."""
        try:
            result = self._run_task(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="[agent_name]",
                worker_name="[WorkerName]",
                operation="[operation_name]",
                context={k: v for k, v in kwargs.items() if k != 'df'}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="[agent_name]",
                worker_name="[WorkerName]",
                error_type=type(e).__name__,
                error_message=str(e),
                context=kwargs
            )
            raise
    
    def _run_task(self, **kwargs) -> WorkerResult:
        """Perform the actual task."""
        result = self._create_result(task_type="[task_type]")
        
        try:
            # Your implementation here
            result.data = {"key": "value"}
            return result
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="error"
            )
            result.success = False
            return result
```

---

## Next Steps

1. **Identify all agents** in your system
2. **List all workers** for each agent
3. **Apply this pattern** to each worker
4. **Create test files** for each agent
5. **Run tests** to verify tracking works
6. **Monitor health** via ProjectManager

---

## References

- **ErrorIntelligence**: `agents/error_intelligence/main.py`
- **ErrorTracker**: `agents/error_intelligence/workers/error_tracker.py`
- **Reference Implementation**: `agents/aggregator/workers/`
- **Test Examples**: `scripts/test_error_intelligence_aggregator.py`
- **Base Worker**: `agents/aggregator/workers/base_worker.py`

---

## Support

For questions or issues:
1. Check the **Troubleshooting** section above
2. Review the **Aggregator implementation** for reference
3. Compare your code with the test files
4. Verify ErrorTracker is being used as a singleton

Happy integrating! 🚀
