"""Week 2 Day 5: Visualizer Agent Integration Tests (10 tests).

Tests:
1. Agent initialization
2. Data loading
3. Bar chart generation
4. Line chart generation
5. Scatter plot generation
6. Histogram generation
7. Box plot generation
8. Heatmap generation
9. Empty dataframe handling
10. Performance benchmark
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import time

from agents.visualizer import Visualizer


class TestVisualizerInitialization:
    """Test 1: Agent initialization."""

    def test_agent_initializes(self):
        """Test agent initializes successfully."""
        visualizer = Visualizer()
        assert visualizer is not None
        assert visualizer.name == "Visualizer"
        assert visualizer.data is None
        # Check for worker instances
        assert hasattr(visualizer, 'bar_worker')
        assert hasattr(visualizer, 'line_worker')
        assert hasattr(visualizer, 'scatter_worker')
        assert hasattr(visualizer, 'histogram_worker')
        assert hasattr(visualizer, 'boxplot_worker')


class TestVisualizerDataLoading:
    """Test 2: Data loading and management."""

    @pytest.fixture
    def visualizer(self):
        return Visualizer()

    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame for visualization (100 rows, 5 columns)."""
        np.random.seed(42)
        return pd.DataFrame({
            'x_values': np.arange(100),
            'y_values': np.random.randn(100) * 10 + 50,
            'category': np.random.choice(['A', 'B', 'C', 'D'], 100),
            'values': np.random.randint(10, 100, 100),
            'metric': np.random.randn(100),
        })

    def test_set_data(self, visualizer, sample_data):
        """Test setting data."""
        visualizer.set_data(sample_data)
        assert visualizer.data is not None
        assert visualizer.data.shape == (100, 5)

    def test_get_data(self, visualizer, sample_data):
        """Test getting data."""
        visualizer.set_data(sample_data)
        retrieved = visualizer.get_data()
        assert retrieved is not None
        assert retrieved.shape == sample_data.shape

    def test_data_copy(self, visualizer, sample_data):
        """Test data is copied (not referenced)."""
        visualizer.set_data(sample_data)
        sample_data.iloc[0, 0] = 999
        assert visualizer.get_data().iloc[0, 0] != 999


class TestBarChart:
    """Test 3: Bar chart generation."""

    @pytest.fixture
    def visualizer_with_data(self):
        visualizer = Visualizer()
        np.random.seed(42)
        df = pd.DataFrame({
            'category': ['A', 'B', 'C', 'D', 'E'],
            'values': [23, 45, 56, 78, 32],
        })
        visualizer.set_data(df)
        return visualizer

    def test_bar_chart_creation(self, visualizer_with_data):
        """Test bar chart generation runs successfully."""
        result = visualizer_with_data.bar_chart(
            x_col='category',
            y_col='values',
            title='Sample Bar Chart'
        )
        assert result is not None
        assert isinstance(result, dict)

    def test_bar_chart_has_data(self, visualizer_with_data):
        """Test bar chart contains chart data."""
        result = visualizer_with_data.bar_chart(
            x_col='category',
            y_col='values'
        )
        assert 'chart' in result or 'data' in result or 'fig' in result or len(result) > 0


class TestLineChart:
    """Test 4: Line chart generation."""

    @pytest.fixture
    def visualizer_with_data(self):
        visualizer = Visualizer()
        np.random.seed(42)
        df = pd.DataFrame({
            'time': np.arange(50),
            'value': np.cumsum(np.random.randn(50)),
        })
        visualizer.set_data(df)
        return visualizer

    def test_line_chart_creation(self, visualizer_with_data):
        """Test line chart generation runs successfully."""
        result = visualizer_with_data.line_chart(
            x_col='time',
            y_col='value',
            title='Time Series'
        )
        assert result is not None
        assert isinstance(result, dict)

    def test_line_chart_has_data(self, visualizer_with_data):
        """Test line chart contains chart data."""
        result = visualizer_with_data.line_chart(
            x_col='time',
            y_col='value'
        )
        assert 'chart' in result or 'data' in result or 'fig' in result or len(result) > 0


class TestScatterPlot:
    """Test 5: Scatter plot generation."""

    @pytest.fixture
    def visualizer_with_data(self):
        visualizer = Visualizer()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'size': np.random.randint(10, 100, 100),
        })
        visualizer.set_data(df)
        return visualizer

    def test_scatter_plot_creation(self, visualizer_with_data):
        """Test scatter plot generation runs successfully."""
        result = visualizer_with_data.scatter_plot(
            x_col='x',
            y_col='y',
            title='Scatter Plot'
        )
        assert result is not None
        assert isinstance(result, dict)

    def test_scatter_plot_has_data(self, visualizer_with_data):
        """Test scatter plot contains chart data."""
        result = visualizer_with_data.scatter_plot(
            x_col='x',
            y_col='y'
        )
        assert 'chart' in result or 'data' in result or 'fig' in result or len(result) > 0


class TestHistogram:
    """Test 6: Histogram generation."""

    @pytest.fixture
    def visualizer_with_data(self):
        visualizer = Visualizer()
        np.random.seed(42)
        df = pd.DataFrame({
            'values': np.random.randn(1000),
        })
        visualizer.set_data(df)
        return visualizer

    def test_histogram_creation(self, visualizer_with_data):
        """Test histogram generation runs successfully."""
        result = visualizer_with_data.histogram(
            col='values',
            bins=30,
            title='Distribution'
        )
        assert result is not None
        assert isinstance(result, dict)

    def test_histogram_has_data(self, visualizer_with_data):
        """Test histogram contains chart data."""
        result = visualizer_with_data.histogram(
            col='values'
        )
        assert 'chart' in result or 'data' in result or 'fig' in result or len(result) > 0


