# GOAT Data Analyst - Documentation

## Overview

GOAT Data Analyst is a production-grade aggregation engine for pandas DataFrames with advanced error handling, quality scoring, and comprehensive data validation. Built with A+ quality standards including type hints, input validation, error intelligence, and full test coverage.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from agents.aggregator.main import Aggregator
import pandas as pd

# Create aggregator
agg = Aggregator()

# Load data
df = pd.read_csv('data.csv')

# Run aggregation
result = agg.aggregate(
    data=df,
    operations=[
        {"type": "group_by", "by": "category", "agg": "sum"}
    ]
)

# Check quality
print(f"Quality Score: {result.quality_score}")
print(f"Success: {result.success}")
```

## Features

### Phase 1: Type Hints & Validation ✅
- Complete type hints on all 9 workers
- Comprehensive input validation
- Dataframe structure validation
- Column existence and type checking

### Phase 2: Quality Scoring ✅
- Quality score calculation (0.0-1.0)
- Null value tracking and penalties
- Duplicate detection and handling
- Metadata enrichment

### Phase 3: Advanced Error Handling ✅
- Infinity/NaN detection and handling
- Memory error catching with suggestions
- ValueError/TypeError specific handling
- Worker-specific error patterns
- Graceful degradation (skip bad records)
- Error Intelligence integration

## Workers

### StatisticsWorker
Computes statistical aggregations (mean, std, sum, min, max, median).

**Errors Tracked:** 9 types
- infinity_values, unexpected_nan, std_nan
- infinity_to_zero, nan_to_zero
- conversion_error, value_error, memory_error, overflow_error

**Quality Penalty:** 0-20%

### PivotWorker
Creates pivot tables from DataFrames.

**Errors Tracked:** 7 types
- pivot_value_error, memory_error, series_conversion_error
- reset_index_error, empty_pivot, infinity_in_result, nan_in_result

**Quality Penalty:** 0-20%

### GroupByWorker
Performs groupby aggregations with multiple functions.

**Errors Tracked:** 7 types
- groupby_error, invalid_agg_specs, aggregation_value_error
- memory_error, empty_result, infinity_in_result, nan_in_result

**Quality Penalty:** 0-20%

### CrossTabWorker
Creates cross-tabulations for categorical data.

**Errors Tracked:** 7 types
- crosstab_value_error, memory_error, series_conversion
- conversion_error, empty_result, infinity_in_result, nan_in_result

**Quality Penalty:** 0-20%

### ValueCountWorker
Counts unique values in columns.

**Errors Tracked:** 6 types
- value_count_type_error, value_conversion_error
- result_building_error, nunique_error, empty_result, memory_error

**Quality Penalty:** 0-15%

### LagLeadFunction
Calculates lag and lead operations for time series.

**Errors Tracked:** 2+ types
- shift_error, memory_error

**Quality Penalty:** 0-10%

### RollingAggregation
Computes rolling window aggregations.

**Errors Tracked:** 5+ types

**Quality Penalty:** 0-20%

### ExponentialWeighted
Calculates exponential weighted moving average (EWMA).

**Errors Tracked:** 4+ types

**Quality Penalty:** 0-15%

### WindowFunction
Performs multi-operation window functions.

**Errors Tracked:** 6+ types

**Quality Penalty:** 0-20%

## Quality Scoring

Quality scores reflect data completeness and error handling performance:

```
quality = max(0, min(1, 
    base_quality - null_penalty - error_penalty
))
```

### Penalties
- Null warnings: 0-15% (5% per warning)
- Duplicate handling: 0-15% (varies)
- Advanced errors: 0-20% (5% per error type)

### Interpretation
- 0.9-1.0: Excellent (no data quality issues)
- 0.8-0.9: Good (minor issues handled)
- 0.7-0.8: Fair (moderate issues)
- <0.7: Poor (significant quality issues)

## Error Handling

### Infinity Values
- **Detection:** np.isinf() checks on computed values
- **Handling:** Converted to 0.0 with tracking
- **Coverage:** 6/9 workers

### NaN Values
- **Detection:** np.isnan() checks after operations
- **Handling:** Converted to 0.0 with warning
- **Coverage:** 7/9 workers

### Memory Errors
- **Detection:** MemoryError exception catching
- **Handling:** Critical error with memory reduction suggestions
- **Coverage:** 9/9 workers

### Value Errors
- **Detection:** ValueError exception catching
- **Handling:** Per-operation error handling with user suggestions
- **Coverage:** 9/9 workers

### Empty Results
- **Detection:** Post-operation empty DataFrame checks
- **Handling:** Error with data validation suggestion
- **Coverage:** 8/9 workers

## Metadata

All workers return rich metadata:

```python
result.data = {
    "rows_processed": int,
    "null_count": int,
    "quality_score": float,
    
    # Phase 3 Additions
    "advanced_errors_encountered": int,
    "advanced_error_types": list,
    
    # Worker-specific fields
    "infinity_values_found": int,
    "nan_values_found": int,
}
```

## Error Intelligence

All errors are tracked through ErrorIntelligence:

```python
self.error_intelligence.track_success(
    agent_name="aggregator",
    worker_name="WorkerName",
    operation="operation_type",
    context={
        "success": True,
        "quality_score": 0.95,
        "advanced_errors": 0,
        "error_types": []
    }
)
```

## API Reference

See [API.md](./API.md) for complete API documentation.

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for system design and worker hierarchy.

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

## Testing

Run tests with:

```bash
pytest tests/ -v --cov=agents/aggregator
```

For specific worker tests:

```bash
pytest tests/workers/test_statistics_worker.py -v
```

See [TESTING.md](./TESTING.md) for detailed testing documentation.

## Performance

### Benchmarks
- **StatisticsWorker:** ~50ms for 10K rows
- **PivotWorker:** ~100ms for 10K rows with 10 categories
- **GroupByWorker:** ~80ms for 10K rows with 5 groups

### Optimization Tips
1. Use appropriate data types (uint32 vs uint64)
2. Pre-filter data before aggregation
3. Use groupby for large categorical operations
4. Enable memory monitoring for very large datasets

## Contributing

Contributions welcome! Follow these guidelines:

1. **Type Hints:** All new code requires type hints
2. **Testing:** 90%+ coverage for new workers
3. **Error Handling:** Must catch Memory/Value/Type errors
4. **Documentation:** Update README and docstrings
5. **Quality:** Target 0.95+ quality score

## License

MIT License - See LICENSE file

## Version

**Current:** 1.0.0  
**Last Updated:** 2025-12-13

---

**Built with A+ Quality Standards:**
- ✅ Complete type hints
- ✅ Input validation
- ✅ Quality scoring
- ✅ Advanced error handling
- ✅ Comprehensive testing
