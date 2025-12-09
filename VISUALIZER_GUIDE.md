# Visualizer Agent - Plugin Architecture Guide

## Quick Start

```python
from agents.visualizer import Visualizer
import pandas as pd

# Create visualizer
vis = Visualizer()

# Load data
df = pd.read_csv('data.csv')
vis.set_data(df)

# Create chart
result = vis.line_chart('date', 'sales', title='Sales Over Time')
if result['success']:
    print(f"Chart created: {result['chart_type']}")
```

---

## 7 Built-In Chart Types

### 1. Line Chart (Time Series)
```python
vis.line_chart(
    x_col='date',
    y_col='sales',
    title='Sales Trend',
    theme='plotly_white',
    markers=True
)
```

### 2. Bar Chart (Categorical)
```python
vis.bar_chart(
    x_col='region',
    y_col='sales',
    title='Sales by Region',
    color='category'
)
```

### 3. Scatter Plot (Correlations)
```python
vis.scatter_plot(
    x_col='units',
    y_col='sales',
    color_col='region',
    size_col='profit'
)
```

### 4. Histogram (Distribution)
```python
vis.histogram(
    col='sales',
    bins=30,
    title='Sales Distribution'
)
```

### 5. Box Plot (Quartiles)
```python
vis.box_plot(
    y_col='sales',
    x_col='region',
    title='Sales by Region'
)
```

### 6. Heatmap (Correlation)
```python
vis.heatmap(
    title='Correlation Matrix',
    palette='rdbu'
)
```

### 7. Pie Chart (Composition)
```python
vis.pie_chart(
    col='category',
    title='Market Share'
)
```

---

## 🎨 Themes (Easy Upgradeable)

Available themes:
- `plotly_white` - Clean, professional
- `plotly_dark` - Dark mode
- `plotly` - Default
- `ggplot2` - R style
- `seaborn` - Python data science style

**TO ADD NEW THEME:**
1. Edit `agents/visualizer/workers/config/themes.py`
2. Add to THEMES dict
3. Done! All workers automatically use it

```python
# In themes.py:
THEMES = {
    "my_theme": "my_plotly_template",
    # ...
}
```

---

## 🎭 Color Palettes (Easy Upgradeable)

Available palettes:
- Sequential: `viridis`, `plasma`, `inferno`, `blues`, `greens`
- Diverging: `rdbu`, `brbg`, `piyg`
- Categorical: `set1`, `set2`, `pastel`, `dark`, `bold`

**TO ADD NEW PALETTE:**
1. Edit `agents/visualizer/workers/config/palettes.py`
2. Add to PALETTES dict
3. Done! All workers automatically use it

```python
# In palettes.py:
PALETTES = {
    "my_palette": "Plotly_ColorScale",
    # ...
}
```

---

## 🔌 Plugin Architecture - Add New Chart Types

### Step 1: Create Worker

Copy `template_worker.py` and rename:

```python
# my_new_chart_worker.py
from .base_worker import BaseChartWorker, WorkerResult, ErrorType
from .config import get_theme

class MyNewChartWorker(BaseChartWorker):
    def __init__(self):
        super().__init__("MyNewChartWorker", "my_new_chart")
    
    def execute(self, **kwargs) -> WorkerResult:
        df = kwargs.get('df')
        result = self._create_result()
        
        # Validate
        validation = self._validate_dataframe(df)
        if validation:
            return validation
        
        # Your chart logic here
        # fig = px.my_chart_type(...)
        
        result.data = fig
        result.plotly_json = fig.to_json()
        return result
```

### Step 2: Register in `workers/__init__.py`

```python
from .my_new_chart_worker import MyNewChartWorker

__all__ = [
    # ... existing ...
    "MyNewChartWorker",
]
```

### Step 3: Add Method to Agent

```python
# In visualizer.py
def my_new_chart(self, **kwargs) -> Dict[str, Any]:
    if self.data is None:
        return {"status": "error", "message": "No data set"}
    
    result = self.my_new_chart_worker.safe_execute(
        df=self.data,
        **kwargs,
    )
    
    self._store_chart(result)
    return result.to_dict()
```

**DONE!** Your chart type is now available.

---

## ⚙️ Worker Architecture

### BaseChartWorker

All workers inherit from `BaseChartWorker` which provides:

