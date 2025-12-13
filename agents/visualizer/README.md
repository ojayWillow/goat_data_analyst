# Visualizer Agent - A+ Data Visualization

**Version:** 2.0.0

The Visualizer Agent creates interactive charts from tabular data with enterprise-grade error handling, data quality tracking, and automatic retry mechanisms.

## Overview

Visualize your data with 7 interactive chart types:

- **Line Charts** - Time-series and trend analysis
- **Bar Charts** - Categorical comparisons
- **Scatter Plots** - Correlation analysis
- **Histograms** - Distribution visualization
- **Box Plots** - Quartile and outlier detection
- **Heatmaps** - Correlation matrices
- **Pie Charts** - Composition analysis

All charts are powered by Plotly, with full customization support.

## Quick Start

```python
from agents.visualizer.visualizer import Visualizer
import pandas as pd

# Create agent
viz = Visualizer()

# Load data
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=100),
    'sales': range(100, 200),
    'region': ['North']*50 + ['South']*50
})
viz.set_data(df)

# Create charts
line_result = viz.line_chart('date', 'sales', title='Sales Trend')
bar_result = viz.bar_chart('region', 'sales', title='Sales by Region')

# Check health
health = viz.get_health_report()
print(f"Health: {health['overall_health']:.1f}%")
```

## Features

### 1. Data Quality Tracking

Automatically detects and tracks:
- Null values (percentage, location)
- Duplicate rows
- Data type mismatches
- Missing values by column

**Quality Score:** 0-1 range
- 1.0 = Perfect data
- 0.9+ = Minor issues
- 0.7-0.9 = Moderate issues
- <0.7 = Significant data quality problems

### 2. Error Intelligence

Comprehensive error tracking:
- Standardized error types (25+ categories)
- Automatic error classification
- Error pattern analysis
- Recovery recommendations

Errors are tracked by:
- Worker (which chart type)
- Error type (data, parameter, rendering)
- Timestamp
- Context (columns affected, sample values)

### 3. Health Reporting

Get comprehensive health metrics:

```python
health = viz.get_health_report()

# Returns:
{
    'status': 'healthy',                    # healthy | degraded
    'overall_health': 87.5,                 # 0-100%
    'total_charts_created': 5,
    'total_errors': 2,
    'error_types': {'missing_column': 1, 'data_type_error': 1},
    'worker_health': {
        'line': 95.0,
        'bar': 88.0,
        'scatter': 100.0,
        ...
    },
    'average_quality_score': 0.92,
    'execution_count': 5,
    'recommendations': [
        'Found 2 duplicate rows. Consider deduplication.',
        'Data contains 3.2% null values.'
    ]
}
```

### 4. Resilience

Automatic retry with exponential backoff:
- 3 retry attempts for chart creation
- 2 second initial delay
- Exponential backoff (2x)
- Timeout protection (30 seconds)

### 5. Input Validation

Robust validation for all inputs:
- DataFrame type checking
- Column existence verification
- Data type validation
- Size limit enforcement
- Parameter range validation

## API Reference

### Visualizer Methods

#### set_data(df: DataFrame) → None

Load data for visualization.

```python
viz.set_data(df)
# Resets previous charts and execution history
```

**Raises:**
- `TypeError`: If df not DataFrame
- `ValueError`: If df is empty

#### line_chart(...) → Dict

Create line chart for time-series or continuous data.

```python
result = viz.line_chart(
    x_col='date',           # Required: X-axis column
    y_col='value',          # Required: Y-axis column
    title='Trend',          # Optional
    theme='plotly_white',   # Optional
    markers=True            # Optional: Show markers
)
```

#### bar_chart(...) → Dict

Create bar chart for categorical comparisons.

```python
result = viz.bar_chart(
    x_col='region',         # Required: Categorical column
    y_col='sales',          # Required: Numeric column
    title='By Region',      # Optional
    color='category'        # Optional: Grouping column
)
```

#### scatter_plot(...) → Dict

Create scatter plot for correlation analysis.

```python
result = viz.scatter_plot(
    x_col='x',
    y_col='y',
    color_col='category',   # Optional: Color dimension
    size_col='size'         # Optional: Size dimension
)
```