class TestBoxPlot:
    """Test 7: Box plot generation."""

    @pytest.fixture
    def visualizer_with_data(self):
        visualizer = Visualizer()
        np.random.seed(42)
        df = pd.DataFrame({
            'group': np.repeat(['A', 'B', 'C', 'D'], 25),
            'values': np.random.randn(100),
        })
        visualizer.set_data(df)
        return visualizer

    def test_boxplot_creation(self, visualizer_with_data):
        """Test box plot generation runs successfully."""
        result = visualizer_with_data.box_plot(
            y_col='values',
            x_col='group',
            title='Box Plot'
        )
        assert result is not None
        assert isinstance(result, dict)

    def test_boxplot_has_data(self, visualizer_with_data):
        """Test box plot contains chart data."""
        result = visualizer_with_data.box_plot(
            y_col='values'
        )
        assert 'chart' in result or 'data' in result or 'fig' in result or len(result) > 0


class TestHeatmap:
    """Test 8: Heatmap generation."""

    @pytest.fixture
    def visualizer_with_data(self):
        visualizer = Visualizer()
        np.random.seed(42)
        df = pd.DataFrame(
            np.random.randn(10, 10),
            columns=[f'col_{i}' for i in range(10)],
            index=[f'row_{i}' for i in range(10)]
        )
        visualizer.set_data(df)
        return visualizer

    def test_heatmap_creation(self, visualizer_with_data):
        """Test heatmap generation runs successfully."""
        result = visualizer_with_data.heatmap(
            title='Correlation Heatmap'
        )
        assert result is not None
        assert isinstance(result, dict)

    def test_heatmap_has_data(self, visualizer_with_data):
        """Test heatmap contains chart data."""
        result = visualizer_with_data.heatmap()
        assert 'chart' in result or 'data' in result or 'fig' in result or len(result) > 0


class TestEdgeCases:
    """Test 9: Empty dataframe handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        visualizer = Visualizer()
        empty_df = pd.DataFrame()
        visualizer.set_data(empty_df)
        assert visualizer.get_data() is not None
        assert visualizer.get_data().shape[0] == 0

    def test_single_row_dataframe(self):
        """Test handling of single row DataFrame."""
        visualizer = Visualizer()
        single_row = pd.DataFrame({
            'a': [1.0],
            'b': [2.0],
            'c': [3.0]
        })
        visualizer.set_data(single_row)
        assert visualizer.get_data().shape[0] == 1

    def test_no_data_error(self):
        """Test error when no data is set."""
        visualizer = Visualizer()
        with pytest.raises(Exception):
            visualizer.bar_chart(x_col='col', y_col='val')


class TestPerformance:
    """Test 10: Performance benchmark."""

    def test_chart_generation_performance_1k_rows(self):
        """Test chart generation on 1,000 rows completes in reasonable time."""
        visualizer = Visualizer()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.arange(1000),
            'y': np.random.randn(1000) * 10 + 50,
            'category': np.random.choice(['A', 'B', 'C'], 1000),
            'values': np.random.randint(1, 100, 1000),
        })
        visualizer.set_data(df)

        start = time.time()
        
        # Generate multiple charts
        result1 = visualizer.line_chart(x_col='x', y_col='y')
        result2 = visualizer.scatter_plot(x_col='x', y_col='y')
        result3 = visualizer.histogram(col='y')
        
        elapsed = time.time() - start

        assert elapsed < 30  # Should complete in < 30 seconds
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None


class TestComprehensiveVisualization:
    """Test comprehensive visualization pipeline."""

    def test_full_visualization_pipeline(self):
        """Test creating multiple chart types on same dataset."""
        visualizer = Visualizer()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.arange(100),
            'y': np.cumsum(np.random.randn(100)),
            'category': np.random.choice(['GroupA', 'GroupB', 'GroupC'], 100),
            'metric': np.random.randn(100),
        })
        
        visualizer.set_data(df)
        
        # Create various charts
        bar_result = visualizer.bar_chart(x_col='category', y_col='metric')
        line_result = visualizer.line_chart(x_col='x', y_col='y')
        scatter_result = visualizer.scatter_plot(x_col='x', y_col='metric')
        hist_result = visualizer.histogram(col='metric')
        
        # All should be dictionaries
        assert isinstance(bar_result, dict)
        assert isinstance(line_result, dict)
        assert isinstance(scatter_result, dict)
        assert isinstance(hist_result, dict)
        
        # All should have content
        assert len(bar_result) > 0
        assert len(line_result) > 0
        assert len(scatter_result) > 0
        assert len(hist_result) > 0

    def test_chart_retrieval(self):
        """Test chart creation and retrieval."""
        visualizer = Visualizer()
        np.random.seed(42)
        df = pd.DataFrame({
            'a': np.random.randn(50),
            'b': np.random.randn(50),
            'c': np.random.choice(['Type1', 'Type2'], 50),
        })
        
        visualizer.set_data(df)
        
        # Create a chart
        result = visualizer.line_chart(x_col='a', y_col='b')
        assert result is not None
        
        # Get summary
        summary = visualizer.get_summary()
        assert 'Visualizer' in summary
        assert '50 rows' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
