"""Integration tests - Agents working together.

Tests the full pipeline:
1. DataLoader loads data
2. Explorer analyzes it
3. Visualizer creates charts
4. AnomalyDetector finds outliers
5. Aggregator summarizes results
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

from agents.data_loader import DataLoader
from agents.explorer import Explorer
from agents.visualizer import Visualizer
from agents.anomaly_detector import AnomalyDetector
from agents.aggregator import Aggregator


class TestAgentPipeline:
    """Test agents working together."""

    @pytest.fixture
    def sample_data_file(self):
        """Create sample CSV file for pipeline."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=100),
            "sales": np.random.normal(1000, 200, 100),
            "units": np.random.poisson(50, 100),
            "region": np.random.choice(["North", "South", "East", "West"], 100),
        })
        
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        yield temp_path
        Path(temp_path).unlink()

    def test_full_pipeline(self, sample_data_file):
        """Test complete agent pipeline."""
        
        # STEP 1: DataLoader loads data
        loader = DataLoader()
        load_result = loader.load(sample_data_file)
        assert load_result['status'] == 'success'
        df = load_result['data']
        
        # STEP 2: Explorer analyzes
        explorer = Explorer()
        explorer.set_data(df)
        
        # Use Explorer's get_summary_report which aggregates all analyses
        summary = explorer.get_summary_report()
        assert summary['status'] == 'success'
        assert 'numeric_stats' in summary
        assert 'categorical_stats' in summary
        
        # STEP 3: Visualizer creates charts
        visualizer = Visualizer()
        visualizer.set_data(df)
        
        # Line chart
        line_result = visualizer.line_chart('date', 'sales', title='Sales Over Time')
        assert line_result['success']
        
        # Bar chart
        bar_result = visualizer.bar_chart('region', 'sales', title='Sales by Region')
        assert bar_result['success']
        
        # Histogram
        hist_result = visualizer.histogram('sales', bins=20, title='Sales Distribution')
        assert hist_result['success']
        
        # STEP 4: AnomalyDetector finds outliers
        detector = AnomalyDetector()
        detector.set_data(df)
        
        iqr_result = detector.detect_iqr('sales', multiplier=1.5)
        assert iqr_result['success']
        
        iso_result = detector.detect_isolation_forest(['sales', 'units'], contamination=0.1)
        assert iso_result['success']
        
        # STEP 5: Aggregator summarizes
        aggregator = Aggregator()
        aggregator.set_data(df)
        
        stats = aggregator.get_stats('sales')
        assert stats['status'] == 'success'
        
        group_stats = aggregator.group_by_and_aggregate('region', 'sales', 'mean')
        assert group_stats['status'] == 'success'
        
        # ALL AGENTS WORKING TOGETHER ✅
        assert visualizer.list_charts()['count'] >= 3
        assert detector.summary_report()['total_detections'] >= 2

    def test_error_recovery(self, sample_data_file):
        """Test agents handle errors gracefully."""
        
        # Load data
        loader = DataLoader()
        result = loader.load(sample_data_file)
        df = result['data']
        
        # Try to visualize non-existent column
        visualizer = Visualizer()
        visualizer.set_data(df)
        bad_result = visualizer.line_chart('nonexistent', 'sales')
        
        # Should handle error gracefully
        assert not bad_result['success']
        assert len(bad_result['errors']) > 0
        
        # But next valid chart should work
        good_result = visualizer.line_chart('date', 'sales')
        assert good_result['success']

    def test_data_flow(self, sample_data_file):
        """Test data flows correctly through agents."""
        
        # Load
        loader = DataLoader()
        load_result = loader.load(sample_data_file)
        df = load_result['data']
        
        # Analyze with Explorer
        explorer = Explorer()
        explorer.set_data(df)
        
        # Get full summary (this works with the worker-based architecture)
        summary = explorer.get_summary_report()
        assert summary['status'] == 'success'
        
        # Extract numeric columns from the result
        numeric_cols = summary['numeric_stats'].get('numeric_columns', [])
        assert len(numeric_cols) > 0
        
        # Visualize first numeric column
        visualizer = Visualizer()
        visualizer.set_data(df)
        
        col_name = numeric_cols[0]
        hist_result = visualizer.histogram(col_name)
        assert hist_result['success']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