```python
class BaseChartWorker(ABC):
    # Validation helpers
    def _validate_dataframe(df) -> WorkerResult
    def _validate_columns(df, columns) -> WorkerResult
    
    # Error handling
    def _add_error(result, error_type, message)
    def _add_warning(result, message)
    
    # Result creation
    def _create_result(task_type) -> WorkerResult
    
    # Execution
    def execute(**kwargs) -> WorkerResult  # Override this!
    def safe_execute(**kwargs) -> WorkerResult  # Error handling
```

### WorkerResult Format

All workers return standardized result:

```python
{
    "worker": "LineChartWorker",
    "chart_type": "line",
    "success": True,
    "data": <plotly_figure>,
    "metadata": {
        "x_column": "date",
        "y_column": "sales",
        "theme": "plotly_white",
        # ...
    },
    "errors": [],
    "warnings": [],
    "execution_time_ms": 45.2,
    "plotly_json": "<json_serialized_figure>",
}
```

---

## 🧪 Testing

### Unit Tests

Each worker has tests in `tests/test_visualizer.py`

```python
def test_line_chart():
    vis = Visualizer()
    vis.set_data(sample_df)
    result = vis.line_chart('x', 'y')
    assert result['success']
    assert result['chart_type'] == 'line'
```

### Integration Tests

Test agents together in `tests/test_integration.py`

```python
def test_full_pipeline():
    # Load data
    loader = DataLoader()
    df = loader.load('data.csv')['data']
    
    # Visualize
    vis = Visualizer()
    vis.set_data(df)
    result = vis.line_chart('x', 'y')
    assert result['success']
```

---

## 📊 Configuration Validation

### Validation Before Use

```python
from agents.visualizer.workers.config import ConfigValidator

# Validate theme
valid, msg = ConfigValidator.validate_theme('plotly_white')
if not valid:
    print(f"Error: {msg}")

# Validate palette
valid, msg = ConfigValidator.validate_palette('viridis')
if not valid:
    print(f"Error: {msg}")

# Validate bins
valid, msg = ConfigValidator.validate_bins(30)
if not valid:
    print(f"Error: {msg}")
```

---

## 🚀 Best Practices

1. **Always check result['success']** before using chart
2. **Use themes for consistency** across charts
3. **Leverage color coding** (color_col, size_col) for extra dimensions
4. **Add meaningful titles** for clarity
5. **Validate config** before passing to workers
6. **Extend plugins** instead of modifying existing workers

---

## 🔧 Common Patterns

### Create Multiple Charts

```python
vis = Visualizer()
vis.set_data(df)

# Create suite of charts
charts = []
charts.append(vis.line_chart('date', 'sales'))
charts.append(vis.bar_chart('region', 'sales'))
charts.append(vis.heatmap())

# Check all succeeded
all_success = all(c['success'] for c in charts)
print(f"Created {len([c for c in charts if c['success']])} charts")
```

### Handle Errors Gracefully

```python
result = vis.line_chart('col1', 'col2')
if not result['success']:
    for error in result['errors']:
        print(f"Error: {error['message']}")
else:
    print(f"Chart created successfully")
```

### List Available Options

```python
from agents.visualizer.workers.config import list_themes, list_palettes

themes = list_themes()
print(f"Available themes: {themes['available_themes']}")

palettes = list_palettes()
print(f"Available palettes: {palettes['available_palettes']}")
```

---

## 📈 Architecture Diagram

```
Visualizer (Agent)
    ├── LineChartWorker (extends BaseChartWorker)
    ├── BarChartWorker
    ├── ScatterPlotWorker
    ├── HistogramWorker
    ├── BoxPlotWorker
    ├── HeatmapWorker
    ├── PieChartWorker
    └── ConfigValidator
        ├── Themes (plotly_white, plotly_dark, ...)
        └── Palettes (viridis, rdbu, set1, ...)

        NEW CHART TYPE?
        └── Just extend BaseChartWorker + register!
```

---

## ✅ Summary

- **7 built-in chart types** - All your common needs
- **Plugin architecture** - Easy to add new charts
- **Theme system** - Consistent styling
- **Palette system** - Beautiful colors
- **Config validation** - Clear error messages
- **Extensible design** - Build on solid foundation

**Happy visualizing! 🎨**