#### histogram(...) → Dict

Create histogram for distribution analysis.

```python
result = viz.histogram(
    col='values',           # Required: Column to analyze
    bins=30,                # Optional: Number of bins (5-200)
    title='Distribution'
)
```

#### box_plot(...) → Dict

Create box plot for quartile analysis.

```python
result = viz.box_plot(
    y_col='values',         # Required: Numeric column
    x_col='category',       # Optional: Grouping column
    title='Quartiles'
)
```

#### heatmap(...) → Dict

Create correlation heatmap.

```python
result = viz.heatmap(
    numeric_only=True,      # Optional: Only numeric columns
    palette='rdbu'          # Optional: Color palette
)
```

#### pie_chart(...) → Dict

Create pie chart for composition analysis.

```python
result = viz.pie_chart(
    col='category',         # Required: Column to visualize
    title='Composition'
)
```

#### list_charts() → Dict

List all created charts.

```python
charts = viz.list_charts()
# Returns: {
#     'status': 'success',
#     'count': 5,
#     'charts': [
#         {'id': 'line_0', 'quality_score': 0.95, 'timestamp': '...'},
#         {...}
#     ]
# }
```

#### get_health_report() → Dict

Get comprehensive health metrics (see Features section).

#### get_summary() → str

Get text summary of agent state.

## Chart Result Format

All chart methods return standardized results:

```python
{
    'success': True,                        # Creation succeeded
    'data': <plotly.Figure>,                # Plotly figure object
    'quality_score': 0.95,                  # Data quality (0-1)
    'rows_processed': 100,
    'rows_failed': 5,
    'metadata': {
        'x_column': 'date',
        'y_column': 'sales',
        'data_points': 100,
        'title': 'Sales Trend',
        'theme': 'plotly_white'
    },
    'errors': [],                           # Any errors encountered
    'warnings': [],                         # Non-fatal warnings
    'data_quality_issues': [                # Detected issues
        {
            'issue_type': 'null_values',
            'rows_affected': 5,
            'severity': 'warning'
        }
    ],
    'execution_time_ms': 234.5,
    'plotly_json': '...'                    # JSON representation
}
```

## Input Requirements

### DataFrame Requirements

- **Type:** pandas.DataFrame
- **Minimum rows:** 1
- **Maximum rows:** No limit
- **Maximum columns:** 10,000
- **Data types:** Supports numeric, string, datetime, categorical

### Column Requirements

Vary by chart type:

| Chart Type | X Column | Y Column | Additional |
|-----------|----------|----------|-------------|
| Line | Datetime or numeric | Numeric | Optional: markers |
| Bar | String/categorical | Numeric | Optional: color column |
| Scatter | Numeric | Numeric | Optional: color, size |
| Histogram | Numeric | - | Bins parameter |
| Box Plot | Optional: categorical | Numeric | - |
| Heatmap | - | - | 2+ numeric columns |
| Pie | Categorical | - | - |

## Error Handling

### Common Errors

**MissingColumnError**
```python
Error: Missing columns: ['missing_col']. Available: ['a', 'b', 'c']

Solution:
Check DataFrame column names with df.columns
Verify correct spelling and case sensitivity
```

**InvalidDataTypeError**
```python
Error: Column 'x' is not numeric, got object

Solution:
Convert column: df['x'] = pd.to_numeric(df['x'])
Or filter to numeric columns: df.select_dtypes(include=['number'])
```

**DataQualityWarning**
```python
Warning: Found 50 null values (5.0%) in column 'sales'

Solution:
Handle nulls: df.dropna() or df.fillna(0)
Check data source for data quality issues
```

### Error Intelligence

When chart creation fails, the error is automatically tracked with:
- Error type (standardized)
- Error message (descriptive)
- Context (columns affected, sample values)
- Timestamp
- Worker that failed

Access errors via health report:

```python
health = viz.get_health_report()
for error_type, count in health['error_types'].items():
    print(f"{error_type}: {count} occurrences")
```

## Data Quality

### Quality Calculation

Quality Score = 1.0 - (problematic_cells / total_cells)

Problematic cells include:
- Null values
- Duplicate rows (weighted)

### Quality Score Thresholds

