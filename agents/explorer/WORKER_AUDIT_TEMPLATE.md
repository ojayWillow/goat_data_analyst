# Explorer Agent - Worker Audit & Fix Template

## Status Summary

**Completed (3):**
- ✅ BaseWorker (foundation - fixed)
- ✅ NumericAnalyzer (template - fixed)
- ✅ CategoricalAnalyzer (template - fixed)

**Remaining (9):**
- ⏳ CorrelationAnalyzer
- ⏳ QualityAssessor
- ⏳ NormalityTester
- ⏳ DistributionComparison
- ⏳ DistributionFitter
- ⏳ SkewnessKurtosisAnalyzer
- ⏳ OutlierDetector
- ⏳ CorrelationMatrix
- ⏳ StatisticalSummary

---

## Fix Template Pattern

Every worker must follow this pattern:

### 1. **Imports & Constants**
```python
from typing import Any, Dict, Optional
import pandas as pd

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# Constants (magic numbers at top)
MIN_SAMPLES = 1
QUALITY_THRESHOLD = 0.8
```

### 2. **Class Docstring**
```python
class WorkerName(BaseWorker):
    """One-line summary.
    
    Longer description of what the worker does.
    
    Input Requirements:
        df: pandas.DataFrame - (required)
        column: str - (if needed)
    
    Output Format:
        result.data contains:
            key1: Description
            key2: Description
    
    Quality Score:
        - 1.0: All success
        - 1.0 - (warnings * 0.1) - (errors * 0.2): Reduced
        - Minimum: 0.0
    
    Example:
        >>> worker = WorkerName()
        >>> result = worker.safe_execute(df=df)
        >>> if result.success:
        ...     print(result.data)
    
    Raises:
        None (all errors in WorkerResult)
    """
```

### 3. **__init__**
```python
def __init__(self) -> None:
    """Initialize worker."""
    super().__init__("WorkerName")
    self.error_intelligence = ErrorIntelligence()
```

### 4. **_validate_input**
```python
def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
    """Validate input parameters.
    
    Returns:
        WorkerError if invalid, None if valid
    """
    df = kwargs.get('df')
    
    if df is None:
        return WorkerError(
            error_type=ErrorType.MISSING_DATA,
            message="No DataFrame provided",
            severity="error",
            suggestion="Call with df parameter"
        )
    
    if not isinstance(df, pd.DataFrame):
        return WorkerError(
            error_type=ErrorType.TYPE_ERROR,
            message=f"Expected DataFrame, got {type(df).__name__}",
            severity="error",
            suggestion="Pass a pandas DataFrame"
        )
    
    # Add worker-specific validation
    column = kwargs.get('column')
    if column and column not in df.columns:
        return WorkerError(
            error_type=ErrorType.INVALID_PARAMETER,
            message=f"Column '{column}' not found",
            severity="error",
            details={"available_columns": list(df.columns)},
            suggestion=f"Column must be one of: {list(df.columns)}"
        )
    
    return None
```

### 5. **execute** (MUST return WorkerResult, NEVER raise)
```python
def execute(self, **kwargs: Any) -> WorkerResult:
    """Execute the worker task.
    
    Args:
        df: DataFrame to analyze
        [other params]
    
    Returns:
        WorkerResult with success/failure status
    
    Note:
        NEVER raises. All errors in WorkerResult.
    """
    df = kwargs.get('df')
    result = self._create_result(task_type="worker_task")
    
    try:
        self.logger.info("Starting task")
        
        # Validation already done in safe_execute(), but double-check
        if df is None or df.empty:
            result.success = False
            result.quality_score = 0.0
            return result
        
        # Extract parameters
        column = kwargs.get('column')
        
        # Process data
        data: Dict[str, Any] = {}
        errors_found: list = []
        warnings_found: list = []
        
        # Core logic here
        try:
            # Do work
            data['key'] = 'value'
        except Exception as e:
            errors_found.append(str(e))
            self.logger.error(f"Error: {e}", exc_info=True)
        
        # Add errors/warnings
        for warning in warnings_found:
            self._add_warning(result, warning)
        
        for error_msg in errors_found:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                error_msg,
                severity="warning"
            )
        
        result.data = data
        
        # Quality score
        quality = 1.0
        quality -= len(warnings_found) * 0.1
        quality -= len(errors_found) * 0.2
        result.quality_score = max(0, min(1, quality))
        
        result.success = len(errors_found) == 0
        
        self.logger.info(f"Task complete (quality: {result.quality_score:.2f})")
        return result
    
    except Exception as e:
        """Safety net."""
        self.logger.error(f"Unexpected error: {e}", exc_info=True)
        self._add_error(
            result,
            ErrorType.UNKNOWN_ERROR,
            str(e),
            severity="critical"
        )
        result.success = False
        result.quality_score = 0.0
        return result
```