- **0.95-1.0:** Excellent (> threshold)
- **0.85-0.95:** Good (acceptable)
- **0.70-0.85:** Fair (monitor)
- **< 0.70:** Poor (investigate)

### Data Issues Detected

Automatically reports:
- Null values by column
- Duplicate rows
- Data type mismatches
- Extreme value outliers (optional)

## Advanced Usage

### Custom Themes

All chart methods support Plotly themes:

```python
viz.line_chart('x', 'y', theme='plotly_dark')
# Options: plotly, plotly_white, plotly_dark, ggplot2, seaborn, etc.
```

### Large Datasets

For performance with large datasets:

```python
# Sample data before visualization
sampled_df = df.sample(n=10000, random_state=42)
viz.set_data(sampled_df)
```

### Batch Processing

```python
viz = Visualizer()
viz.set_data(df)

charts = []
for col in df.select_dtypes(include=['number']).columns:
    result = viz.histogram(col=col)
    charts.append(result)

health = viz.get_health_report()
print(f"Created {health['total_charts_created']} charts")
```

## Performance

### Typical Execution Times

| Chart Type | Small (100 rows) | Medium (10K rows) | Large (100K rows) |
|-----------|------------------|-------------------|-------------------|
| Line | 50-100ms | 150-300ms | 500-1000ms |
| Bar | 40-80ms | 120-200ms | 400-800ms |
| Scatter | 60-120ms | 200-400ms | 600-1200ms |
| Histogram | 30-50ms | 100-150ms | 300-600ms |
| Box Plot | 40-70ms | 120-200ms | 400-800ms |
| Heatmap | 100-200ms | 300-600ms | 1000-2000ms |
| Pie | 50-100ms | 150-300ms | 500-1000ms |

### Optimization Tips

1. **Sample large datasets** (>100K rows)
2. **Use numeric_only** for heatmaps with mixed types
3. **Limit pie chart categories** (<20 for readability)
4. **Pre-filter data** before visualization

## Architecture

```
Visualizer (Agent)
├── LineChartWorker
├── BarChartWorker
├── ScatterPlotWorker
├── HistogramWorker
├── BoxPlotWorker
├── HeatmapWorker
└── PieChartWorker

Each Worker:
├── Input Validation
├── Data Quality Check
├── Chart Generation
├── Error Tracking
└── Result Formatting

Integration:
├── Error Intelligence System
├── Structured Logging
├── Retry Mechanism
└── Health Monitoring
```

## Testing

Run comprehensive test suite:

```bash
pytest tests/test_visualizer_a_plus.py -v --cov=agents.visualizer
```

**Test Coverage:** 90%+

**Test Categories:**
- Data management (5 tests)
- All 7 workers (25+ tests)
- Data quality (5 tests)
- Integration (5 tests)
- Error handling (5 tests)

## Version History

### v2.0.0 (Current - A+ Standards)

**New Features:**
- Comprehensive error intelligence integration
- Data quality scoring (0-1 range)
- Health monitoring and reporting
- Execution history tracking
- Worker-level health metrics
- Chart cache management (LRU)
- Automatic retry with exponential backoff
- Structured error classification

**Improvements:**
- Full type hints (100%)
- Complete docstrings
- Enhanced validation
- Better error messages
- Performance optimization

### v1.0.0 (Legacy)

Initial release with basic chart functionality.

## Troubleshooting

### Chart not displaying

```python
# Verify data is set
assert viz.data is not None

# Check result success
assert result['success'] == True

# View errors
print(result['errors'])
```

### Poor data quality score

```python
# Check quality issues
for issue in result['data_quality_issues']:
    print(issue)

# Get recommendations
health = viz.get_health_report()
for rec in health['recommendations']:
    print(rec)
```

### Out of memory

```python
# Sample data
df_sample = df.sample(frac=0.1)  # 10% sample
viz.set_data(df_sample)
```

## Support

For issues, feature requests, or questions:
1. Check the Troubleshooting section
2. Review test cases in `tests/test_visualizer_a_plus.py`
3. Consult ARCHITECTURE.md for detailed design
4. Review API_REFERENCE.md for method details

## License

See LICENSE file in repository.