### 6. **Helper Methods**
```python
def _compute_something(self, col_name: str, series: pd.Series) -> Dict[str, Any]:
    """Helper to compute metric.
    
    Args:
        col_name: Column name
        series: Data series
    
    Returns:
        Dictionary of results
    
    Raises:
        Exception: If fails (caller handles)
    """
    try:
        result = {
            'key': float(series.mean()),
        }
        return result
    except Exception as e:
        self.logger.error(f"Error in _compute_something: {e}", exc_info=True)
        raise
```

---

## Checklist for Each Worker

### Code Quality
- [ ] All functions have type hints (Args and Returns)
- [ ] All constants defined at module top (no magic numbers in code)
- [ ] execute() NEVER raises, returns WorkerResult
- [ ] _validate_input() checks df type, not empty, and any required parameters
- [ ] docstrings include: summary, input requirements, output format, example, raises

### Error Handling
- [ ] Input validation in _validate_input()
- [ ] Try-catch for each column/item loop
- [ ] WorkerError objects with error_type, message, severity, suggestion
- [ ] Errors added to result, not raised
- [ ] Fallback exception handler returns WorkerResult

### Quality Score
- [ ] Quality starts at 1.0
- [ ] Reduced by 0.1 per warning
- [ ] Reduced by 0.2 per error
- [ ] Clamped 0.0-1.0
- [ ] Success based on errors, not exceptions

### Logging
- [ ] Log when starting task
- [ ] Log when errors occur (with exc_info=True)
- [ ] Log final result with quality score
- [ ] Use appropriate log levels (info, warning, error)

---

## Remaining Workers to Fix

### Priority 1: Core Workers (2)
1. **CorrelationAnalyzer** - Analyzes numeric correlations
2. **QualityAssessor** - Overall data quality assessment

### Priority 2: Statistical Workers (7)
3. **NormalityTester** - Shapiro-Wilk test
4. **DistributionComparison** - KS test  
5. **DistributionFitter** - Fit distributions
6. **SkewnessKurtosisAnalyzer** - Skewness/kurtosis
7. **OutlierDetector** - Z-score detection
8. **CorrelationMatrix** - Correlation heatmap
9. **StatisticalSummary** - Comprehensive summary

---

## Key Differences from Template

Each worker may differ in:
- **Input parameters**: Some need specific columns, thresholds, etc.
- **Output structure**: Different metrics returned in result.data
- **Validation logic**: Custom checks for parameters
- **Core computation**: Different statistical methods
- **Quality calculation**: May weight factors differently

But they ALL follow the same pattern for:
- Error handling
- Docstrings
- Type hints
- Never raising exceptions
- Returning WorkerResult

---

## Quick Apply

To fix a worker:
1. Copy the template pattern above
2. Adapt for worker's specific logic
3. Ensure validation is complete
4. Make sure execute() never raises
5. Add proper docstrings
6. Add type hints
7. Test with sample data

---

## Notes

- BaseWorker handles safe_execute() wrapper
- Workers only implement execute()
- safe_execute() adds timing, error tracking
- All errors tracked via error_intelligence
- Quality score drives agent health reporting
